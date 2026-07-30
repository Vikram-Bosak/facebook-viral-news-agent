from duckduckgo_search import DDGS
import logging
import re
import requests
import urllib.parse

def get_bing_image(query, avoid_url=None):
    """
    Fallback method to search Bing Images for a related image.
    Does not suffer from DuckDuckGo's strict rate limits.
    """
    logging.info(f"Searching Bing Images for: '{query}'")
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=10)
        # Match both HTML-escaped and standard JSON formats of Bing Images
        urls = re.findall(r'murl&quot;:&quot;([^&]+)&quot;', r.text)
        if not urls:
            urls = re.findall(r'"murl"\s*:\s*"([^"]+)"', r.text)
            
        for u in urls:
            # Clean backslashes and HTML entities if any
            u_clean = urllib.parse.unquote(u.replace("\\", ""))
            if u_clean.startswith("http") and u_clean != avoid_url:
                # Filter out generic diagrams, charts, vectors, icons
                u_lower = u_clean.lower()
                if any(x in u_lower for x in ["chart", "diagram", "psychrometric", "blueprint", "graph", "vector", "icon", "placeholder"]):
                    continue
                # Skip known bad facebook lookaside or tracking URLs that yield binary/corrupted responses
                if "lookaside.fbsbx.com" in u_lower:
                    continue
                logging.info(f"Found related image on Bing: {u_clean}")
                return u_clean
    except Exception as e:
        logging.warning(f"Bing image search failed: {e}")
    return None

def get_related_image(keyword, avoid_url=None):
    """
    Generates a related image using Pollinations AI (Flux model).
    """
    import urllib.parse
    clean_keyword = re.sub(r"[‘’“”\"']", "", keyword)
    # Build a clean prompt for image generation
    prompt = f"realistic professional photo of {clean_keyword}, high quality celebrity portrait, cinematic lighting, 8k resolution"
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true&private=true"
    logging.info(f"Generated AI image URL using Pollinations.ai: {image_url}")
    return image_url
