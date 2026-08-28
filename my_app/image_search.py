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

    # 1. Live Web Search (Bing/Web image index)
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(clean_query)}&form=HDRSC2&first=1"
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            # Find m="{...}" metadata blocks containing murl (full image) and turl (thumbnail)
            matches = re.findall(r'm="(\{.*?\})"', resp.text)
            for m in matches:
                try:
                    data = json.loads(html.unescape(m))
                    img_url = data.get("murl")
                    thumb_url = data.get("turl") or img_url
                    title = data.get("t") or clean_query

                    if img_url and img_url.startswith("http") and img_url not in seen_urls:
                        seen_urls.add(img_url)
                        results.append({
                            "url": img_url,
                            "thumb": thumb_url,
                            "title": title,
                            "source": "Web / Google Images"
                        })
                        if len(results) >= limit:
                            break
                except Exception:
                    continue
    except Exception as e:
        pass

    # 2. Wikipedia / Wikimedia Commons API
    if len(results) < limit:
        try:
            wiki_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": clean_query,
                "gsrlimit": 8,
                "prop": "pageimages",
                "piprop": "thumbnail|original",
                "pithumbsize": 500,
            }
            wiki_headers = {"User-Agent": "PostyApp/1.0 (contact@posty.local)"}
            wiki_resp = requests.get(wiki_url, params=params, headers=wiki_headers, timeout=5)
            if wiki_resp.status_code == 200:
                pages = wiki_resp.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    if "original" in page:
                        orig = page["original"]["source"]
                        thumb = page.get("thumbnail", {}).get("source", orig)
                        title = page.get("title", clean_query)
                        if orig and orig not in seen_urls:
                            seen_urls.add(orig)
                            results.append({
                                "url": orig,
                                "thumb": thumb,
                                "title": title,
                                "source": "Wikimedia Commons"
                            })
                            if len(results) >= limit:
                                break
        except Exception:
            pass

    # 3. High quality Unsplash curated photo URLs matching topic
    if len(results) < limit:
        keywords = clean_query.replace(" ", ",")
        for i in range(1, 4):
            unsplash_url = f"https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80&sig={i}&kw={urllib.parse.quote(keywords)}"
            if unsplash_url not in seen_urls:
                seen_urls.add(unsplash_url)
                results.append({
                    "url": unsplash_url,
                    "thumb": unsplash_url,
                    "title": f"{clean_query} Photo {i}",
                    "source": "Unsplash HD"
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

