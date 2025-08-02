#!/usr/bin/env python3
"""
Medium Posts Processor

This script processes all Medium posts by:
1. Creating a directory for each post
2. Copying the HTML file to that directory
3. Downloading remote images and converting them to WebP format
4. Updating image links in the HTML to reference local images
5. Cleaning HTML by removing unwanted attributes and classes
6. Updating internal links between posts

Supports configuration for different Medium authors.
"""

from datetime import datetime, timedelta

import argparse
import hashlib
import io
import logging
import os
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path
from PIL import Image

from config import MediumConfig, load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MediumPostProcessor:
    def __init__(self, config: MediumConfig):
        """
        Initialize the processor with configuration

        Args:
            config: MediumConfig instance containing all settings
        """
        self.config = config
        self.posts_dir = Path(config.posts_dir)
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create a session for downloading images
        self.session = urllib.request.build_opener()
        self.session.addheaders = [('User-Agent', config.user_agent)]

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

            # Add delay based on configuration
            time.sleep(self.config.download_delay)

            # Download the image
            response = self.session.open(url)

            # Handle rate limiting with exponential backoff
            if response.status == 429:
                logger.warning(
                    f"Rate limited (429) for {url}, waiting {self.config.retry_delay} seconds..."
                )
                time.sleep(self.config.retry_delay)
                # Try again
                response = self.session.open(url)
                if response.status == 429:
                    logger.warning(
                        f"Still rate limited after waiting, waiting another {self.config.retry_delay * 2} seconds..."
                    )
                    time.sleep(self.config.retry_delay * 2)
                    response = self.session.open(url)
                    if response.status == 429:
                        logger.error(
                            f"Still rate limited after extended waiting, skipping {url}"
                        )
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
                    background.paste(
                        image, mask=image.split()[-1] if image.mode == 'RGBA' else None
                    )
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

                # Save as WebP with configured quality
                image.save(
                    output_path,
                    'WEBP',
                    quality=self.config.image_quality,
                    optimize=True,
                )
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
        """Extract all internal links to other posts by the same author"""
        soup = BeautifulSoup(html_content, 'html.parser')
        internal_links = []

        # Find all links that point to posts by the same author
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and self.config.is_internal_link(href):
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
            # Remove configured data attributes
            for attr in self.config.remove_data_attributes:
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

        # Remove configured elements
        for element_name in self.config.remove_elements:
            for element in soup.find_all(element_name):
                element.decompose()

        # Clean up CSS classes (remove Medium-specific classes)
        for element in soup.find_all():
            if element.has_attr('class'):
                classes = element.get('class', [])
                # Filter out configured Medium-specific classes
                cleaned_classes = [
                    cls
                    for cls in classes
                    if cls not in self.config.remove_medium_classes
                ]
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
            logger.info(
                f"No images found in {html_file.name}, skipping image processing"
            )
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
            logger.info(
                f"Updated HTML with {len(image_mapping)} local image references"
            )
        else:
            logger.warning(
                f"No images were successfully downloaded for {html_file.name}"
            )

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
                logger.info(
                    f"Post {i}/{len(html_files)} already processed: {html_file.name}"
                )
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

    def convert_relative_date(self, relative_date_text):
        """Convert relative date text to actual date"""
        if not relative_date_text:
            return None

        # Clean the text
        text = relative_date_text.strip().lower()

        # Current date
        now = datetime.now()

        # Common patterns
        patterns = [
            (r'(\d+)\s*days?\s*ago', lambda m: now - timedelta(days=int(m.group(1)))),
            (r'(\d+)\s*weeks?\s*ago', lambda m: now - timedelta(weeks=int(m.group(1)))),
            (
                r'(\d+)\s*months?\s*ago',
                lambda m: now - timedelta(days=int(m.group(1)) * 30),
            ),
            (
                r'(\d+)\s*years?\s*ago',
                lambda m: now - timedelta(days=int(m.group(1)) * 365),
            ),
            (r'yesterday', lambda m: now - timedelta(days=1)),
            (r'today', lambda m: now),
            (r'(\d+)\s*hours?\s*ago', lambda m: now - timedelta(hours=int(m.group(1)))),
            (
                r'(\d+)\s*minutes?\s*ago',
                lambda m: now - timedelta(minutes=int(m.group(1))),
            ),
        ]

        for pattern, converter in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    actual_date = converter(match)
                    return actual_date.strftime('%Y-%m-%d')
                except Exception as e:
                    logger.warning(f"Error converting date '{relative_date_text}': {e}")
                    return None

        return None

    def extract_post_info(self, url):
        """Extract post information from a Medium URL"""
        try:
            logger.info(f"Fetching post: {url}")

            # Add delay to be respectful
            time.sleep(2)

            response = self.session.open(url)

            if response.status != 200:
                logger.error(f"Failed to fetch {url}: HTTP {response.status}")
                return None

            html_content = response.read().decode('utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract title
            title = None
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            # Extract author
            author = None
            author_elem = soup.find('a', {'data-testid': 'authorName'})
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Extract publication date
            date = None
            date_selectors = [
                'time[datetime]',
                '[data-testid="storyReadTime"]',
                '.pw-post-date',
                'time',
            ]

            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    if selector == 'time[datetime]' or selector == 'time':
                        date = date_elem.get('datetime')
                        if date:
                            try:
                                dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                                date = dt.strftime('%Y-%m-%d')
                                break
                            except Exception as e:
                                logger.warning(f"Error parsing datetime: {e}")
                                date = None
                    else:
                        # Look for date in the text or nearby elements
                        parent = date_elem.parent
                        if parent:
                            text = parent.get_text()
                            # Look for ISO date format
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
                            if date_match:
                                date = date_match.group(1)
                                break
                            else:
                                # Look for other date formats
                                date_match = re.search(
                                    r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
                                    text,
                                )
                                if date_match:
                                    try:
                                        dt = datetime.strptime(
                                            date_match.group(1), '%d %b %Y'
                                        )
                                        date = dt.strftime('%Y-%m-%d')
                                        break
                                    except Exception as e:
                                        logger.warning(f"Date parsing failed: {e}")
                                        pass
                                else:
                                    # Try to find relative date patterns
                                    relative_patterns = [
                                        r'(\d+)\s*days?\s*ago',
                                        r'(\d+)\s*weeks?\s*ago',
                                        r'(\d+)\s*months?\s*ago',
                                        r'yesterday',
                                        r'today',
                                    ]

                                    for pattern in relative_patterns:
                                        match = re.search(pattern, text.lower())
                                        if match:
                                            if pattern in ['yesterday', 'today']:
                                                relative_date = match.group(0)
                                            else:
                                                relative_date = (
                                                    f"{match.group(1)} days ago"
                                                )

                                            # Convert relative date to actual date
                                            actual_date = self.convert_relative_date(
                                                relative_date
                                            )
                                            if actual_date:
                                                date = actual_date
                                            break
                    if date:
                        break

            # Extract main content
            content = None
            article_elem = soup.find('article')
            if article_elem:
                # Clean the content
                cleaned_article = self.clean_content(article_elem)
                if cleaned_article:
                    content = str(cleaned_article)

            return {
                'title': title,
                'author': author,
                'date': date,
                'content': content,
                'url': url,
            }

        except Exception as e:
            logger.error(f"Error extracting post info: {e}")
            return None

    def clean_content(self, article_elem):
        """Clean the article content by removing unwanted elements and sections"""
        if not article_elem:
            return None

        # Create a copy to avoid modifying the original
        import copy

        cleaned_article = copy.deepcopy(article_elem)

        # Remove unwanted elements
        for elem in cleaned_article.find_all(['script', 'style', 'iframe']):
            elem.decompose()

        # Remove Medium-specific UI elements
        unwanted_selectors = [
            '[data-testid="headerClapButton"]',
            '[data-testid="headerBookmarkButton"]',
            '[data-testid="headerSocialShareButton"]',
            '[data-testid="audioPlayButton"]',
            '.pw-multi-vote-icon',
            '.pw-multi-vote-count',
            '.pw-responses-count',
            '.speechify-ignore',
            '[role="tooltip"]',
            '[aria-hidden="true"]',
            '.ac.cp',  # Author info container
            '.ac.ij',  # Author photo container
            '.ac.r.it',  # Author name container
            '.ac.r.jc',  # Author info wrapper
            '.je.bm',  # Read time container
            '.ac.cp.ji',  # Action buttons container
            '.ac.r.jy',  # Share buttons container
            '.ac.r.ko',  # Clap button container
            '.ac.r.lq',  # Bookmark container
            '.fd.ls.cn',  # Audio/share container
            '.lt.lu.lv.lw.lx.ly',  # Audio button wrapper
        ]

        for selector in unwanted_selectors:
            for elem in cleaned_article.select(selector):
                elem.decompose()

        # Remove elements with specific classes that contain UI elements
        unwanted_classes = [
            'ac',
            'cp',
            'ji',
            'jj',
            'jk',
            'jl',
            'jm',
            'jn',
            'jo',
            'jp',
            'jq',
            'jr',
            'js',
            'jt',
            'ju',
            'jv',
            'jw',
            'jx',
            'kn',
            'ko',
            'kp',
            'kq',
            'kr',
            'ks',
            'kt',
            'ku',
            'kv',
            'kw',
            'kx',
            'ky',
            'kz',
            'la',
            'lb',
            'lc',
            'ld',
            'le',
            'lf',
            'lg',
            'lh',
            'li',
            'lj',
            'lk',
            'll',
            'lm',
            'ln',
            'lo',
            'lp',
            'lq',
            'lr',
            'ls',
            'lt',
            'lu',
            'lv',
            'lw',
            'lx',
            'ly',
            'lz',
            'ma',
            'mb',
            'mc',
            'md',
            'me',
            'mf',
            'mg',
            'mh',
            'mi',
            'mj',
            'mk',
            'ml',
            'mm',
            'mn',
            'mo',
            'mp',
            'mq',
        ]

        for class_name in unwanted_classes:
            for elem in cleaned_article.find_all(class_=class_name):
                # Only remove if it's not a paragraph or heading
                if elem.name not in [
                    'p',
                    'h1',
                    'h2',
                    'h3',
                    'h4',
                    'h5',
                    'h6',
                    'div',
                    'span',
                ]:
                    elem.decompose()

        # Find the subtitle (h2 element)
        subtitle = cleaned_article.find('h2')
        if subtitle:
            # Find the first figure element after the subtitle
            first_figure = None
            for elem in subtitle.find_next_siblings():
                if elem.name == 'figure':
                    first_figure = elem
                    break

            if first_figure:
                # Remove all elements between subtitle and first figure
                current_elem = subtitle.find_next_sibling()
                while current_elem and current_elem != first_figure:
                    next_elem = current_elem.find_next_sibling()
                    current_elem.decompose()
                    current_elem = next_elem

        return cleaned_article

    def process_single_post_from_url(self, url):
        """Process a single post from a Medium URL"""
        logger.info(f"Processing single post from URL: {url}")

        # Extract post information
        post_info = self.extract_post_info(url)
        if not post_info:
            logger.error("Failed to extract post information")
            return False

        # Create a proper filename from title and date
        title = post_info['title'] or 'untitled'
        safe_title = self.sanitize_filename(title)

        # Add date if available
        if post_info['date']:
            try:
                date_obj = datetime.fromisoformat(
                    post_info['date'].replace('Z', '+00:00')
                )
                date_str = date_obj.strftime('%Y-%m-%d')
                filename = f"{date_str}_{safe_title}.html"
            except:
                filename = f"{safe_title}.html"
        else:
            filename = f"{safe_title}.html"

        # Create a temporary HTML file with proper name
        import tempfile

        temp_dir = tempfile.mkdtemp()
        temp_html_path = os.path.join(temp_dir, filename)

        with open(temp_html_path, 'w', encoding='utf-8') as f:
            # Create HTML content
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post_info['title'] or 'Untitled'}</title>
    <meta name="author" content="{post_info['author'] or 'Unknown'}">
    <meta name="date" content="{post_info['date'] or ''}">
    <meta name="source" content="{post_info['url']}">
</head>
<body>
    {post_info['content'] or '<p>No content available</p>'}
</body>
</html>"""
            f.write(html_content)

        try:
            # Process the temporary HTML file
            temp_html_file = Path(temp_html_path)
            self.process_post(temp_html_file)
            logger.info(f"Successfully processed post: {post_info['title']}")
            return True
        finally:
            # Clean up temporary directory
            import shutil

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

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
                        updated_html, links_updated = self.update_internal_links(
                            cleaned_html, link_mapping
                        )

                        # Write the cleaned and updated HTML back to the file
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(updated_html)

                        if links_updated > 0:
                            logger.info(
                                f"Updated {links_updated} internal links in {html_file.name}"
                            )
                            updated_posts += 1
                            total_links_updated += links_updated
                        else:
                            logger.debug(f"No internal links found in {html_file.name}")

                        logger.info(f"Cleaned HTML and saved to {html_file}")

                    except Exception as e:
                        logger.error(
                            f"Error updating internal links in {html_file}: {e}"
                        )

        logger.info(
            f"Updated internal links in {updated_posts} posts (total: {total_links_updated} links)"
        )


def main():
    """Main function with command line argument support"""
    parser = argparse.ArgumentParser(
        description='Process Medium posts with configurable settings'
    )
    parser.add_argument(
        '--config',
        '-c',
        default='julsimon',
        help='Configuration name (default: julsimon)',
    )
    parser.add_argument(
        '--author',
        '-a',
        help='Medium author username (creates new config if not exists)',
    )
    parser.add_argument(
        '--list-configs', action='store_true', help='List available configurations'
    )
    parser.add_argument(
        '--single-post',
        '-s',
        help='Process a single Medium post URL instead of batch processing',
    )

    args = parser.parse_args()

    if args.list_configs:
        # List available config files
        config_files = [
            f
            for f in os.listdir('.')
            if f.startswith('config_') and f.endswith('.json')
        ]
        if config_files:
            print("Available configurations:")
            for config_file in config_files:
                config_name = config_file.replace('config_', '').replace('.json', '')
                print(f"  - {config_name}")
        else:
            print("No configuration files found. Using default configuration.")
        return

    # Load configuration
    if args.author:
        # Create new config for specified author
        config = MediumConfig()
        config.author_username = args.author
        config.author_display_name = args.author.replace('_', ' ').title()
        config.author_url = f"{config.medium_base_url}/@{config.author_username}"
        config.internal_link_patterns = [
            f"{config.medium_base_url}/@{config.author_username}/",
            f"{config.author_url}/",
        ]
        print(f"Using configuration for author: {config.author_display_name}")
    else:
        # Load existing config
        config = load_config(args.config)
        print(
            f"Using configuration: {args.config} for author: {config.author_display_name}"
        )

    # Create processor and run
    processor = MediumPostProcessor(config)

    if args.single_post:
        # Process a single post from URL
        success = processor.process_single_post_from_url(args.single_post)
        if success:
            print("✅ Single post processed successfully!")
        else:
            print("❌ Failed to process single post")
    else:
        # Process all posts
        processor.process_all_posts()


if __name__ == "__main__":
    main()
