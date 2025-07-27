#!/usr/bin/env python3
"""
Medium Posts Processor

This script processes all Medium posts by:
1. Creating a directory for each post
2. Copying the HTML file to that directory
3. Downloading remote images and converting them to WebP format
4. Updating image links in the HTML to reference local images
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

class MediumPostProcessor:
    def __init__(self, posts_dir="posts", output_dir="processed_posts"):
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
        """Download an image from URL and save it with aggressive throttling"""
        try:
            logger.info(f"Downloading: {url}")
            
            # Add a much longer delay to be very respectful to servers and avoid rate limiting
            time.sleep(3.0)  # Increased to 3 seconds between downloads
            
            # Download the image
            response = self.session.open(url)
            
            # Handle rate limiting with exponential backoff
            if response.status == 429:
                logger.warning(f"Rate limited (429) for {url}, waiting 60 seconds...")
                time.sleep(60)  # Wait 60 seconds on rate limit
                # Try again once
                response = self.session.open(url)
                if response.status == 429:
                    logger.warning(f"Still rate limited after waiting, waiting another 120 seconds...")
                    time.sleep(120)  # Wait another 2 minutes
                    response = self.session.open(url)
                    if response.status == 429:
                        logger.error(f"Still rate limited after extended waiting, skipping {url}")
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
                # Handle relative URLs (though unlikely in Medium exports)
                if src.startswith('http'):
                    image_urls.append(src)
                elif src.startswith('//'):
                    image_urls.append('https:' + src)
        
        return list(set(image_urls))  # Remove duplicates
    
    def generate_image_filename(self, image_number):
        """Generate a filename for the downloaded image using sequential naming"""
        # Use sequential naming like AWS blog downloader: image01.webp, image02.webp, etc.
        return f"image{image_number:02d}.webp"
    
    def extract_internal_links(self, html_content):
        """Extract all internal links to other Julien Simon Medium posts"""
        soup = BeautifulSoup(html_content, 'html.parser')
        internal_links = []
        
        # Find all links that point to Julien Simon's Medium posts
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and 'medium.com/@julsimon/' in href:
                internal_links.append(href)
        
        return list(set(internal_links))  # Remove duplicates
    
    def create_link_mapping(self):
        """Create a mapping from Medium URLs to local file paths"""
        link_mapping = {}
        
        # Scan all processed posts to build the mapping
        for post_dir in self.output_dir.iterdir():
            if post_dir.is_dir():
                # Find the index.html file in this directory
                html_file = post_dir / "index.html"
                if html_file.exists():
                    
                    # Read the HTML to extract the canonical URL
                    with open(html_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    soup = BeautifulSoup(content, 'html.parser')
                    canonical_link = soup.find('a', class_='p-canonical')
                    
                    if canonical_link and canonical_link.get('href'):
                        medium_url = canonical_link.get('href')
                        # Create relative path to the local HTML file (now index.html)
                        relative_path = f"{post_dir.name}/index.html"
                        link_mapping[medium_url] = relative_path
                        logger.debug(f"Mapped {medium_url} -> {relative_path}")
        
        return link_mapping
    
    def update_internal_links(self, html_content, link_mapping):
        """Update HTML content to reference local files instead of Medium URLs"""
        soup = BeautifulSoup(html_content, 'html.parser')
        updated_count = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href in link_mapping:
                link['href'] = link_mapping[href]
                logger.info(f"Updated internal link: {href} -> {link_mapping[href]}")
                updated_count += 1
        
        return str(soup), updated_count
    
    def clean_html(self, html_content):
        """Clean up unwanted HTML attributes and tags"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted data attributes from images
        for img in soup.find_all('img'):
            # Remove Medium-specific data attributes
            for attr in ['data-image-id', 'data-width', 'data-height', 'data-is-featured']:
                if img.has_attr(attr):
                    del img[attr]
        
        # Remove unwanted data attributes from links
        for link in soup.find_all('a'):
            # Remove duplicate data-href attributes
            if link.has_attr('data-href'):
                del link['data-href']
            # Remove Medium-specific action attributes
            for attr in ['data-action', 'data-action-observe-only']:
                if link.has_attr(attr):
                    del link[attr]
            # Remove rel="noopener" attributes
            if link.has_attr('rel') and link['rel'] == ['noopener']:
                del link['rel']
        
        # Remove unwanted attributes from other elements
        for element in soup.find_all():
            # Remove data-paragraph-count attributes
            if element.has_attr('data-paragraph-count'):
                del element['data-paragraph-count']
            # Remove name attributes (often redundant with id)
            if element.has_attr('name'):
                del element['name']
        
        # Remove Medium-specific elements that are not needed
        # Remove iframe elements (embeds, etc.)
        for iframe in soup.find_all('iframe'):
            iframe.decompose()
        
        # Remove script elements
        for script in soup.find_all('script'):
            script.decompose()
        
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
        """Create a clean directory name from the HTML filename, removing UUID-like parts"""
        # Extract the base name without extension
        base_name = html_file.stem
        
        # Remove UUID-like parts (typically at the end, 8-12 characters)
        # Pattern: date_title-uuid
        # We want to keep: date_title
        if '-' in base_name:
            # Split by '-' and take all parts except the last one if it looks like a UUID
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
        
        # Create post directory (even if no images)
        post_dir_name = self.create_post_directory_name(html_file)
        post_dir = self.output_dir / post_dir_name
        post_dir.mkdir(exist_ok=True)
        
        # Copy the HTML file and rename to index.html
        new_html_path = post_dir / "index.html"
        shutil.copy2(html_file, new_html_path)
        logger.info(f"Copied HTML to: {new_html_path}")
        
        if not image_urls:
            logger.info(f"No images found in {html_file.name}, skipping image processing")
            return
        
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
        
        # Clean up the HTML content
        cleaned_html = self.clean_html(html_content)
        
        # Update the HTML with local image references
        if image_mapping:
            updated_html = self.update_html_images(cleaned_html, image_mapping)
        else:
            updated_html = cleaned_html
        
        # Write the cleaned and updated HTML back to the file
        with open(new_html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        if image_mapping:
            logger.info(f"Updated HTML with {len(image_mapping)} local image references")
        else:
            logger.warning(f"No images were successfully downloaded for {html_file.name}")
        
        logger.info(f"Cleaned HTML and saved to {new_html_path}")
    
    def process_all_posts(self):
        """Process all HTML files in the posts directory using a two-pass approach"""
        html_files = list(self.posts_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.posts_dir}")
            return
        
        logger.info(f"Found {len(html_files)} HTML files to process")
        
        # First pass: Process all posts to create directories and download images
        logger.info("=== FIRST PASS: Processing posts and downloading images ===")
        for i, html_file in enumerate(html_files, 1):
            # Check if this post has already been processed (has index.html)
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
        
        # Second pass: Update internal links between posts
        logger.info("=== SECOND PASS: Updating internal links ===")
        self.update_all_internal_links()
        
        logger.info("Processing complete!")
    
    def update_all_internal_links(self):
        """Update all internal links in processed posts"""
        # Create mapping from Medium URLs to local file paths
        logger.info("Creating link mapping...")
        link_mapping = self.create_link_mapping()
        logger.info(f"Created mapping for {len(link_mapping)} posts")
        
        # Update internal links in all processed posts
        updated_posts = 0
        total_links_updated = 0
        
        for post_dir in self.output_dir.iterdir():
            if post_dir.is_dir():
                html_file = post_dir / "index.html"
                if html_file.exists():
                    logger.info(f"Updating internal links in: {html_file}")
                    
                    try:
                        # Read the HTML file
                        with open(html_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        # Clean and update internal links
                        cleaned_html = self.clean_html(html_content)
                        updated_html, links_updated = self.update_internal_links(cleaned_html, link_mapping)
                        
                        # Write the cleaned and updated HTML back to the file
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(updated_html)
                        
                        if links_updated > 0:
                            logger.info(f"Updated {links_updated} internal links in {html_file.name}")
                            updated_posts += 1
                            total_links_updated += links_updated
                        else:
                            logger.debug(f"No internal links found in {html_file.name}")
                        
                        logger.info(f"Cleaned HTML and saved to {html_file}")
                            
                    except Exception as e:
                        logger.error(f"Error updating internal links in {html_file}: {e}")
        
        logger.info(f"Updated internal links in {updated_posts} posts (total: {total_links_updated} links)")

def main():
    """Main function"""
    processor = MediumPostProcessor()
    processor.process_all_posts()

if __name__ == "__main__":
    main() 