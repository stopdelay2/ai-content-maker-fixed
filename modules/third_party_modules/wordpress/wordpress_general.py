import base64, json, requests
import mimetypes
from typing import Optional, Tuple

from configs import *
from typing import Optional, Union

from modules.third_party_modules.openai.openai_images import generate_image_bytes
from modules.utils.filename import make_wp_safe_filename


def wordpress_upload_post(
    wordpress_user,
    wordpress_password,
    wordpress_site
):

    WP_USER     = wordpress_user
    WP_APP_PASS = wordpress_password
    SITE        = wordpress_site

    auth = base64.b64encode(f"{WP_USER}:{WP_APP_PASS}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    html_body = """
    <!DOCTYPE html>
    <html lang='en'>
      <body>
    
        <h1>How to Calm an Angry Penguin – SEO Study</h1>
    
        <p>
          Penguins are adorable, but even the cutest seabirds have bad days. In this quick study
          we explore <strong>three evidence-based techniques</strong> you can apply whenever a penguin
          seems flustered—whether you’re a zookeeper, a documentary crew member, or just a curious visitor.
        </p>
    
        <h2>Why Penguins Get Flustered</h2>
        <p>Common stressors include:</p>
        <ul>
          <li>Sudden loud noises</li>
          <li>Unexpected changes in food supply</li>
          <li>Intrusion into personal nesting space</li>
        </ul>
    
        <h2>Step-by-Step Calming Method</h2>
        <ol>
          <li><strong>Approach slowly</strong> from the side to avoid looking like a predator.</li>
          <li>Offer a small fish, such as a herring, to build trust.</li>
          <li>If the penguin flaps its wings rapidly, <em>stop and give it space</em>.</li>
        </ol>
    
    
        <p>
          For the full dataset and methodology, read the complete
          <a href="https://example.com/full-study" target="_blank" rel="noopener">research paper</a>.
        </p>
    
      </body>
    </html>
    """




    payload = {
        "title":   "How to Calm an Angry Penguin – SEO study",
        "content": html_body,          # see next section
        "status":  "publish",          # or 'draft'
        "slug":    "angry-penguin",
        "tags":    [23, 45],           # optional
        "meta":    {"_yoast_wpseo_focuskw": "angry penguin"}  # Yoast example
    }

    r = requests.post(f"{SITE}/wp-json/wp/v2/posts", headers=headers,
                      data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    print("New post id:", r.json()["id"])

    return r.json()["id"]


def _wp_auth_header(user: str, app_pass: str) -> dict:
    token = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def wp_upload_media_bytes(
    site: str,
    user: str,
    app_pass: str,
    image_bytes: bytes,
    filename: str,
    mime_type: Optional[str] = None,
) -> dict:
    """Upload a binary image to WP Media Library. Returns media JSON dict."""
    if not mime_type:
        mime_type = mimetypes.guess_type(filename)[0] or "image/png"
    headers = {
        **_wp_auth_header(user, app_pass),
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": mime_type,
    }
    url = f"{site.rstrip('/')}/wp-json/wp/v2/media"
    r = requests.post(url, headers=headers, data=image_bytes, timeout=120)
    r.raise_for_status()
    return r.json()


def wp_update_media_meta(site: str, user: str, app_pass: str, media_id: int,
                      alt_text: str = "", title: str = "") -> dict:
    """Set alt text and title for a media item."""
    url = f"{site.rstrip('/')}/wp-json/wp/v2/media/{media_id}"
    headers = {
        **_wp_auth_header(user, app_pass),
        "Content-Type": "application/json",
    }
    payload = {}
    if alt_text:
        payload["alt_text"] = alt_text
    if title:
        payload["title"] = title
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()

# --- add these helpers in wordpress_general.py ---

def _trim_meta_description(s: str, max_len: int = 155) -> str:
    s = " ".join((s or "").split())
    if len(s) <= max_len:
        return s
    cut = s[:max_len]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut + "…"

def _build_post_payload(title: str,
                        content_html: str,
                        status: str = "publish",
                        featured_media_id: Optional[int] = None,
                        meta_description: Optional[str] = None,
                        seo_plugin: str = "yoast") -> dict:
    payload = {
        "title": title,
        "content": content_html,
        "status": status,
    }
    if featured_media_id:
        payload["featured_media"] = featured_media_id

    # Optional: meta description
    if meta_description:
        md = _trim_meta_description(meta_description)

        # Always set excerpt as a universal fallback
        payload["excerpt"] = md

        # Plugin-specific meta keys
        if seo_plugin == "yoast":
            payload.setdefault("meta", {})["_yoast_wpseo_metadesc"] = md
        elif seo_plugin == "rankmath":
            payload.setdefault("meta", {})["rank_math_description"] = md
        elif seo_plugin == "aioseo":
            payload.setdefault("meta", {})["_aioseo_description"] = md
        # else: no special plugin meta

    return payload


def create_post_with_featured_image(
    site: str,
    user: str,
    app_pass: str,
    keyword: str,
    title: str,
    content_html: str,
    status: str = "publish",
    meta_description: Optional[str] = None,
    seo_plugin: str = "yoast",  # "yoast" | "rankmath" | "aioseo" | "none"
) -> dict:

    image_prompt = openai_image_prompt_pattern.format(
        article_topic=keyword
    )

    # 1) Generate image bytes
    img_bytes, ext = generate_image_bytes(
        image_prompt,
        openai_image_model,
        '1792x1024',
        "b64_json"
    )

    # 2) Upload to WordPress Media
    filename = make_wp_safe_filename(keyword, ext)
    mime = mimetypes.guess_type(filename)[0] or "image/png"
    media = wp_upload_media_bytes(
        site,
        user,
        app_pass,
        img_bytes,
        filename,
        mime
    )
    featured_media_id = int(media["id"])

    # 3) Set alt text + title on the media
    wp_update_media_meta(
        site,
        user,
        app_pass,
        featured_media_id,
        title,
        keyword
    )

    """Create a post and set its featured image."""
    url = f"{site.rstrip('/')}/wp-json/wp/v2/posts"
    headers = {
        **_wp_auth_header(user, app_pass),
        "Content-Type": "application/json",
    }
    payload = _build_post_payload(
        title=title,
        content_html=content_html,
        status=status,
        featured_media_id=featured_media_id,
        meta_description=meta_description,
        seo_plugin=seo_plugin
    )
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    r.raise_for_status()
    return r.json()


