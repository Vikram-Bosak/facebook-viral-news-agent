import sys
import os
import logging
from src.image_editor.image_processor import create_facebook_post
from src.scraper.image_search import get_related_image

logging.basicConfig(level=logging.INFO)

def run():
    headline = "*BERNIE SANDERS* WANTS TO TAX AMERICA'S *938 BILLIONAIRES 5%* EACH YEAR AND USE THE *$4.4 TRILLION* TO GIVE EVERY FAMILY A *$12,000 CHECK*, INCREASE TEACHER SALARIES, AND *EXPAND MEDICARE*."
    
    # Search for a clean background image of Bernie Sanders laughing
    bg_image = get_related_image("Bernie Sanders laughing") or "https://upload.wikimedia.org/wikipedia/commons/0/0f/Bernie_Sanders_in_March_2020.jpg"
    print("Background image found:", bg_image.encode('ascii', 'ignore').decode('ascii'))
    
    # Search for a related news subject image for the circle badge (e.g. Bernie Sanders portrait)
    circle_image = get_related_image("Bernie Sanders portrait", avoid_url=bg_image) or bg_image
    print("Circle badge image found:", circle_image.encode('ascii', 'ignore').decode('ascii'))
    
    create_facebook_post(
        image_url=bg_image,
        image_url_2=circle_image, # Related portrait inside the circular badge
        headline=headline,
        source_name="JJEFFROSE",
        output_path="test_bernie.jpg",
        logo_path="assets/logo/logo.png"
    )
    print("SUCCESS: Image generated at test_bernie.jpg")

if __name__ == "__main__":
    run()
