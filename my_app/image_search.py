import requests
import re
import urllib.parse
import html
import json
from django.core.files.base import ContentFile

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"


def search_web_images(query: str, limit: int = 12) -> list:
    """Search live web pages, Google/Bing image results, Wikimedia, and Unsplash for high-res images."""
    if not query or not query.strip():
        query = "technology"

    clean_query = query.strip()
    results = []
    seen_urls = set()

    blocked_domains = ("ytimg.com", "pinimg.com", "instagram.com", "fbcdn.net", "tiktok.com", "wp.com/v/t")

    # 1. Wikimedia Commons API (Fast, 100% free, direct CDN images, no hotlink block)
    try:
        commons_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={urllib.parse.quote(clean_query)}&gsrlimit=8&prop=imageinfo&iiprop=url|thumburl&iiurlwidth=800&format=json"
        commons_resp = requests.get(commons_url, headers={"User-Agent": "PostyApp/1.0 (contact@posty.local)"}, timeout=4)
        if commons_resp.status_code == 200:
            pages = commons_resp.json().get("query", {}).get("pages", {})
            for page in pages.values():
                info = page.get("imageinfo", [{}])[0]
                img_url = info.get("thumburl") or info.get("url")
                if img_url and img_url.startswith("http") and img_url not in seen_urls:
                    seen_urls.add(img_url)
                    raw_title = page.get("title", clean_query).replace("File:", "").replace(".jpg", "").replace(".png", "")
                    results.append({
                        "url": img_url,
                        "thumb": img_url,
                        "title": raw_title[:45],
                        "source": "Wikimedia Commons"
                    })
                    if len(results) >= limit:
                        break
    except Exception:
        pass

    # 2. Live Web Search (Bing/Web image index with hotlink protection filter)
    if len(results) < limit:
        try:
            url = f"https://www.bing.com/images/search?q={urllib.parse.quote(clean_query)}&form=HDRSC2&first=1"
            headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                matches = re.findall(r'm="(\{.*?\})"', resp.text)
                for m in matches:
                    try:
                        data = json.loads(html.unescape(m))
                        img_url = data.get("murl")
                        thumb_url = data.get("turl") or img_url
                        title = data.get("t") or clean_query

                        if img_url and img_url.startswith("http") and not any(b in img_url for b in blocked_domains) and img_url not in seen_urls:
                            seen_urls.add(img_url)
                            results.append({
                                "url": img_url,
                                "thumb": thumb_url,
                                "title": title[:50],
                                "source": "Web Images"
                            })
                            if len(results) >= limit:
                                break
                    except Exception:
                        continue
        except Exception:
            pass

    # 3. Dynamic Topic-Specific AI Artwork
    if len(results) < limit:
        ai_artwork = generate_ai_artwork(f"Cinematic photorealistic 8k image of {clean_query}")
        if ai_artwork["url"] not in seen_urls:
            seen_urls.add(ai_artwork["url"])
            results.append({
                "url": ai_artwork["url"],
                "thumb": ai_artwork["thumb"],
                "title": f"AI Art: {clean_query.title()}",
                "source": "Posty Generative Art"
            })

    return results




def download_image_to_field(post_instance, image_url: str):
    """Download live web image and attach to post image field."""
    if not image_url or not image_url.startswith("http"):
        return
    
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(image_url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.content:
            # Determine extension
            content_type = resp.headers.get("content-type", "")
            ext = "jpg"
            if "png" in content_type:
                ext = "png"
            elif "webp" in content_type:
                ext = "webp"
            elif "gif" in content_type:
                ext = "gif"
                
            filename = f"post_{post_instance.id or 'new'}_{int(len(resp.content))}.{ext}"
            post_instance.image.save(filename, ContentFile(resp.content), save=False)
    except Exception:
        pass


def generate_ai_artwork(prompt: str, width: int = 1200, height: int = 630) -> dict:
    """Generate high quality AI artwork from a descriptive text prompt."""
    safe_prompt = urllib.parse.quote(prompt.strip())
    # Pollinations AI generation URL (no API key needed, high quality output)
    image_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={width}&height={height}&nologo=true&enhance=true"
    return {
        "url": image_url,
        "thumb": image_url,
        "prompt": prompt,
        "source": "Posty AI Generative Art"
    }

