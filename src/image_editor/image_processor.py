import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
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
        font_url = "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"
        if not os.path.exists(font_path) or os.path.getsize(font_path) < 10000: # Check if corrupted
            import requests
            try:
                logging.info(f"Downloading {name} font from {font_url}...")
                r = requests.get(font_url)
                r.raise_for_status()
                with open(font_path, "wb") as f:
                    f.write(r.content)
            except Exception as e:
                logging.warning(f"Failed to download font: {e}")
        try:
            font = ImageFont.truetype(font_path, size)
            return font
        except Exception as e:
            logging.warning(f"Failed to load downloaded font, falling back to Impact/Arial. Error: {e}")
            try:
                return ImageFont.truetype("impact.ttf", size)
            except Exception:
                try:
                    return ImageFont.truetype("arialbd.ttf", size)
                except Exception:
                    return ImageFont.load_default()
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

def draw_circular_badge(base_img, flag_url_or_path, size=300, pos_x=70, pos_y=600):
    badge_img = fetch_image(flag_url_or_path)
    if not badge_img:
        # Fallback to a solid circle if loading fails
        badge_img = Image.new('RGB', (size, size), "#FF3366")
        
    # Fit the image entirely inside the circular badge (Fit to Circle) without cropping any part
    badge_img.thumbnail((size, size), Image.Resampling.LANCZOS)
    
    # Create a square background image and paste the resized image centered
    square_img = Image.new('RGB', (size, size), "#000000")
    w, h = badge_img.size
    square_img.paste(badge_img, ((size - w) // 2, (size - h) // 2))
    badge_img = square_img
    
    # Create a circular mask
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)
    
    # Convert badge to RGBA
    circular_badge = Image.new('RGBA', (size, size), (0,0,0,0))
    circular_badge.paste(badge_img.convert("RGBA"), (0, 0), mask)
    
    # Draw a nice white border around the circle
    draw_border = ImageDraw.Draw(circular_badge)
    draw_border.ellipse((0, 0, size, size), outline="#FFFFFF", width=4)
    
    # Draw drop shadow for the "embedded" ("fansa hua") effect
    shadow_size = size + 30
    shadow = Image.new('RGBA', (shadow_size, shadow_size), (0,0,0,0))
    draw_shadow = ImageDraw.Draw(shadow)
    # Soft black circle for shadow
    shadow_offset = 15
    draw_shadow.ellipse((0, 0, shadow_size, shadow_size), fill=(0, 0, 0, 180))
    # Blur the shadow circle
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    
    # Paste shadow then badge
    base_img.paste(shadow, (pos_x - shadow_offset, pos_y - shadow_offset), shadow)
    base_img.paste(circular_badge, (pos_x, pos_y), circular_badge)



def render_multicolor_text_centered(draw, text, y_pos, font, max_width, img_width, dry_run=False):
    """
    Renders text centered, wrapping it, with line spacing (0.9).
    """
    # Parse tokens and their highlight states
    tokens = []
    in_highlight = False
    highlight_idx = -1
    for word in text.split():
        # Check start (ignore leading punctuation like quotes)
        if "*" in word and word.find("*") < len(word) / 2:
            if not in_highlight:
                in_highlight = True
                highlight_idx += 1
            
        # Check end (asterisk could be before trailing punctuation)
        ends_with = "*" in word[len(word)//2:] and len(word) > 1
        
        clean_word = word.replace("*", "")
        
        tokens.append({"text": clean_word, "highlight": in_highlight, "color_idx": highlight_idx})
        
        if ends_with:
            in_highlight = False

    lines = []
    current_line = []
    
    def get_word_width(word):
        try:
            bbox_word = draw.textbbox((0, 0), word, font=font)
            return bbox_word[2] - bbox_word[0]
        except AttributeError:
            return draw.textsize(word, font=font)[0]
        
    try:
        space_w = draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]
    except AttributeError:
        space_w = draw.textsize(" ", font=font)[0]
        
    def get_line_width(line_tokens):
        if not line_tokens:
            return 0
        total = sum(get_word_width(t["text"]) for t in line_tokens)
        total += space_w * (len(line_tokens) - 1)
        return total

    for token in tokens:
        current_line.append(token)
        if get_line_width(current_line) > max_width:
            current_line.pop()
            lines.append(current_line)
            current_line = [token]
    if current_line:
        lines.append(current_line)
        
    # Calculate line height using ascent + descent
    try:
        ascent, descent = font.getmetrics()
        line_height = ascent + descent
    except Exception:
        try:
            bbox_A = draw.textbbox((0, 0), "hg", font=font)
            line_height = bbox_A[3] - bbox_A[1]
        except AttributeError:
            line_height = draw.textsize("hg", font=font)[1]
    
    # Line spacing is exactly 0.9 of line height
    actual_line_height = line_height * 0.9
    total_height = len(lines) * actual_line_height
    
    if dry_run:
        return total_height
    
    for line_tokens in lines:
        line_width = get_line_width(line_tokens)
        x_pos = (img_width - line_width) // 2
        
        for token in line_tokens:
            clean_word = token["text"]
            if token["highlight"]:
                # Premium multicolor palette (Orange/Red, Blue, Green, Yellow)
                HIGHLIGHT_COLORS = ["#FF5733", "#00BFFF", "#2ECC71", "#FFD700"]
                color = HIGHLIGHT_COLORS[token["color_idx"] % len(HIGHLIGHT_COLORS)]
            else:
                color = "#FFFFFF"
            
            # Draw full word directly to ensure perfect anti-aliasing and sharpness
            draw.text((x_pos, y_pos), clean_word, font=font, fill=color)
            x_pos += get_word_width(clean_word) + space_w
            
        y_pos += actual_line_height
        
    return y_pos

def create_facebook_post(image_url, image_url_2, headline, source_name="IGN", output_path="output.jpg", logo_path="assets/logo.png", hook_text="", circle_image_url=None):
    # If circle_image_url is not explicitly passed, use image_url_2 as the circular badge if present,
    # and clear image_url_2 so the main layout remains a premium single full image.
    if not circle_image_url and image_url_2:
        circle_image_url = image_url_2
        image_url_2 = None
        
    # Premium Layout Dimensions: 1080 x 1350
    base_width, base_height = 1080, 1350
    bg_color = "#0B0C10" # Solid dark bottom background
    
    base_img = Image.new('RGB', (base_width, base_height), color=bg_color)
    
    # 1. Process Images (Split Screen or Single)
    img1 = fetch_image(image_url) if image_url else None
    img2 = fetch_image(image_url_2) if image_url_2 else None
    
    # Apply Copyright Safety Logic (Horizontal Flip + Minor Brightness Jitter)
    def apply_safety(img):
        if not img: return None
        img = ImageOps.mirror(img)
        # Apply a tiny undetectable brightness shift to change image hash completely
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1.02) # +2% brightness
        
    img1 = apply_safety(img1)
    img2 = apply_safety(img2)
    
    if img1 and img2:
        # Split screen: left and right
        w1, w2 = 540, 540
        img1_cropped = center_crop(img1, w1, base_height)
        img2_cropped = center_crop(img2, w2, base_height)
        base_img.paste(img1_cropped, (0, 0))
        base_img.paste(img2_cropped, (w1, 0))
        
        # Add a subtle black divider line
        draw_temp = ImageDraw.Draw(base_img)
        draw_temp.line([(w1, 0), (w1, base_height)], fill="#000000", width=4)
    elif img1:
        # Full screen background image (slightly blurred)
        img1_blurred = img1.filter(ImageFilter.GaussianBlur(3))
        img1_cropped = center_crop(img1_blurred, base_width, base_height)
        base_img.paste(img1_cropped, (0, 0))
    else:
        # Fallback empty
        pass
        
    # Draw vertical gradient overlay from y=600 to y=1050 over the photo area
    overlay = Image.new('RGBA', (base_width, base_height), (0,0,0,0))
    draw_gradient(overlay, 600, 1050, color_start=(11,12,16,0), color_end=(11,12,16,255))
    base_img = Image.alpha_composite(base_img.convert('RGBA'), overlay).convert('RGB')
    
    draw = ImageDraw.Draw(base_img)
    
    # Draw solid black background for text area below y=1050
    draw.rectangle([(0, 1050), (base_width, base_height)], fill="#0B0C10")
    
    # 2. Position Circular Badge completely inside the photo area (centered vertically in the photo zone)
    badge_size = 300
    pos_y = int(700 - badge_size // 2) # Centered at y=700 (ends at y=850, well above black zone at y=950)
    
    # Check headline to alternate sides dynamically
    if len(headline) % 2 == 0:
        pos_x = 70
    else:
        pos_x = base_width - badge_size - 70
        
    pos_x = int(pos_x)
    pos_y = int(pos_y)
        
    draw_circular_badge(
        base_img, 
        flag_url_or_path=circle_image_url or "https://flagcdn.com/w640/us.png", 
        size=badge_size, 
        pos_x=pos_x, 
        pos_y=pos_y
    )
    
    # 3. Format and Position Text (Centered All-Caps Fact Details)
    # Combine headline and hook into a single block of uppercase text
    if hook_text:
        combined_text = f"{headline} {hook_text}".upper()
    else:
        combined_text = headline.upper()
        
    # Sanitize combined text
    combined_text = combined_text.replace("’", "'").replace("“", '"').replace("”", '"')
    combined_text = re.sub(r'[^\x00-\x7F*]+', '', combined_text)
    
    # Revert to first design font size selection logic
    headline_length = len(combined_text)
    if headline_length < 40:
        font_size = 110
    elif headline_length < 70:
        font_size = 85
    elif headline_length < 100:
        font_size = 68
    else:
        font_size = 54
        
    text_font = get_font("anton", size=font_size)
    
    margin = 50
    max_text_width = base_width - (margin * 2)
    
    # Measure text block height
    text_total_height = render_multicolor_text_centered(draw, combined_text, 0, text_font, max_text_width, base_width, dry_run=True)
    
    # Bottom margin padding is exactly 60px
    bottom_padding = 60
    
    # Position Elements (Bottom-aligned)
    text_start_y = base_height - bottom_padding - text_total_height
    
    # Paste uploaded logo banner image above the text if it exists
    banner_path = "assets/logo/banner.png"
    if os.path.exists(banner_path):
        try:
            banner = Image.open(banner_path).convert("RGBA")
            bw, bh = banner.size
            new_bw = 500
            new_bh = int(bh * (new_bw / bw))
            banner = banner.resize((new_bw, new_bh), Image.Resampling.LANCZOS)
            
            bx = int((base_width - new_bw) // 2)
            by = int(text_start_y - new_bh - 25)
            base_img.paste(banner, (bx, by), banner)
        except Exception as e:
            logging.error(f"Failed to load user banner logo: {e}")
            
    # Draw the text
    render_multicolor_text_centered(draw, combined_text, text_start_y, text_font, max_text_width, base_width)
    
    # Ensure output directory exists
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    # Save Image
    base_img.save(output_path, quality=95)
    logging.info(f"Image saved to {output_path} with split screen layout.")
    return output_path
