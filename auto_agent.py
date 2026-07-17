import os
import time
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv

from src.scraper.multi_source_fetcher import get_latest_entertainment_news
from src.scraper.image_search import get_related_image
from src.analyzer.llm_analyzer import generate_content_from_article, generate_facebook_caption
from src.image_editor.image_processor import create_facebook_post
from src.facebook.facebook_publisher import upload_to_facebook
from src.discord.discord_reporter import send_discord_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_processed_trends():
    if not os.path.exists("output/processed_news.txt"):
        return set()
    with open("output/processed_news.txt", "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_processed_trend(trend_title):
    os.makedirs("output", exist_ok=True)
    with open("output/processed_news.txt", "a", encoding="utf-8") as f:
        f.write(f"{trend_title}\n")

def job():
    logging.info("Starting automated job (Scanning sources for news under 24 hours old)...")
    news_items = get_latest_entertainment_news(max_age_hours=24)
    if not news_items:
        logging.info("No fresh articles found within the last 2 hours.")
        return

    processed = load_processed_trends()
    
    for item in news_items:
        title = item["title"]
        if title in processed:
            continue
            
        logging.info(f"Processing new article: {title}")
        
        image_url = item["image_url"]
        description = item.get("description", "")
        source_url = item.get("link", "")
        source_name = "INTERNET"
        if "variety.com" in source_url: source_name = "VARIETY"
        elif "hollywoodreporter.com" in source_url: source_name = "THR"
        elif "deadline.com" in source_url: source_name = "DEADLINE"
        elif "eonline.com" in source_url: source_name = "E! NEWS"
        elif "comicbook.com" in source_url: source_name = "COMICBOOK"
        elif "ign.com" in source_url: source_name = "IGN"
        
        # 1. Fetch Second Image
        image_url_2 = get_related_image(title, avoid_url=image_url)
        
        os.makedirs("output", exist_ok=True)
        generation_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y%m%d_%H%M%S')
        post_id = f"{generation_time}_{int(time.time())}"
        
        # 2. Image Content & Style
        ai_data = generate_content_from_article(title, description)
        headline = ai_data.get("headline", title)
        hook_text = ai_data.get("hook_text", description)
        style = ai_data.get("style", "Breaking News Style")
        
        logging.info(f"Headline: {headline}")
        
        poster_path = f"output/post_{post_id}.jpg"
        
        # 3. Image Creation
        processed_img_path = create_facebook_post(
            image_url=image_url, 
            image_url_2=image_url_2,
            headline=headline,
            source_name=source_name,
            output_path=poster_path,
            logo_path="assets/logo/logo.png"
        )
        
        if not processed_img_path:
            logging.error(f"Failed to create image for {title}.")
            continue
            
        # 3. Facebook Caption
        try:
            facebook_caption = generate_facebook_caption(title)
        except Exception as e:
            logging.warning("LLM caption generation failed. Using fallback template.")
            facebook_caption = f"🚨 Hollywood Update! 🚨\n\n{title}\n\nStay tuned for more updates! 👇\n#HollywoodNews #CelebrityBuzz #Trending #Entertainment #News"

        # 4. Upload to Facebook
        upload_success, fb_post_id = upload_to_facebook(processed_img_path, facebook_caption)
        
        # 5. Discord Report
        page_id = os.getenv("FACEBOOK_PAGE_ID", "1094922960379153")
        status_text = "Success" if upload_success else "Failed"
        post_url = f"https://www.facebook.com/{page_id}/posts/{fb_post_id}" if upload_success else "N/A"
        
        report = f"""✅ Pipeline Run Completed

🎬 Photo Name:
{headline} 🚀

📤 Facebook Upload Status: {status_text}

🏷️ SEO Title:
{headline}

📝 Description:
{facebook_caption}

Original File: {os.path.basename(processed_img_path)}

🔗 Facebook Photo Post URL:
{post_url}

📦 GitHub Repository:
https://github.com/Vikram-Bosak/facebook-viral-news-agent

📄 Source Article:
{source_url}
"""
        send_discord_report(processed_img_path, report)

        if upload_success:
            save_processed_trend(title)
            logging.info(f"Successfully processed and uploaded {title}.")
            break # Process only one successfully per run to avoid spamming
        else:
            logging.error(f"Failed to upload {title} to Facebook. Will try another article if available.")

if __name__ == "__main__":
    load_dotenv()
    
    # Fail-Fast Validation
    required_env_vars = ["FACEBOOK_ACCESS_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"CRITICAL ERROR: Missing essential environment variables: {', '.join(missing_vars)}. Exiting immediately.")
        exit(1)
        
    job()
