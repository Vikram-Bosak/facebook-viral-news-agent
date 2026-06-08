import os
import requests
import logging

def send_telegram_photo(photo_path, caption):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logging.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing. Skipping Telegram report.")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            logging.info("Telegram photo report sent successfully.")
            return True
    except Exception as e:
        logging.error(f"Failed to send Telegram photo: {e}")
        return False
