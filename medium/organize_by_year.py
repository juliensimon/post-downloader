#!/usr/bin/env python3
"""
Organize cleaned posts by year
"""

import os
import re
import shutil
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_year_from_directory_name(dir_name):
    """Extract year from directory name (format: YYYY-MM-DD_title)"""
    # Look for YYYY-MM-DD pattern at the beginning
    match = re.match(r'^(\d{4})-\d{2}-\d{2}', dir_name)
    if match:
        return match.group(1)
    return None

def organize_posts_by_year(source_dir="cleaned_posts", target_dir="posts_by_year"):
    """Organize posts by year into separate directories"""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    if not source_path.exists():
        logger.error(f"Source directory {source_dir} does not exist")
        return
    
    # Create target directory
    target_path.mkdir(exist_ok=True)
    
    # Get all directories in the source
    post_dirs = [d for d in source_path.iterdir() if d.is_dir()]
    
    if not post_dirs:
        logger.warning(f"No directories found in {source_dir}")
        return
    
    logger.info(f"Found {len(post_dirs)} posts to organize")
    
    # Track statistics
    year_stats = {}
    moved_count = 0
    
    for post_dir in post_dirs:
        dir_name = post_dir.name
        year = extract_year_from_directory_name(dir_name)
        
        if not year:
            logger.warning(f"Could not extract year from directory name: {dir_name}")
            continue
        
        # Create year directory if it doesn't exist
        year_dir = target_path / year
        year_dir.mkdir(exist_ok=True)
        
        # Move the post directory to the year directory
        target_post_dir = year_dir / dir_name
        
        if target_post_dir.exists():
            logger.warning(f"Target directory already exists, skipping: {target_post_dir}")
            continue
        
        try:
            shutil.move(str(post_dir), str(target_post_dir))
            logger.info(f"Moved {dir_name} to {year}/")
            
            # Update statistics
            if year not in year_stats:
                year_stats[year] = 0
            year_stats[year] += 1
            moved_count += 1
            
        except Exception as e:
            logger.error(f"Failed to move {dir_name}: {e}")
    
    # Print summary
    logger.info(f"Successfully organized {moved_count} posts by year:")
    for year in sorted(year_stats.keys()):
        logger.info(f"  {year}: {year_stats[year]} posts")
    
    # Check if source directory is now empty
    remaining_dirs = [d for d in source_path.iterdir() if d.is_dir()]
    if not remaining_dirs:
        logger.info(f"Source directory {source_dir} is now empty")
    else:
        logger.warning(f"Source directory {source_dir} still contains {len(remaining_dirs)} directories")

def main():
    """Main function"""
    logger.info("=== ORGANIZING POSTS BY YEAR ===")
    organize_posts_by_year()
    logger.info("Organization complete!")

if __name__ == "__main__":
    main() 