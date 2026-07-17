from duckduckgo_search import DDGS
import logging

def get_related_image(keyword, avoid_url=None):
    """
    Searches DuckDuckGo for an image related to the keyword.
    Tries to return an image URL that is different from avoid_url.
    """
    logging.info(f"Searching for related image: {keyword}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                keyword,
                region="wt-wt",
                safesearch="moderate",
                size="Large",
                max_results=5
            ))
            
            for res in results:
                img_url = res.get('image')
                if img_url and img_url != avoid_url:
                    logging.info(f"Found related image: {img_url}")
                    return img_url
                    
    except Exception as e:
        logging.error(f"Image search failed for '{keyword}': {e}")
        
    return None
