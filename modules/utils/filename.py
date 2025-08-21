# utils/filename.py
import re, unicodedata


def make_wp_safe_filename(name: str, ext: str) -> str:
    """
    ASCII-only filename for HTTP headers.
    Keeps letters, digits, ., _, - . Falls back to 'file' if empty.
    """
    base = unicodedata.normalize("NFKD", name)
    base = base.encode("ascii", "ignore").decode("ascii")  # drop non-ASCII
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-_.")
    if not base:
        base = "file"
    if ext and not ext.startswith("."):
        ext = "." + ext
    return f"{base}{ext}"
