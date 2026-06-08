import os
import time
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

from src.scraper.cnn_fetcher import get_cnn_entertainment_news
from src.analyzer.llm_analyzer import generate_content_from_article
from src.image_editor.image_processor import create_facebook_post
from src.telegram.telegram_reporter import send_telegram_photo

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_processed_trends():
    if not os.path.exists("output/processed_news.txt"):
        return set()
    with open("output/processed_news.txt", "r") as f:
        return set(line.strip() for line in f)

def save_processed_trend(trend_title):
    os.makedirs("output", exist_ok=True)
    with open("output/processed_news.txt", "a") as f:
        f.write(f"{trend_title}\n")

def job():
    logging.info("Starting automated job (1 Image per run)...")
    news_items = get_cnn_entertainment_news()
    if not news_items:
        logging.info("No new articles found.")
        return

    processed = load_processed_trends()
    
    for item in news_items:
        title = item["title"]
        if title in processed:
            continue
            
        logging.info(f"Processing new article: {title}")
        
        image_url = item["image_url"]
        content = generate_content_from_article(title, item.get("description", ""))
        
        os.makedirs("Generated-Images", exist_ok=True)
        output_filename = f"Generated-Images/post_{int(time.time())}.jpg"
        branding = os.getenv("BRANDING_TEXT", "Celebrity Buzz USA")
        
        processed_img_path = create_facebook_post(
            image_url, 
            headline=content["headline"],
            hook_text=content["hook_text"],
            branding=branding, 
            output_path=output_filename,
            logo_path="assets/logo/logo.png"
        )
        
        save_processed_trend(title)
        logging.info(f"Finished processing {title}.")
        
        generation_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %I:%M %p EST')
        report = (
            f"✅ <b>New Facebook Poster Generated</b>\n\n"
            f"📰 <b>News Title:</b> {title}\n"
            f"🕒 <b>Time:</b> {generation_time}\n"
            f"📁 <b>Location:</b> Saved to GitHub `Generated-Images` folder"
        )
        
        if processed_img_path:
            send_telegram_photo(processed_img_path, report)
        break

if __name__ == "__main__":
    load_dotenv()
    job()
