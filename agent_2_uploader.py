import os
import time
import requests
import logging
import random
import datetime
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def random_sleep(max_minutes=1):
    sleep_time = random.randint(1, max_minutes * 60)
    logging.info(f"Random Jitter: Sleeping for {sleep_time} seconds to prevent API rate limits...")
    time.sleep(sleep_time)
    logging.info("Woke up from jitter. Proceeding with upload.")

def get_openai_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

def load_processed_messages():
    if not os.path.exists("output/processed_telegram_messages.txt"):
        return set()
    with open("output/processed_telegram_messages.txt", "r") as f:
        return set(line.strip() for line in f)

def save_processed_message(message_id):
    os.makedirs("output", exist_ok=True)
    with open("output/processed_telegram_messages.txt", "a") as f:
        f.write(f"{message_id}\n")

def download_telegram_photo(file_id, bot_token, output_path):
    # Get file path
    url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
    response = requests.get(url)
    response.raise_for_status()
    file_path = response.json()['result']['file_path']
    
    # Download file
    download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    img_data = requests.get(download_url).content
    with open(output_path, 'wb') as handler:
        handler.write(img_data)
    logging.info(f"Downloaded image to {output_path}")

def fallback_generate_caption(title):
    return (
        f"🚨 Hollywood Update! 🚨\n\n"
        f"{title}\n\n"
        f"Stay tuned for more updates! 👇\n"
        f"#HollywoodNews #CelebrityBuzz #Trending #Entertainment #News #CelebrityBuzzUSA"
    )

def llm_generate_caption(title):
    client = get_openai_client()
    if not client:
        raise Exception("OpenAI client not initialized (Missing API Key).")
        
    logging.info(f"Generating LLM caption for: {title}")
    prompt = f"""
Write a highly engaging Facebook post caption for an American entertainment news page called 'Celebrity Buzz USA'.
The post is about this news title: {title}

Requirements:
- Keep it catchy, exciting, and short (3-4 sentences max).
- Include 2-3 relevant emojis.
- Include an engaging hook or question at the end to drive comments.
- Include 5-6 relevant hashtags at the very bottom (like #HollywoodNews, #Trending).
- Do not include markdown formatting, just the raw text ready for Facebook.
"""
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            top_p=0.95,
            max_tokens=1024,
            stream=False
        )
        caption = completion.choices[0].message.content.strip()
        if not caption:
            raise Exception("Empty response from LLM")
        return caption
    except Exception as e:
        logging.error(f"LLM caption generation failed: {e}")
        raise

def upload_to_facebook(image_path, text_content):
    """
    Uploads the image and text to Facebook using the Graph API.
    """
    access_token = os.getenv("FACEBOOK_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID", "me") # Default to 'me' if not provided
    
    if not access_token:
        logging.error("FACEBOOK_ACCESS_TOKEN is missing. Cannot upload to Facebook.")
        return False
        
    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    try:
        with open(image_path, 'rb') as image_file:
            files = {
                'source': image_file
            }
            data = {
                'message': text_content,
                'access_token': access_token,
                'published': 'true'
            }
            
            logging.info(f"Uploading {image_path} to Facebook...")
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get('post_id', result.get('id'))
            logging.info(f"Successfully uploaded to Facebook! Post ID: {post_id}")
            return True, post_id
            
    except Exception as e:
        logging.error(f"Failed to upload to Facebook: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            logging.error(f"Facebook API Response: {response.text}")
        return False, None

def send_detailed_report(bot_token, chat_id, message_id, title, facebook_text, post_id, source_url, image_url, image_path):
    page_id = os.getenv("FACEBOOK_PAGE_ID", "me")
    repo = os.getenv("GITHUB_REPOSITORY", "Vikram-Bosak/facebook-viral-news-agent")
    run_id = os.getenv("GITHUB_RUN_ID", "unknown")
    
    # Attempt to construct a public URL
    url_post_id = post_id.split('_')[-1] if '_' in post_id else post_id
    public_url = f"https://www.facebook.com/{page_id}/posts/{url_post_id}"
    
    import html
    
    # Extract hashtags and SEO Title (Headline)
    lines = facebook_text.split('\n')
    seo_title = lines[0] if lines else "Hollywood Update"
    hashtags = " ".join([word for word in facebook_text.split() if word.startswith("#")])
    
    safe_title = html.escape(title)
    safe_seo_title = html.escape(seo_title)
    safe_facebook_text = html.escape(facebook_text)
    
    image_name = os.path.basename(image_path)
    
    report_text = (
        f"✅ <b>Upload Successfully Completed</b>\n"
        f"🖼️ <b>Image Name:</b>\n{image_name}\n\n"
        f"✅ DOWNLOADED\n"
        f"✏️ EDITED\n"
        f"🚀 UPLOADED\n"
        f"✔️ COMPLETED\n\n"
        f"📤 Facebook Upload Status: Success\n\n"
        f"🏷️ <b>SEO Title:</b>\n{safe_seo_title}\n\n"
        f"📝 <b>Description:</b>\n{safe_facebook_text}\n\n"
        f"Original Title: {safe_title}\n"
        f"Source: {source_url}\n"
        f"Original Image: {image_url}\n\n"
        f"🔗 <b>Facebook Post URL:</b>\n{public_url}\n\n"
        f"📦 <b>GitHub Repository:</b>\nhttps://github.com/{repo}\n\n"
        f"📄 <b>Workflow Run:</b>\nhttps://github.com/{repo}/actions/runs/{run_id}"
    )
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        'chat_id': chat_id,
        'text': report_text,
        'reply_to_message_id': message_id,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        logging.info(f"Successfully sent detailed report for message {message_id}.")
    else:
        logging.error(f"Failed to send detailed report for message {message_id}: {response.text}")

def monitor_telegram_queue():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN_AGENT2") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logging.error("TELEGRAM_BOT_TOKEN_AGENT2 or TELEGRAM_CHAT_ID missing.")
        return

    processed = load_processed_messages()
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    # To avoid retrieving old messages repeatedly, you might want to track the 'offset'.
    # For now, we process all recent updates and filter by our local processed list.
    try:
        response = requests.get(url)
        response.raise_for_status()
        updates = response.json().get('result', [])
    except Exception as e:
        logging.error(f"Error fetching updates: {e}")
        return

    # Telegram naturally returns updates in chronological order. We can ensure we take the oldest pending.
    for update in sorted(updates, key=lambda x: x.get('update_id', 0)):
        # Check if it's a channel post or a regular group message
        message = update.get('channel_post') or update.get('message')
        if not message:
            continue
            
        message_id = str(message.get('message_id'))
        caption = message.get('caption', '')
        
        # We only care about messages that have "STATUS: PENDING"
        if "STATUS: PENDING" in caption and message_id not in processed:
            logging.info(f"Found PENDING message with ID: {message_id}")
            
            # Extract photo
            photos = message.get('photo')
            if not photos:
                logging.warning(f"Message {message_id} has no photo. Skipping.")
                continue
                
            # Telegram provides multiple sizes, the last one is usually the highest resolution
            best_photo = photos[-1]
            file_id = best_photo['file_id']
            
            os.makedirs("output/downloads", exist_ok=True)
            download_path = f"output/downloads/downloaded_{message_id}.jpg"
            
            try:
                # Random Jitter (Human-like behavior)
                random_sleep(max_minutes=1)
                
                download_telegram_photo(file_id, bot_token, download_path)
                
                # Extract Metadata from Telegram caption
                title = "Hollywood Update"
                source_url = "Unknown"
                image_url = "Unknown"
                for line in caption.split('\n'):
                    if line.startswith("TITLE:"):
                        title = line.replace("TITLE:", "").strip()
                    elif line.startswith("SOURCE_URL:"):
                        source_url = line.replace("SOURCE_URL:", "").strip()
                    elif line.startswith("IMAGE_URL:"):
                        image_url = line.replace("IMAGE_URL:", "").strip()
                        
                # Generate Facebook post text
                facebook_text = ""
                try:
                    facebook_text = llm_generate_caption(title)
                except Exception as e:
                    logging.warning("LLM caption generation failed. Using fallback template.")
                    facebook_text = fallback_generate_caption(title)
                
                # Upload to Facebook
                success, post_id = upload_to_facebook(download_path, facebook_text)
                if success and post_id:
                    # Update status in Telegram with Detailed Report
                    send_detailed_report(bot_token, chat_id, message_id, title, facebook_text, post_id, source_url, image_url, download_path)
                    
                    # Mark as processed locally
                    save_processed_message(message_id)
                    
                    logging.info("Successfully processed 1 image. Stopping for this run.")
                    break # Stop after 1 successful upload
            except Exception as e:
                logging.error(f"Failed to process message {message_id}: {e}")

if __name__ == "__main__":
    load_dotenv()
    
    # Fail-Fast Validation
    if not os.getenv("NVIDIA_API_KEY") or not os.getenv("FACEBOOK_ACCESS_TOKEN") or not os.getenv("TELEGRAM_CHAT_ID"):
        logging.error("CRITICAL ERROR: Missing essential environment variables (NVIDIA_API_KEY, FACEBOOK_ACCESS_TOKEN, or TELEGRAM_CHAT_ID). Exiting immediately.")
        exit(1)
        
    logging.info("Starting Agent 2: Telegram Monitor & Uploader")
    monitor_telegram_queue()
