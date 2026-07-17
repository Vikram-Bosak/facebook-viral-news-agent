from src.scraper.multi_source_fetcher import get_latest_entertainment_news
from src.scraper.image_search import get_related_image
from src.analyzer.llm_analyzer import generate_content_from_article, generate_facebook_caption
from src.image_editor.image_processor import create_facebook_post
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def force_run():
    # Force 24 hours to guarantee we find a trending news item today
    news_items = get_latest_entertainment_news(max_age_hours=24)
    title = "Bollywood Queen Jacqueline Fernandez Just Dropped Her AI Avatar And its Basically a Digital Twin That Spills Her Secret"
    description = ""
    image_url = news_items[0]["image_url"] if news_items else "https://via.placeholder.com/800"
    source_url = ""
    source_name = "VARIETY" # Mock source for test
    
    logging.info(f"Processing: {title}")
    
    image_url_2 = get_related_image(title, avoid_url=image_url)
    
    ai_data = generate_content_from_article(title, description)
    headline = ai_data.get("headline", title)
    
    # We will output this to the test file
    poster_path = "test_today_news.jpg"
    
    processed_img_path = create_facebook_post(
        image_url=image_url, 
        image_url_2=image_url_2,
        headline=headline,
        source_name=source_name,
        output_path=poster_path,
        logo_path="assets/logo/logo.png"
    )
    
    print("FINISHED. Image saved at:", processed_img_path)

if __name__ == "__main__":
    force_run()
