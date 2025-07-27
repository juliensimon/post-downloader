#!/usr/bin/env python3
"""
Medium Posts Cleaner

This script processes Medium posts by:
1. Downloading remote images and converting them to WebP format
2. Updating image links in the HTML to reference local images
3. Preserving embedded content like videos and gists
4. Removing peripheral content (header, footer, etc.)
5. Keeping only the post content
6. Not updating links to other posts
"""

import os
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image
import io
import hashlib
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediumPostCleaner:
    def __init__(self, posts_dir="posts", output_dir="cleaned_posts"):
        self.posts_dir = Path(posts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create a session for downloading images
        self.session = urllib.request.build_opener()
        self.session.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        
    def sanitize_filename(self, filename):
        """Sanitize filename for safe filesystem usage"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename
    
    def download_image(self, url, output_path):
        """Download an image from URL and save it as WebP with throttling"""
        try:
            logger.info(f"Downloading: {url}")
            
            # Add delay to be respectful to servers
            time.sleep(2.0)
            
            # Download the image
            response = self.session.open(url)
            
            # Handle rate limiting
            if response.status == 429:
                logger.warning(f"Rate limited (429) for {url}, waiting 30 seconds...")
                time.sleep(30)
                response = self.session.open(url)
                if response.status == 429:
                    logger.error(f"Still rate limited, skipping {url}")
                    return False
            
            if response.status != 200:
                logger.warning(f"Failed to download {url}: HTTP {response.status}")
                return False
                
            image_data = response.read()
            
            # Try to open with PIL to validate it's an image
            try:
                image = Image.open(io.BytesIO(image_data))
                # Convert to RGB if necessary (for WebP compatibility)
                if image.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background for transparent images
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Save as WebP
                image.save(output_path, 'WEBP', quality=85, optimize=True)
                logger.info(f"Saved as WebP: {output_path}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to process image {url}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
    
    def extract_image_urls(self, html_content):
        """Extract all image URLs from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = []
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # Handle relative URLs
                if src.startswith('http'):
                    image_urls.append(src)
                elif src.startswith('//'):
                    image_urls.append('https:' + src)
        
        return list(set(image_urls))  # Remove duplicates
    
    def generate_image_filename(self, image_number):
        """Generate a filename for the downloaded image using sequential naming"""
        return f"image{image_number:02d}.webp"
    
    def clean_html(self, html_content):
        """Clean up HTML content, removing peripheral content and preserving embedded content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove header, footer, and other peripheral content
        for element in soup.find_all(['header', 'footer']):
            element.decompose()
        
        # Remove subtitle and description sections
        for section in soup.find_all('section', attrs={'data-field': ['subtitle', 'description']}):
            section.decompose()
        
        # Remove script elements (but preserve embedded content)
        for script in soup.find_all('script'):
            # Keep gist scripts, remove others
            if not script.get('src', '').startswith('https://gist.github.com'):
                script.decompose()
        
        # Remove unwanted data attributes from images
        for img in soup.find_all('img'):
            for attr in ['data-image-id', 'data-width', 'data-height', 'data-is-featured']:
                if img.has_attr(attr):
                    del img[attr]
        
        # Remove unwanted data attributes from links
        for link in soup.find_all('a'):
            if link.has_attr('data-href'):
                del link['data-href']
            for attr in ['data-action', 'data-action-observe-only']:
                if link.has_attr(attr):
                    del link[attr]
            if link.has_attr('rel') and link['rel'] == ['noopener']:
                del link['rel']
        
        # Remove unwanted attributes from other elements
        for element in soup.find_all():
            if element.has_attr('data-paragraph-count'):
                del element['data-paragraph-count']
            if element.has_attr('name'):
                del element['name']
        
        # Clean up CSS classes (remove Medium-specific classes)
        for element in soup.find_all():
            if element.has_attr('class'):
                classes = element.get('class', [])
                # Remove Medium-specific classes
                medium_classes = [
                    'graf', 'markup--anchor', 'markup--p-anchor', 'markup--li-anchor',
                    'markup--em', 'markup--strong', 'markup--h3-anchor', 'markup--h4-anchor',
                    'graf--h3', 'graf--p', 'graf--h4', 'graf--li', 'graf--figure',
                    'graf--iframe', 'graf--layoutFillWidth', 'graf--layoutOutsetCenter',
                    'graf--layoutOutsetRow', 'graf--leading', 'graf--title',
                    'graf--startsWithDoubleQuote', 'graf-after--h3', 'graf-after--p',
                    'graf-after--h4', 'graf-after--figure', 'graf-after--li',
                    'is-partialWidth', 'graf--trailing', 'section--body',
                    'section--first', 'section--last', 'section-divider',
                    'section-content', 'section-inner', 'sectionLayout--insetColumn',
                    'sectionLayout--fullWidth', 'sectionLayout--outsetColumn',
                    'sectionLayout--outsetRow', 'imageCaption', 'graf-imageAnchor'
                ]
                # Filter out Medium-specific classes
                cleaned_classes = [cls for cls in classes if cls not in medium_classes]
                if cleaned_classes:
                    element['class'] = cleaned_classes
                else:
                    del element['class']
        
        return str(soup)
    
    def update_html_images(self, html_content, image_mapping):
        """Update HTML content to reference local images"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if src in image_mapping:
                img['src'] = image_mapping[src]
                logger.info(f"Updated image link: {src} -> {image_mapping[src]}")
        
        return str(soup)
    
    def create_post_directory_name(self, html_file):
        """Create a clean directory name from the HTML filename"""
        # Extract the base name without extension
        base_name = html_file.stem
        
        # Remove UUID-like parts (typically at the end, 8-12 characters)
        if '-' in base_name:
            parts = base_name.split('-')
            if len(parts) > 1:
                last_part = parts[-1]
                # Check if the last part looks like a UUID (8-12 alphanumeric characters)
                if len(last_part) >= 8 and len(last_part) <= 12 and last_part.isalnum():
                    # Remove the UUID part
                    clean_name = '-'.join(parts[:-1])
                else:
                    clean_name = base_name
            else:
                clean_name = base_name
        else:
            clean_name = base_name
        
        return self.sanitize_filename(clean_name)
    
    def process_post(self, html_file):
        """Process a single post"""
        logger.info(f"Processing: {html_file}")
        
        # Read the HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract image URLs
        image_urls = self.extract_image_urls(html_content)
        logger.info(f"Found {len(image_urls)} images in {html_file.name}")
        
        # Create post directory
        post_dir_name = self.create_post_directory_name(html_file)
        post_dir = self.output_dir / post_dir_name
        post_dir.mkdir(exist_ok=True)
        
        # Download and convert images
        image_mapping = {}
        image_counter = 1
        
        for url in image_urls:
            try:
                # Generate filename for the image using sequential numbering
                image_filename = self.generate_image_filename(image_counter)
                image_path = post_dir / image_filename
                
                # Download and convert the image
                if self.download_image(url, image_path):
                    # Update the mapping
                    image_mapping[url] = image_filename
                    # Increment counter only for successfully downloaded images
                    image_counter += 1
                else:
                    logger.warning(f"Failed to download image: {url}")
                    
            except Exception as e:
                logger.error(f"Error processing image {url}: {e}")
        
        # Clean up the HTML content (remove peripheral content, preserve embedded content)
        cleaned_html = self.clean_html(html_content)
        
        # Update the HTML with local image references
        if image_mapping:
            updated_html = self.update_html_images(cleaned_html, image_mapping)
        else:
            updated_html = cleaned_html
        
        # Write the cleaned and updated HTML to index.html
        output_html_path = post_dir / "index.html"
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        if image_mapping:
            logger.info(f"Updated HTML with {len(image_mapping)} local image references")
        else:
            logger.info(f"No images were downloaded for {html_file.name}")
        
        logger.info(f"Cleaned HTML and saved to {output_html_path}")
    
    def process_sample_posts(self, sample_count=3):
        """Process a few sample posts to test the approach"""
        html_files = list(self.posts_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.posts_dir}")
            return
        
        # Take the first few files as samples
        sample_files = html_files[:sample_count]
        logger.info(f"Processing {len(sample_files)} sample posts: {[f.name for f in sample_files]}")
        
        for i, html_file in enumerate(sample_files, 1):
            logger.info(f"Processing sample {i}/{len(sample_files)}: {html_file.name}")
            try:
                self.process_post(html_file)
            except Exception as e:
                logger.error(f"Error processing {html_file.name}: {e}")
                continue
        
        logger.info("Sample processing complete!")
    
    def process_all_posts(self):
        """Process all HTML files in the posts directory"""
        html_files = list(self.posts_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.posts_dir}")
            return
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        for i, html_file in enumerate(html_files, 1):
            # Check if this post has already been processed
            post_dir_name = self.create_post_directory_name(html_file)
            post_dir = self.output_dir / post_dir_name
            index_file = post_dir / "index.html"
            
            if index_file.exists():
                logger.info(f"Post {i}/{len(html_files)} already processed: {html_file.name}")
                continue
            
            logger.info(f"Processing post {i}/{len(html_files)}: {html_file.name}")
            try:
                self.process_post(html_file)
            except Exception as e:
                logger.error(f"Error processing {html_file.name}: {e}")
                continue
        
        logger.info("Processing complete!")

def main():
    """Main function"""
    cleaner = MediumPostCleaner()
    
    # Process a few samples first
    logger.info("=== PROCESSING SAMPLE POSTS ===")
    cleaner.process_sample_posts(sample_count=8)
    
    # Ask user if they want to continue with all posts
    response = input("\nSample processing complete. Process all posts? (y/n): ")
    if response.lower() == 'y':
        logger.info("=== PROCESSING ALL POSTS ===")
        cleaner.process_all_posts()
    else:
        logger.info("Processing stopped after samples.")

if __name__ == "__main__":
    main() 