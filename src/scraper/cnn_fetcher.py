import feedparser
import logging

def get_cnn_entertainment_news():
    """
    Fetches the latest Entertainment news from CNN's RSS feed.
    Returns a list of dictionaries with 'title', 'link', and 'image_url'.
    """
    news_items = []
    try:
        rss_url = "http://rss.cnn.com/rss/edition_entertainment.rss"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            description = getattr(entry, 'description', '')
            image_url = None
            
            # Find the best image in media_content
            if hasattr(entry, 'media_content'):
                best_image = None
                max_width = 0
                for media in entry.media_content:
                    if media.get('medium') == 'image':
                        width = int(media.get('width', 0))
                        if width > max_width:
                            max_width = width
                            best_image = media.get('url')
                
                if best_image:
                    image_url = best_image
            
            # Fallback for old RSS structure if any
            if not image_url and hasattr(entry, 'media_thumbnail'):
                if len(entry.media_thumbnail) > 0:
                    image_url = entry.media_thumbnail[0].get('url')
                    
            # Only append if an image was found, since the image is crucial
            if image_url:
                news_items.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "image_url": image_url
                })
                
        logging.info(f"Fetched {len(news_items)} news items with images from CNN Entertainment RSS.")
    except Exception as e:
        logging.error(f"Error fetching CNN RSS: {e}")
        
    return news_items

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    news = get_cnn_entertainment_news()
    for n in news[:5]:
        print(f"{n['title']}\nImage: {n['image_url']}\n")
