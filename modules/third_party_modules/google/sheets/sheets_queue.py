from __future__ import annotations
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from configs import *

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
REQUIRED_FIELDS_FOR_CLAIM = ["keyword", "project_id", "engine", "language"]

SHEETS_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)

EXPECTED_HEADERS = [
    "id", "website_url", "keyword", "project_id", "engine", "language", "category_id", "tags_json",
    "status", "created_time", "processing_by", "lease_until", "processed_time", "error",
]

HEADER_RANGE = "B3:O3"
DATA_RANGE = "B4:O"  # row 2 onward


def _row_ready(r: Row) -> bool:
    return all(str(r.data.get(k, "")).strip() for k in REQUIRED_FIELDS_FOR_CLAIM)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime(ISO_FMT)


def parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, ISO_FMT).replace(tzinfo=timezone.utc)
    except Exception:
        return None

def parse_sheet_dt(v) -> Optional[datetime]:
    """
    Accepts either an ISO string 'YYYY-MM-DDTHH:MM:SSZ' or a Sheets serial number.
    Returns an aware UTC datetime, or None.
    """
    if v is None or v == "":
        return None
    # numeric serial?
    if isinstance(v, (int, float)):
        try:
            return SHEETS_EPOCH + timedelta(days=float(v))
        except Exception:
            return None
    # ISO string?
    if isinstance(v, str):
        try:
            return datetime.strptime(v, ISO_FMT).replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None




@dataclass
class Row:
    row_number: int  # 2-based index in the sheet
    data: Dict[str, Any]


class SheetsQueue:
    def __init__(self, spreadsheet_id: str, sheet_name: str, service_account_json_path: str):
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = service_account.Credentials.from_service_account_file(service_account_json_path, scopes=scopes)
        self.svc = build("sheets", "v4", credentials=creds).spreadsheets()

        self._assert_headers()

    # ---------- Setup / guards ----------

    def _assert_headers(self) -> None:
        resp = self.svc.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!{HEADER_RANGE}"
        ).execute()
        values = resp.get("values", [[]])
        headers = values[0] if values else []
        if headers != EXPECTED_HEADERS:
            raise RuntimeError(
                f"Header mismatch.\nFound: {headers}\nExpected: {EXPECTED_HEADERS}\n"
                f"Fix headers in row 3 of '{self.sheet_name}'."
            )

    # ---------- Core helpers ----------

    def _read_all(self) -> List[Row]:
        """Read entire table as list[Row], keeping row_number."""
        resp = self.svc.values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!{DATA_RANGE}",
            valueRenderOption="UNFORMATTED_VALUE"
        ).execute()
        rows = resp.get("values", [])

        results: List[Row] = []
        for idx, raw in enumerate(rows, start=4):  # row 4 is the first data row
            # Pad to 14 columns
            raw = (raw + [""] * 14)[:14]
            data = {EXPECTED_HEADERS[i]: raw[i] for i in range(14)}
            results.append(Row(row_number=idx, data=data))
        return results

    # --- add this new helper ---
    def queue_stats(self) -> dict:
        """
        Returns counts for total, pending, ready (pending+required fields present),
        in_progress, expired leases, done, failed.
        """
        rows = self._read_all()
        now = datetime.now(timezone.utc)

        total = len(rows)
        pending = 0
        ready = 0
        in_progress = 0
        expired = 0
        done = 0
        failed = 0

        for r in rows:
            status = str(r.data.get("status", "")).strip().lower()
            if status == "pending":
                pending += 1
                if _row_ready(r):
                    ready += 1
            elif status == "in_progress":
                in_progress += 1
                lu = parse_sheet_dt(r.data.get("lease_until", ""))
                if lu and lu < now:
                    expired += 1
            elif status == "done":
                done += 1
            elif status == "failed":
                failed += 1

        return {
            "total": total,
            "pending": pending,
            "ready": ready,
            "in_progress": in_progress,
            "expired": expired,
            "done": done,
            "failed": failed,
        }


    def _write_rows_full(self, rows: List[Row]) -> None:
        """Batch write full rows (A..N) for given row_numbers."""
        data_payload = []
        for r in rows:
            ordered = [r.data.get(h, "") for h in EXPECTED_HEADERS]
            b4 = f"{self.sheet_name}!B{r.row_number}:O{r.row_number}"
            data_payload.append({"range": b4, "values": [ordered]})

        if not data_payload:
            return

        self.svc.values().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body={"valueInputOption": "RAW", "data": data_payload}
        ).execute()

    # ---------- Public API ----------

    def batch_fetch(self) -> List[Row]:
        """Return all rows (including pending/in_progress/done/failed)."""
        #print(self._read_all())
        return self._read_all()

    def claim_pending(
        self,
        limit: int,
        worker_id: str,
        lease_minutes: int = 10
    ) -> List[Row]:
        """
        Atomically-ish "claim" up to N jobs:
        - Eligible if status == 'pending' OR (status == 'in_progress' AND lease_until expired)
        - Sort by created_time (oldest first; blanks treated as newest)
        - For each claimed row: set id (if blank), created_time (if blank), status='in_progress',
          processing_by=worker_id, lease_until=now+lease_minutes
        Returns claimed rows (with updated fields).
        """
        all_rows = self._read_all()

        # Compute eligibility
        now = datetime.now(timezone.utc)
        eligible: List[Row] = []
        for r in all_rows:
            status = str(r.data.get("status", "")).strip().lower()
            lease_until = parse_sheet_dt(r.data.get("lease_until", ""))
            if status == "pending" and _row_ready(r):
                eligible.append(r)
            elif status == "in_progress" and lease_until and lease_until < now:
                eligible.append(r)

        # Sort by created_time (oldest first). Blanks treated as "far future" so they end up last.
        def sort_key(row: Row):
            ct_raw = row.data.get("created_time", "")
            ct = parse_sheet_dt(ct_raw)
            return ct if ct else datetime.max.replace(tzinfo=timezone.utc)

        eligible.sort(key=sort_key)

        to_claim = eligible[:limit]

        # Update in-memory models, then batch write
        lease_str = (now + timedelta(minutes=lease_minutes)).replace(microsecond=0).strftime(ISO_FMT)

        updated_rows: List[Row] = []
        for r in to_claim:
            if not str(r.data.get("id", "")).strip():
                r.data["id"] = uuid.uuid4().hex  # stable unique id

            if not str(r.data.get("created_time", "")).strip():
                r.data["created_time"] = utc_now_iso()

            r.data["status"] = "in_progress"
            r.data["processing_by"] = worker_id
            r.data["lease_until"] = lease_str
            # Clear any stale error when re-claiming
            if str(r.data.get("error", "")).strip() and r.data["status"] == "in_progress":
                r.data["error"] = ""

            updated_rows.append(r)

        self._write_rows_full(updated_rows)
        return updated_rows

    def complete(
        self,
        rows: List[Row],
        status: str,
        error: str = ""
    ) -> None:
        """
        Mark rows as done/failed. Clears processing_by/lease_until, sets processed_time and error.
        `rows` must contain valid row_number and (ideally) the latest data dict.
        """
        assert status in ("done", "failed"), "status must be 'done' or 'failed'"
        now_str = utc_now_iso()

        # Re-read a map from row_number -> current row to be safe (avoid overwriting unrelated cells)
        latest = {r.row_number: r for r in self._read_all()}

        updates: List[Row] = []
        for r in rows:
            cur = latest.get(r.row_number, r)
            cur.data["status"] = status
            cur.data["processed_time"] = now_str
            cur.data["processing_by"] = ""
            cur.data["lease_until"] = ""
            cur.data["error"] = error if status == "failed" else ""
            updates.append(cur)

        self._write_rows_full(updates)

    def renew_lease(self, rows: List[Row], extend_minutes: int) -> None:
        """
        Extend leases for long-running jobs.
        """
        latest = {r.row_number: r for r in self._read_all()}
        new_until = (datetime.now(timezone.utc) + timedelta(minutes=extend_minutes)).replace(microsecond=0).strftime(ISO_FMT)
        updates: List[Row] = []
        for r in rows:
            cur = latest.get(r.row_number, r)
            cur.data["lease_until"] = new_until
            updates.append(cur)
        self._write_rows_full(updates)

    def append_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Optional helper to add new jobs. Each dict can include any of:
        id, website_url, keyword, project_id, engine, language, category_id, tags_json, status, created_time
        Missing fields are defaulted (id + created_time auto; status=pending).
        """
        prepared = []
        for j in jobs:
            row = {h: "" for h in EXPECTED_HEADERS}
            row.update(j)
            if not str(row.get("id", "")).strip():
                row["id"] = uuid.uuid4().hex
            if not str(row.get("created_time", "")).strip():
                row["created_time"] = utc_now_iso()
            if not str(row.get("status", "")).strip():
                row["status"] = "pending"
            # leave processing_by/lease_until/processed_time/error blank
            prepared.append([row[h] for h in EXPECTED_HEADERS])

        if not prepared:
            return

        self.svc.values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.sheet_name}!B:O",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": prepared}
        ).execute()


def test():
    spreadsheet_id = '175o3QIv_fL9I4e-_Nm35hriF7a5TP8qd1nF0p1dh-Ow'
    spreadsheet_name = 'Sheet1'

    sq = SheetsQueue(
        spreadsheet_id,
        spreadsheet_name,
        google_sheets_key_path
    )

    rows = sq.batch_fetch()
    print(rows)


#test()
