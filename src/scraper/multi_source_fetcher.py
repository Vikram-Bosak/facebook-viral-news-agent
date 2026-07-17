import feedparser
import logging
from datetime import datetime, timezone
import time

FEEDS = [
    "https://news.google.com/rss/search?q=Hollywood+entertainment+news+trending&hl=en-US&gl=US&ceid=US:en",
    "https://variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://deadline.com/feed/",
    "https://www.eonline.com/syndication/feeds/rssfeeds/topstories.xml"
]

def get_latest_entertainment_news(max_age_hours=2):
    """
    Fetches the latest news from multiple Hollywood sources.
    Filters out news older than max_age_hours.
    Sorts by newest first.
    Returns a list of dictionaries with 'title', 'link', 'description', and 'image_url'.
    """
    news_items = []
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for rss_url in FEEDS:
        logging.info(f"Scanning feed: {rss_url}")
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                # Get publication time
                pub_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_time = time.mktime(entry.published_parsed)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_time = time.mktime(entry.updated_parsed)
                
                if not pub_time:
                    continue
                
                age_seconds = current_time - pub_time
                
                # Check if it's within our time window (2 hours)
                if age_seconds < 0 or age_seconds > max_age_seconds:
                    continue
                    
                title = entry.title
                link = entry.link
                description = getattr(entry, 'description', '')
                image_url = None
                
                # 1. Try media_content
                if hasattr(entry, 'media_content'):
                    max_width = 0
                    for media in entry.media_content:
                        if media.get('medium') == 'image':
                            width = int(media.get('width', 0))
                            if width > max_width:
                                max_width = width
                                image_url = media.get('url')
                    # Fallback to the first media_content if width wasn't specified
                    if not image_url and len(entry.media_content) > 0:
                        image_url = entry.media_content[0].get('url')
                        
                # 2. Try media_thumbnail
                if not image_url and hasattr(entry, 'media_thumbnail'):
                    if len(entry.media_thumbnail) > 0:
                        image_url = entry.media_thumbnail[0].get('url')
                        
                # 3. Try enclosures
                if not image_url and hasattr(entry, 'enclosures'):
                    for enc in entry.enclosures:
                        if enc.get('type', '').startswith('image/'):
                            image_url = enc.get('href')
                            break
                            
                # Only add if we found a valid image
                if image_url:
                    news_items.append({
                        "title": title,
                        "link": link,
                        "description": description,
                        "image_url": image_url,
                        "timestamp": pub_time,
                        "source": rss_url
                    })
                    
        except Exception as e:
            logging.error(f"Error fetching {rss_url}: {e}")

    # Sort items by timestamp, newest first
    news_items.sort(key=lambda x: x['timestamp'], reverse=True)
    
    logging.info(f"Found {len(news_items)} fresh articles (under {max_age_hours} hours old) with images.")
    return news_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = get_latest_entertainment_news()
    logging.info(f"Test complete. Found {len(news)} items.")
