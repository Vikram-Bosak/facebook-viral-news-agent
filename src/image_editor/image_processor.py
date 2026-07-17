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
        
    # Delete corrupted files (< 10KB)
    if os.path.exists(font_path) and os.path.getsize(font_path) < 10000:
        os.remove(font_path)
        
    ensure_font_downloaded(font_url, font_path)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        logging.warning(f"Failed to load downloaded font, falling back to Impact/Arial. Error: {e}")
        try:
            # Fallback to standard Windows bold font
            return ImageFont.truetype("impact.ttf", size)
        except Exception:
            try:
                return ImageFont.truetype("arialbd.ttf", size)
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

def render_multicolor_text_centered(draw, text, y_pos, font, max_width, img_width, dry_run=False):
    """
    Renders text centered, wrapping it, and colors *asterisk* text in yellow.
    If dry_run is True, it doesn't draw anything, just returns the total height of the text block.
    """
    # Parse tokens and their highlight states
    tokens = []
    in_highlight = False
    for word in text.split():
        if word.startswith("*"):
            in_highlight = True
            
        ends_with = word.endswith("*") and len(word) > 1
        clean_word = word.replace("*", "")
        
        tokens.append({"text": clean_word, "highlight": in_highlight})
        
        if ends_with:
            in_highlight = False

    lines = []
    current_line = []
    
    def get_line_width(line_tokens):
        clean_text = " ".join([t["text"] for t in line_tokens])
        try:
            bbox = draw.textbbox((0, 0), clean_text, font=font)
            return bbox[2] - bbox[0]
        except AttributeError:
            return draw.textsize(clean_text, font=font)[0]

    for token in tokens:
        current_line.append(token)
        if get_line_width(current_line) > max_width:
            current_line.pop()
            lines.append(current_line)
            current_line = [token]
    if current_line:
        lines.append(current_line)
        
    line_spacing = 10
    total_height = 0
    
    # Calculate line height
    try:
        bbox_A = draw.textbbox((0, 0), "A", font=font)
        line_height = bbox_A[3] - bbox_A[1]
    except AttributeError:
        line_height = draw.textsize("A", font=font)[1]
    
    actual_line_height = line_height * 0.95 + line_spacing
    total_height = len(lines) * actual_line_height
    
    if dry_run:
        return total_height
    
    for line_tokens in lines:
        line_width = get_line_width(line_tokens)
        x_pos = (img_width - line_width) // 2
        
        for token in line_tokens:
            clean_word = token["text"]
            color = "#E0FF00" if token["highlight"] else "#FFFFFF" # Yellow/Greenish highlight
            
            draw.text((x_pos, y_pos), clean_word, font=font, fill=color)
            
            try:
                bbox_word = draw.textbbox((0, 0), clean_word, font=font)
                word_w = bbox_word[2] - bbox_word[0]
                bbox_space = draw.textbbox((0, 0), " ", font=font)
                space_w = bbox_space[2] - bbox_space[0]
            except AttributeError:
                word_w = draw.textsize(clean_word, font=font)[0]
                space_w = draw.textsize(" ", font=font)[0]
                
            x_pos += word_w + space_w
            
        y_pos += actual_line_height
        
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
        
    # From y=600 to y=1050 for a taller gradient for bigger text
    draw_gradient(base_img, 600, 1050, color_start=(11,12,16,0), color_end=(11,12,16,255))
    
    # Needs RGBA composite for gradient to work if base is RGB, actually draw_gradient on RGB will just draw opaque if we don't use alpha composite.
    # Let's fix gradient by creating an overlay
    overlay = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
    draw_gradient(overlay, 600, 1050, color_start=(11,12,16,0), color_end=(11,12,16,255))
    base_img = Image.alpha_composite(base_img.convert('RGBA'), overlay).convert('RGB')
    
    draw = ImageDraw.Draw(base_img)
    
    # 3. Top Banner (replacing logo)
    banner_path = "assets/logo/banner.png"
    if os.path.exists(banner_path):
        try:
            banner = Image.open(banner_path).convert("RGBA")
            # Resize banner so it spans nicely across the top (e.g. 600px wide)
            bw, bh = banner.size
            new_bw = 700
            new_bh = int(bh * (new_bw / bw))
            banner = banner.resize((new_bw, new_bh), Image.Resampling.LANCZOS)
            
            # Place at top center
            bx = (base_width - new_bw) // 2
            by = 40
            base_img.paste(banner, (bx, by), banner)
        except Exception as e:
            logging.error(f"Failed to load banner: {e}")
            
    # 4. Determine font size
    headline_length = len(headline)
    if headline_length < 40:
        font_size = 130
    elif headline_length < 70:
        font_size = 100
    elif headline_length < 100:
        font_size = 80
    else:
        font_size = 64
        
    headline_font = get_font("anton", size=font_size)
    
    # Calculate text height to bottom-align
    margin = 40
    max_text_width = base_width - (margin * 2)
    text_total_height = render_multicolor_text_centered(draw, headline, 0, headline_font, max_text_width, base_width, dry_run=True)
    
    # Bottom margin padding
    bottom_padding = 60
    
    # 5. Position Elements (Bottom-aligned)
    # The text ends at (base_height - bottom_padding)
    text_start_y = base_height - bottom_padding - text_total_height
    
    # Badge sits above the text
    badge_text = "HOLLYWOOD FLASH"
    badge_font = get_font("roboto", size=20)
    try:
        bbox_badge = draw.textbbox((0, 0), badge_text, font=badge_font)
        tw = bbox_badge[2] - bbox_badge[0]
    except AttributeError:
        tw = draw.textsize(badge_text, font=badge_font)[0]
        
    badge_w = tw + 30
    badge_h = 35
    badge_x = (base_width - badge_w) // 2
    badge_y = text_start_y - badge_h - 25
    
    # Draw badge
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=6, fill="#E0FF00")
    draw.text((badge_x + 15, badge_y + 8), badge_text, font=badge_font, fill="#000000")
    
    # Draw Headline
    render_multicolor_text_centered(draw, headline, text_start_y, headline_font, max_text_width, base_width)
    
    # 6. Source Footer (Removed per user request)
    base_img.save(output_path)
    logging.info(f"Image saved to {output_path} with split screen layout.")
    return output_path
