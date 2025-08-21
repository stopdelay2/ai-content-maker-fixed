import base64
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
import mimetypes

from configs import openai_image_model

from modules.third_party_modules.wordpress.wordpress_general import *
from modules.third_party_modules.openai.openai_images import *
from modules.utils.filename import make_wp_safe_filename


def _decode_prompt(fig) -> str:
    b64 = fig.get("data-ai-prompt-b64")
    if b64:
        try:
            return base64.b64decode(b64).decode("utf-8")
        except Exception:
            pass
    # fallback: plaintext
    return fig.get("data-ai-prompt", "")


def _find_ai_figures(soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
    """
    Returns list of (id, prompt, alt) for each figure.ai-image.
    """
    out = []
    for fig in soup.select("figure.ai-image"):
        img = fig.find("img")
        if not img: continue
        fid = fig.get("id") or img.get("id") or ""
        prompt = _decode_prompt(fig)
        alt = img.get("alt", "").strip()
        if fid and prompt and alt:
            out.append((fid, prompt, alt))
    return out


def process_article_html(
        site,
        user,
        app_pass,
        html
) -> str:
    """
    1) Find figure.ai-image blocks
    2) Generate images via OpenAI
    3) Upload to WP
    4) Replace src tokens, set media alt/title
    5) Optionally drop data-* attributes
    """
    soup = BeautifulSoup(html, "html.parser")
    figures = _find_ai_figures(soup)
    for fid, prompt, alt in figures:
        # 1. Generate
        image_bytes, ext = generate_image_bytes(
            prompt,
            openai_image_model,
            "1792x1024",
            "b64_json"
        )
        filename = make_wp_safe_filename(alt, ext)
        mime = mimetypes.guess_type(filename)[0] or "image/png"
        # 2. Upload
        media = wp_upload_media_bytes(
            site,
            user,
            app_pass,
            image_bytes,
            filename,
            mime_type=mime
        )

        media_url = media.get("source_url")
        media_id = int(media["id"])
        image_title = alt[:60]
        # 3. Update alt/title in the media library
        wp_update_media_meta(
            site,
            user,
            app_pass,
            media_id,
            alt,
            image_title
        )
        # 4. Replace token in the corresponding <img>
        token = f"__AIIMG:{fid}__"
        img = soup.find("img", src=token)
        if img:
            img["src"] = media_url
            img["style"] = "display:block;width:100%;height:auto;"
        # 5. (Optional) clean up data-* so final HTML is “clean”
        fig = soup.find(id=fid)
        if fig:
            # Rebuild attributes without the data-ai-* ones (type-checker friendly)
            fig.attrs = {
                k: v
                for k, v in fig.attrs.items()
                if not (isinstance(k, str) and k.startswith("data-ai-"))
            }
    return str(soup)
