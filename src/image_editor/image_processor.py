import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_font_downloaded(font_url, font_path):
    if not os.path.exists(font_path):
        try:
            logging.info(f"Downloading font from {font_url}")
            r = requests.get(font_url)
            with open(font_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logging.error(f"Failed to download font: {e}")

def get_font(size):
    font_path = "assets/templates/Roboto-Bold.ttf"
    font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    ensure_font_downloaded(font_url, font_path)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def download_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        logging.error(f"Error downloading image: {e}")
        return None

def draw_gradient_overlay(img):
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = img.size
    gradient_start_y = int(height * 0.3) 
    
    for y in range(gradient_start_y, height):
        opacity = int(255 * ((y - gradient_start_y) / (height - gradient_start_y)))
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, opacity))
        
    img.paste(overlay, (0, 0), overlay)

def create_facebook_post(image_url, headline, hook_text, branding="Celebrity Buzz USA", output_path="output.jpg", logo_path="logo.png"):
    img = download_image(image_url)
    if not img:
        img = Image.new('RGB', (1080, 1080), color=(30, 30, 30))
    else:
        img = img.convert('RGB')
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        img = img.crop((left, top, right, bottom))
        img = img.resize((1080, 1080), Image.Resampling.LANCZOS)
        
    draw_gradient_overlay(img)
    
    draw = ImageDraw.Draw(img)
    
    border_inset = 15
    border_width = 3
    draw.rectangle(
        [border_inset, border_inset, 1080 - border_inset, 1080 - border_inset],
        outline=(255, 255, 255, 180),
        width=border_width
    )
    
    main_font = get_font(56) # Slightly larger for headline
    hook_font = get_font(40) # Smaller for hook
    brand_font = get_font(30)
    
    margin = 60
    max_width = 1080 - (margin * 2)
    
    def get_lines(text, font):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = current_line + [word]
            clean_text = " ".join(test_line).replace('*', '')
            bbox = draw.textbbox((0, 0), clean_text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(current_line)
                current_line = [word]
        if current_line: lines.append(current_line)
        return lines

    headline_lines = get_lines(headline, main_font)
    hook_lines = get_lines(hook_text, hook_font)

    line_spacing = 20
    h_bbox_main = draw.textbbox((0, 0), "A", font=main_font)
    line_height_main = (h_bbox_main[3] - h_bbox_main[1]) + line_spacing
    
    h_bbox_hook = draw.textbbox((0, 0), "A", font=hook_font)
    line_height_hook = (h_bbox_hook[3] - h_bbox_hook[1]) + line_spacing

    total_text_height = (len(headline_lines) * line_height_main) + (len(hook_lines) * line_height_hook) + 40 # 40px gap
    
    start_y = 960 - total_text_height
    
    def draw_lines(lines, font, y_pos, line_height):
        is_highlight = False 
        for line_words in lines:
            clean_line = " ".join(line_words).replace('*', '')
            bbox = draw.textbbox((0, 0), clean_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            x = (1080 - line_width) / 2
            
            for i, word in enumerate(line_words):
                if word.startswith('*'):
                    is_highlight = True
                    word = word[1:]
                
                end_highlight = False
                if word.endswith('*'):
                    end_highlight = True
                    word = word[:-1]
                    
                color = "#FFD700" if is_highlight else "#FFFFFF"
                draw.text((x + 3, y_pos + 3), word, font=font, fill=(0, 0, 0, 200))
                draw.text((x, y_pos), word, font=font, fill=color)
                
                bbox_word = draw.textbbox((0, 0), word, font=font)
                x += (bbox_word[2] - bbox_word[0])
                
                if end_highlight:
                    is_highlight = False
                    
                if i < len(line_words) - 1:
                    space_bbox = draw.textbbox((0, 0), " ", font=font)
                    x += (space_bbox[2] - space_bbox[0])
                    
            y_pos += line_height
        return y_pos

    start_y = draw_lines(headline_lines, main_font, start_y, line_height_main)
    start_y += 40 # gap
    draw_lines(hook_lines, hook_font, start_y, line_height_hook)
        
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo_size = 60
            logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            branding_bbox = draw.textbbox((0, 0), branding, font=brand_font)
            bw = branding_bbox[2] - branding_bbox[0]
            
            total_width = logo.width + 15 + bw
            start_x = (1080 - total_width) / 2
            ly = 1080 - 70 - int((logo.height - (branding_bbox[3] - branding_bbox[1])) / 2)
            img.paste(logo, (int(start_x), ly), logo)
            
            tx = start_x + logo.width + 15
            ty = 1080 - 70
            draw.text((tx + 2, ty + 2), branding, font=brand_font, fill=(0, 0, 0, 200))
            draw.text((tx, ty), branding, font=brand_font, fill=(220, 220, 220))
        except Exception as e:
            logging.error(f"Failed to add logo: {e}")
            branding_bbox = draw.textbbox((0, 0), branding, font=brand_font)
            bw = branding_bbox[2] - branding_bbox[0]
            bx = (1080 - bw) / 2
            draw.text((bx + 2, 1080 - 70 + 2), branding, font=brand_font, fill=(0, 0, 0, 200))
            draw.text((bx, 1080 - 70), branding, font=brand_font, fill=(220, 220, 220))
    else:
        branding_bbox = draw.textbbox((0, 0), branding, font=brand_font)
        bw = branding_bbox[2] - branding_bbox[0]
        bx = (1080 - bw) / 2
        draw.text((bx + 2, 1080 - 70 + 2), branding, font=brand_font, fill=(0, 0, 0, 200))
        draw.text((bx, 1080 - 70), branding, font=brand_font, fill=(220, 220, 220))
        
    img.save(output_path)
    logging.info(f"Image saved to {output_path}")
    return output_path

if __name__ == "__main__":
    sample_headline = "Shocking Update on *Tom Cruise*!"
    sample_hook = "The entire internet is talking about this shocking Hollywood update. What do you think about the *latest drama*?"
    create_facebook_post(
        "https://images.unsplash.com/photo-1598899134739-24c46f58b8c0?q=80&w=1080&auto=format&fit=crop", 
        headline=sample_headline, 
        hook_text=sample_hook,
        branding="Celebrity Buzz USA",
        output_path="test_output.jpg"
    )
