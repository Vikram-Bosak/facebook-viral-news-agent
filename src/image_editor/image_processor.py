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

def create_facebook_post(image_url, headline, hook_text, branding="Celebrity Buzz USA", style="Breaking News Style", output_path="output.jpg", logo_path="logo.png"):
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
    
    # Emotional/Sad Style: Desaturate the image
    if style in ["Emotional Style", "Sad Style"]:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(0.2)
        enhancer_brightness = ImageEnhance.Brightness(img)
        img = enhancer_brightness.enhance(0.7)

    draw = ImageDraw.Draw(img)
    
    main_font = get_font(56)
    hook_font = get_font(40)
    brand_font = get_font(30)
    
    def get_lines(text, font, max_w):
        words = text.split()
        lines, current_line = [], []
        for word in words:
            test_line = current_line + [word]
            clean_text = " ".join(test_line).replace('*', '')
            bbox = draw.textbbox((0, 0), clean_text, font=font)
            if (bbox[2] - bbox[0]) <= max_w:
                current_line.append(word)
            else:
                if current_line: lines.append(current_line)
                current_line = [word]
        if current_line: lines.append(current_line)
        return lines

    def draw_text_with_outline(lines, font, y_pos, line_height, text_color, outline_color, stroke_width=3, center=True, is_impact=False):
        for line_words in lines:
            clean_line = " ".join(line_words).replace('*', '')
            bbox = draw.textbbox((0, 0), clean_line, font=font)
            line_width = bbox[2] - bbox[0]
            x = (1080 - line_width) / 2 if center else 60
            
            is_highlight = False
            for i, word in enumerate(line_words):
                if word.startswith('*'):
                    is_highlight = True
                    word = word[1:]
                end_highlight = False
                if word.endswith('*'):
                    end_highlight = True
                    word = word[:-1]
                    
                current_color = "#FFD700" if is_highlight and not is_impact else text_color
                if is_impact:
                    current_color = "#FFD700"
                    outline_color = "#000000"
                
                # Draw Outline
                if outline_color:
                    draw.text((x-stroke_width, y_pos-stroke_width), word, font=font, fill=outline_color)
                    draw.text((x+stroke_width, y_pos-stroke_width), word, font=font, fill=outline_color)
                    draw.text((x-stroke_width, y_pos+stroke_width), word, font=font, fill=outline_color)
                    draw.text((x+stroke_width, y_pos+stroke_width), word, font=font, fill=outline_color)
                
                draw.text((x, y_pos), word, font=font, fill=current_color)
                
                bbox_word = draw.textbbox((0, 0), word, font=font)
                x += (bbox_word[2] - bbox_word[0])
                if end_highlight: is_highlight = False
                if i < len(line_words) - 1:
                    space_bbox = draw.textbbox((0, 0), " ", font=font)
                    x += (space_bbox[2] - space_bbox[0])
            y_pos += line_height
        return y_pos

    # Apply Style Logic
    if style in ["Meme Style", "Funny Style", "Celebrity Reaction Style", "Comparison Style"]:
        headline_lines = get_lines(headline, main_font, 960)
        hook_lines = get_lines(hook_text, hook_font, 960)
        
        # Impact Meme Style Layout
        draw_text_with_outline(headline_lines, main_font, 80, 60, "#FFD700", "#000000", stroke_width=4, is_impact=True)
        draw_text_with_outline(hook_lines, hook_font, 1080 - 150 - (len(hook_lines) * 45), 45, "#FFFFFF", "#000000", stroke_width=3)
        
    elif style in ["Storytelling Style", "Emotional Style", "Sad Style"]:
        # Heavy Bottom Gradient
        draw_gradient_overlay(img)
        headline_lines = get_lines(headline, main_font, 960)
        hook_lines = get_lines(hook_text, hook_font, 960)
        
        total_h = (len(headline_lines) * 60) + (len(hook_lines) * 45) + 40
        start_y = 1080 - 150 - total_h
        
        start_y = draw_text_with_outline(headline_lines, main_font, start_y, 60, "#FFFFFF", None, center=False)
        start_y += 20
        draw_text_with_outline(hook_lines, hook_font, start_y, 45, "#CCCCCC", None, center=False)
        
    else: # Breaking News Style (Default)
        headline_lines = get_lines(headline, main_font, 960)
        headline_h = len(headline_lines) * 60 + 60
        
        # Top Yellow Banner
        draw.rectangle([0, 0, 1080, headline_h], fill="#FFD700")
        draw_text_with_outline(headline_lines, main_font, 30, 60, "#000000", None)
        
        hook_lines = get_lines(hook_text, hook_font, 960)
        hook_h = len(hook_lines) * 45 + 60
        
        # Bottom Black Banner
        draw.rectangle([0, 1080 - hook_h - 100, 1080, 1080], fill="#000000")
        draw_text_with_outline(hook_lines, hook_font, 1080 - hook_h - 70, 45, "#FFFFFF", None)

    # Branding Logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((50, 50), Image.Resampling.LANCZOS)
            img.paste(logo, (40, 1080 - 70), logo)
            draw.text((100, 1080 - 60), branding, font=brand_font, fill=(200, 200, 200))
        except Exception:
            draw.text((40, 1080 - 60), branding, font=brand_font, fill=(200, 200, 200))
    else:
        draw.text((40, 1080 - 60), branding, font=brand_font, fill=(200, 200, 200))
        
    img.save(output_path)
    logging.info(f"Image saved to {output_path} with style: {style}")
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
