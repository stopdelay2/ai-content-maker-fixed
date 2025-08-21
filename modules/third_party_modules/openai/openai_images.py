# generate_and_publish_wp_featured_image.py
import os
import base64
import json
import mimetypes
from typing import Optional, Tuple
import requests
from openai import OpenAI

from configs import *

from modules.third_party_modules.wordpress.wordpress_general import *

# -----------------------
# CONFIG
# -----------------------
# You can hardcode or use env vars. Example uses env vars:
OPENAI_API_KEY = openai_key  # or "sk-..."
WP_USER        = wordpress_user         # WordPress username
WP_APP_PASS    = wordpress_password     # WordPress Application Password
SITE           = wordpress_site       # e.g. "https://example.com"

# Example content (edit as needed)
PROMPT = """A children's book drawing of an American veterinarian using a stethoscope
to listen to the heartbeat of a baby otter."""
POST_TITLE   = "Vet listening to baby otter"
ALT_TEXT     = "Illustration: veterinarian using a stethoscope to listen to a baby otter"
POST_CONTENT = "<p>Programmatically created post with a featured image.</p>"
IMAGE_SIZE   = "1024x1024"  # images API size

# -----------------------
# OPENAI (image generation)
# -----------------------
def generate_image_bytes(
    prompt: str,
    model: str = "dall-e-3",   # or "dall-e-3"
    size: str = "1024x1024",
    response_format: str = "b64_json",
) -> Tuple[bytes, str]:
    """
    Returns (image_bytes, suggested_filename_ext).
    If b64 is missing, falls back to downloading from returned URL.
    """
    client = OpenAI(api_key=OPENAI_API_KEY)
    res = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        response_format=response_format,  # <-- important; default is "url"
        # You can also set: quality="high" (gpt-image-1) or quality="hd" (dall-e-3)
    )

    data = res.data[0]
    if getattr(data, "b64_json", None):
        raw = base64.b64decode(data.b64_json)
        # OpenAI images come as PNG bytes
        return raw, ".png"

    # Fallback: fetch via URL if response_format wasn't honored
    if getattr(data, "url", None):
        r = requests.get(data.url, timeout=120)
        r.raise_for_status()
        # MIME sniff
        ctype = r.headers.get("Content-Type", "image/png").lower()
        ext = ".png"
        if "jpeg" in ctype or "jpg" in ctype:
            ext = ".jpg"
        elif "webp" in ctype:
            ext = ".webp"
        elif "png" in ctype:
            ext = ".png"
        return r.content, ext

    raise RuntimeError("OpenAI image response had neither b64_json nor url")


# -----------------------
# PIPELINE
# -----------------------
def main():
    assert OPENAI_API_KEY, "Set OPENAI_API_KEY"
    assert WP_USER and WP_APP_PASS and SITE, "Set WP_USER, WP_APP_PASS, WP_SITE"

    # 1) Generate image bytes
    img_bytes, ext = generate_image_bytes(PROMPT, model="dall-e-3", size=IMAGE_SIZE, response_format="b64_json")

    # 2) Upload to WordPress Media
    filename = "featured-otter" + ext
    mime = mimetypes.guess_type(filename)[0] or "image/png"
    #media = upload_media_bytes(SITE, WP_USER, WP_APP_PASS, img_bytes, filename, mime_type=mime)

    #media_id = int(media["id"])

    # 3) Set alt text + title on the media
    #update_media_meta(SITE, WP_USER, WP_APP_PASS, media_id, ALT_TEXT, POST_TITLE)

    # 4) Create a post with that image as featured image
    post = create_post_with_featured_image(
        SITE, WP_USER, WP_APP_PASS, POST_TITLE, POST_CONTENT, status="publish"
    )

    #print("Media uploaded:", media_id, "->", media.get("source_url"))
    print("Post created:", post.get("id"), "->", post.get("link"))

#if __name__ == "__main__":
    #main()
