import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import logging
import numpy as np
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_font_downloaded(font_url, font_path):
    if not os.path.exists(font_path):
        try:
            r = requests.get(font_url)
            with open(font_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            logging.error(f"Failed to download font: {e}")

def get_font(name="anton", size=40):
    os.makedirs("assets/fonts", exist_ok=True)
    if name == "anton":
        font_path = "assets/fonts/Anton-Regular.ttf"
        font_url = "https://github.com/googlefonts/anton/raw/main/fonts/ttf/Anton-Regular.ttf"
    elif name == "roboto":
        font_path = "assets/fonts/Roboto-Bold.ttf"
        font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    else:
        font_path = "assets/fonts/Roboto-Regular.ttf"
        font_url = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf"
        
    ensure_font_downloaded(font_url, font_path)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def center_crop(img, target_w, target_h):
    """
    Crops the image to the target size from the center.
    """
    img_w, img_h = img.size
    
    ratio = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    
    return img_resized.crop((left, top, left + target_w, top + target_h))

def fetch_image(url):
    try:
        if url.startswith("http"):
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert('RGB')
        else:
            return Image.open(url).convert('RGB')
    except Exception as e:
        logging.error(f"Error downloading image {url}: {e}")
        return None

def draw_gradient(image, top_y, bottom_y, color_start=(0,0,0,0), color_end=(0,0,0,255)):
    """Draws a vertical gradient on the image."""
    draw = ImageDraw.Draw(image, 'RGBA')
    height = bottom_y - top_y
    for i in range(height):
        # Calculate color for this line
        ratio = i / height
        r = int(color_start[0] + ratio * (color_end[0] - color_start[0]))
        g = int(color_start[1] + ratio * (color_end[1] - color_start[1]))
        b = int(color_start[2] + ratio * (color_end[2] - color_start[2]))
        a = int(color_start[3] + ratio * (color_end[3] - color_start[3]))
        draw.line([(0, top_y + i), (image.width, top_y + i)], fill=(r,g,b,a))

def render_multicolor_text_centered(draw, text, y_pos, font, max_width, img_width):
    """
    Renders text centered. Words wrapped in * are yellow (#FFFF00), others white (#FFFFFF).
    Returns the new y_pos.
    """
    # Simple word wrapping
    words = text.split()
    lines = []
    current_line = []
    
    def get_line_width(line_words):
        # strip asterisks for measurement
        clean_text = " ".join(line_words).replace("*", "")
        # Handle fallback for textbbox if Pillow version varies
        try:
            return draw.textbbox((0,0), clean_text, font=font)[2]
        except AttributeError:
            return draw.textsize(clean_text, font=font)[0]

    for word in words:
        current_line.append(word)
        if get_line_width(current_line) > max_width:
            current_line.pop()
            lines.append(current_line)
            current_line = [word]
    if current_line:
        lines.append(current_line)
        
    line_spacing = 10
    
    for line_words in lines:
        line_width = get_line_width(line_words)
        x_pos = (img_width - line_width) // 2
        
        for word in line_words:
            is_highlight = word.startswith("*") and word.endswith("*")
            clean_word = word.replace("*", "")
            color = "#E0FF00" if is_highlight else "#FFFFFF" # Yellow/Greenish highlight
            
            draw.text((x_pos, y_pos), clean_word, font=font, fill=color)
            
            try:
                word_w = draw.textbbox((0,0), clean_word, font=font)[2]
                space_w = draw.textbbox((0,0), " ", font=font)[2]
            except AttributeError:
                word_w = draw.textsize(clean_word, font=font)[0]
                space_w = draw.textsize(" ", font=font)[0]
                
            x_pos += word_w + space_w
            
        try:
            line_height = draw.textbbox((0,0), "A", font=font)[3]
        except AttributeError:
            line_height = draw.textsize("A", font=font)[1]
            
        y_pos += line_height + line_spacing
        
    return y_pos

def create_facebook_post(image_url, image_url_2, headline, source_name="IGN", output_path="output.jpg", logo_path="assets/logo.png"):
    # Premium Layout Dimensions: 1080 x 1350
    base_width, base_height = 1080, 1350
    img_area_height = 950
    bg_color = "#0B0C10" # Dark bottom
    
    base_img = Image.new('RGB', (base_width, base_height), color=bg_color)
    
    # 1. Process Images (Split Screen or Single)
    img1 = fetch_image(image_url) if image_url else None
    img2 = fetch_image(image_url_2) if image_url_2 else None
    
    if img1 and img2:
        # Split screen: left and right
        w1, w2 = 540, 540
        img1_cropped = center_crop(img1, w1, img_area_height)
        img2_cropped = center_crop(img2, w2, img_area_height)
        base_img.paste(img1_cropped, (0, 0))
        base_img.paste(img2_cropped, (w1, 0))
        
        # Add a subtle black divider line
        draw_temp = ImageDraw.Draw(base_img)
        draw_temp.line([(w1, 0), (w1, img_area_height)], fill="#000000", width=4)
        
    elif img1:
        # Single image
        img1_cropped = center_crop(img1, base_width, img_area_height)
        base_img.paste(img1_cropped, (0, 0))
    else:
        # Fallback empty
        pass
        
    # 2. Gradient Overlay for smooth transition
    # From y=600 to y=950
    draw_gradient(base_img, 650, img_area_height, color_start=(11,12,16,0), color_end=(11,12,16,255))
    
    # Needs RGBA composite for gradient to work if base is RGB, actually draw_gradient on RGB will just draw opaque if we don't use alpha composite.
    # Let's fix gradient by creating an overlay
    overlay = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
    draw_gradient(overlay, 650, img_area_height, color_start=(11,12,16,0), color_end=(11,12,16,255))
    base_img = Image.alpha_composite(base_img.convert('RGBA'), overlay).convert('RGB')
    
    draw = ImageDraw.Draw(base_img)
    
    # 3. Logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Resize logo to 80x80
            logo = logo.resize((80, 80), Image.Resampling.LANCZOS)
            base_img.paste(logo, (30, 30), logo)
        except Exception as e:
            logging.error(f"Failed to load logo: {e}")
            
    # 4. NEWS Badge
    badge_w, badge_h = 100, 35
    badge_x = (base_width - badge_w) // 2
    badge_y = 920
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=8, fill="#E0FF00")
    
    badge_font = get_font("roboto", size=18)
    try:
        tw = draw.textbbox((0,0), "NEWS", font=badge_font)[2]
    except AttributeError:
        tw = draw.textsize("NEWS", font=badge_font)[0]
        
    draw.text((badge_x + (badge_w - tw)//2, badge_y + 6), "NEWS", font=badge_font, fill="#000000")
    
    # 5. Headline
    headline_font = get_font("anton", size=65)
    # The headline comes with *keyword* from LLM
    text_start_y = 980
    margin = 60
    max_text_width = base_width - (margin * 2)
    
    render_multicolor_text_centered(draw, headline, text_start_y, headline_font, max_text_width, base_width)
    
    # 6. Source Footer
    footer_font = get_font("roboto", size=18)
    footer_text = f"VIA {source_name.upper()}"
    try:
        fw = draw.textbbox((0,0), footer_text, font=footer_font)[2]
    except AttributeError:
        fw = draw.textsize(footer_text, font=footer_font)[0]
        
    draw.text(((base_width - fw)//2, 1280), footer_text, font=footer_font, fill="#888888")
    
    base_img.save(output_path)
    logging.info(f"Image saved to {output_path} with split screen layout.")
    return output_path
