# modules/jobs/sheets_keyword_queue_job.py
import logging
import traceback

from configs import *

from configs import (
    google_sheets_key_path,
    google_spreadsheet_id as google_sheets_spreadsheet_id,
    google_spreadsheet_name as google_sheets_tab_name,
)

from modules.third_party_modules.google.sheets.sheets_queue import *
from routes.publish_to_wordpress import create_article_and_publish_internal

WORKER_ID = "apscheduler-daily"
CLAIM_LIMIT = int(max_keywords_per_day)                 # <- cast
LEASE_MINUTES = int(google_sheets_keyword_lease_minutes)  # <- cast


def run_queue_once():
    queue = SheetsQueue(
        spreadsheet_id=google_sheets_spreadsheet_id,
        sheet_name=google_sheets_tab_name,
        service_account_json_path=google_sheets_key_path,
    )

    # (optional) keep the “rows print” you said you want:
    rows = queue.batch_fetch()
    print(rows)  # <-- your raw Rows dump

    # show a compact summary too (handy in logs)
    stats = queue.queue_stats()
    print(
        f"Queue stats: total={stats['total']} | "
        f"pending={stats['pending']} (ready={stats['ready']}) | "
        f"in_progress={stats['in_progress']} (expired={stats['expired']}) | "
        f"done={stats['done']} | failed={stats['failed']}"
    )

    claimed: list[Row] = queue.claim_pending(
        limit=CLAIM_LIMIT,
        worker_id=WORKER_ID,
        lease_minutes=LEASE_MINUTES
    )

    if not claimed:
        # nice, explicit message when there’s nothing to run
        if stats["ready"] == 0:
            print("✅ No eligible jobs: all keywords are done (or none are ready).")
        else:
            # ready==0 covers “none ready”; this else only hits if logic changes later
            print("✅ No jobs claimed.")
        logging.info("No pending jobs.")
        return

    logging.info("Claimed %d jobs", len(claimed))
    print(f"Claimed {len(claimed)} jobs")

    for r in claimed:
        keyword    = str(r.data.get("keyword", "")).strip()
        project_id = str(r.data.get("project_id", "")).strip()
        engine     = str(r.data.get("engine", "")).strip()
        language   = str(r.data.get("language", "")).strip()
        website_url = str(r.data.get("website_url", "")).strip()

        # Optional: you can also pull site/category/tags:
        # category_id = str(r.data.get("category_id", "")).strip()
        # tags_json   = str(r.data.get("tags_json", "")).strip()
        # tags        = json.loads(tags_json) if tags_json else []

        try:
            res = create_article_and_publish_internal(
                keyword=keyword,
                project_id=project_id,
                engine=engine,
                language=language,
                site=website_url
            )
            ok = bool(res.get("success"))
            if ok:
                queue.complete([r], status="done")
                logging.info("Row %s DONE: %s", r.row_number, keyword)
            else:
                msg = res.get("message") or res.get("error") or "Unknown error"
                queue.complete([r], status="failed", error=str(msg)[:500])
                logging.warning("Row %s FAILED: %s (%s)", r.row_number, keyword, msg)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            logging.exception("Row %s FAILED: %s (%s)", r.row_number, keyword, err)
            queue.complete([r], status="failed", error=err[:500])


def keyword_scheduled_job():
    """
    Entry point called by APScheduler.
    You can call run_queue_once() multiple times here if you want to drain the queue:
    e.g., loop while it keeps claiming items or stop after N cycles/time budget.
    """
    run_queue_once()
