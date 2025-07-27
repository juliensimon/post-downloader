#!/usr/bin/env python3
"""
Reprocess a single post to check for issues
"""

from clean_posts import MediumPostCleaner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Reprocess the webinar post"""
    cleaner = MediumPostCleaner()
    
    # Process just the webinar post
    html_file = cleaner.posts_dir / "2018-04-05_Webinar--Building-Your-Smart-Applications-with-Amazon-AI-4f8e10375bad.html"
    
    if html_file.exists():
        logger.info(f"Reprocessing: {html_file}")
        cleaner.process_post(html_file)
        logger.info("Reprocessing complete!")
    else:
        logger.error(f"File not found: {html_file}")

if __name__ == "__main__":
    main() 