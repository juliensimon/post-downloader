#!/usr/bin/env python3
"""
Process all Medium posts without user interaction
"""

from clean_posts import MediumPostCleaner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Process all posts"""
    cleaner = MediumPostCleaner()
    
    logger.info("=== PROCESSING ALL POSTS ===")
    cleaner.process_all_posts()
    logger.info("All posts processing complete!")

if __name__ == "__main__":
    main() 