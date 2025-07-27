#!/usr/bin/env python3
"""
AWS Blog Post Downloader CLI Tool

Downloads AWS blog posts from aws-blog-posts.json, extracts main content,
downloads and converts images to WebP, and applies basic styling.
"""

import json
import argparse
import requests
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image
import io
import time
import sys
from datetime import datetime

class AWSBlogDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def load_posts(self, urls_file):
        """Load blog posts from text file with URLs"""
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        
        return [{'url': url} for url in urls]
    
    def extract_title(self, soup):
        """Extract title from HTML soup"""
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]', 
            'title',
            'h1'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    title = element.get('content')
                else:
                    title = element.get_text().strip()
                if title:
                    # Clean title
                    title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove " | AWS Blog" etc
                    return title.strip()
        
        return "Unknown Title"
    
    def extract_date(self, soup, url):
        """Extract date from HTML soup or URL"""
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[property="article:modified_time"]',
            'time[datetime]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    date_str = element.get('content')
                else:
                    date_str = element.get('datetime') or element.get_text()
                
                if date_str:
                    try:
                        if 'T' in date_str:
                            parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue
        
        # Fallback: extract date from URL
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"
        
        return "2020-01-01"  # fallback

    def create_folder_name(self, post):
        """Create folder name from date and title"""
        date = post['date']
        title = post['title']
        
        # Clean title: remove special chars, convert to lowercase, replace spaces with dashes
        clean_title = re.sub(r'[^\w\s-]', '', title)
        clean_title = re.sub(r'\s+', '-', clean_title.strip().lower())
        
        return f"{date}_{clean_title}"

    def extract_main_content(self, soup):
        """Extract main blog post content, filtering out navigation and sidebars"""
        # Try different selectors for AWS blog main content
        selectors = [
            'section.blog-post-content',
            '.blog-post-content',
            'main article',
            'article.post',
            '[role="main"] article',
            '.main-content article',
            'div.blog-post',
            'div[data-module="BlogPost"]'
        ]
        
        main_content = None
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            # Fallback: look for content with typical blog indicators
            content_divs = soup.find_all('div', class_=re.compile(r'content|post|article|main', re.I))
            if content_divs:
                main_content = max(content_divs, key=lambda x: len(x.get_text()))
        
        if not main_content:
            # Last resort: use body content
            main_content = soup.find('body')
        
        return main_content

    def download_image(self, img_url, post_folder, image_number):
        """Download image and convert to WebP with sequential naming"""
        try:
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            # Generate sequential filename
            webp_name = f"image{image_number:02d}.webp"
            webp_path = post_folder / webp_name
            
            # Convert to WebP
            image = Image.open(io.BytesIO(response.content))
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            image.save(webp_path, 'WebP', quality=85, optimize=True)
            print(f"  Downloaded and converted: {webp_name}")
            
            return webp_name
            
        except Exception as e:
            print(f"  Failed to download image {img_url}: {e}")
            return None

    def remove_polly_content(self, soup):
        """Remove Amazon Polly audio content and branding"""
        # Remove the entire Amazon Polly audio table
        polly_table = soup.find('table', id='amazon-polly-audio-table')
        if polly_table:
            polly_table.decompose()
        
        # Also remove any standalone Polly elements
        polly_elements = soup.find_all(attrs={'id': lambda x: x and 'polly' in x.lower()})
        for element in polly_elements:
            element.decompose()
            
        # Remove audio elements
        audio_elements = soup.find_all('audio')
        for element in audio_elements:
            element.decompose()

    def process_images(self, soup, base_url, post_folder):
        """Download images and update their URLs in the HTML"""
        images = soup.find_all('img')
        image_counter = 1
        
        for img in images:
            src = img.get('src')
            if not src:
                continue
            
            # Skip Polly branding images
            if 'polly' in src.lower() or 'voiced_by_amazon' in src.lower():
                img.decompose()
                continue
            
            # Make URL absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif not src.startswith('http'):
                src = urljoin(base_url, src)
            
            # Download and convert image
            local_path = self.download_image(src, post_folder, image_counter)
            if local_path:
                img['src'] = local_path
                # Remove srcset if present
                if img.get('srcset'):
                    del img['srcset']
                
                # Handle parent link that wraps the image
                parent = img.parent
                if parent and parent.name == 'a' and parent.get('href'):
                    # If the link points to the same image, update it to local path or remove it
                    href = parent.get('href')
                    if href and (href == src or href.endswith(src.split('/')[-1])):
                        # Either update to local path or remove the link entirely
                        parent.replace_with(img)  # Remove the wrapping link
                
                # Increment counter only for successfully downloaded images
                image_counter += 1

    def apply_basic_styling(self, soup):
        """Apply basic CSS styling to the content"""
        style = """
        <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 0.5em;
        }
        h1 { font-size: 2.5em; }
        h2 { font-size: 2em; }
        h3 { font-size: 1.5em; }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1em 0;
        }
        /* Image alignment classes for text wraparound */
        img.alignleft {
            float: left;
            margin: 0.5em 1.5em 1em 0;
        }
        img.alignright {
            float: right;
            margin: 0.5em 0 1em 1.5em;
        }
        img.aligncenter {
            display: block;
            margin: 1em auto;
            float: none;
        }
        img.alignnone {
            float: none;
            margin: 1em 0;
        }
        /* Clear floats after images */
        .wp-block-image::after,
        p:has(img.alignleft)::after,
        p:has(img.alignright)::after {
            content: "";
            display: table;
            clear: both;
        }
        pre {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 1em;
            overflow-x: auto;
        }
        code {
            background: #f8f9fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }
        blockquote {
            border-left: 4px solid #3498db;
            margin: 1em 0;
            padding-left: 1em;
            font-style: italic;
            color: #7f8c8d;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        p {
            margin-bottom: 1em;
        }
        </style>
        """
        
        # Add style to head or create head if it doesn't exist
        head = soup.find('head')
        if not head:
            head = soup.new_tag('head')
            soup.insert(0, head)
        
        head.append(BeautifulSoup(style, 'html.parser'))

    def perform_sanity_checks(self, post_folder, post):
        """Perform sanity checks on downloaded content"""
        print("  Running sanity checks...")
        issues = []
        
        # Check HTML file exists and has content
        html_file = post_folder / "index.html"
        if not html_file.exists():
            issues.append("HTML file missing")
        else:
            try:
                html_content = html_file.read_text(encoding='utf-8')
                if len(html_content) < 1000:  # Minimum reasonable size
                    issues.append(f"HTML file too small ({len(html_content)} chars)")
                
                # Check for essential content
                if post['title'] not in html_content:
                    issues.append("Post title not found in HTML")
                if "Originally published at" not in html_content:
                    issues.append("Source attribution missing")
                
                # Count image references in HTML
                img_refs = html_content.count('src="image')
                if img_refs == 0:
                    issues.append("No image references found in HTML")
                
                # Check for broken image references
                soup = BeautifulSoup(html_content, 'html.parser')
                images = soup.find_all('img')
                for img in images:
                    src = img.get('src')
                    if src and src.startswith('image') and src.endswith('.webp'):
                        img_path = post_folder / src
                        if not img_path.exists():
                            issues.append(f"Referenced image missing: {src}")
                
            except Exception as e:
                issues.append(f"Error reading HTML: {e}")
        
        # Check metadata file
        metadata_file = post_folder / "metadata.json"
        if not metadata_file.exists():
            issues.append("Metadata file missing")
        else:
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    required_fields = ['title', 'url', 'date', 'downloaded_at']
                    for field in required_fields:
                        if field not in metadata:
                            issues.append(f"Metadata missing field: {field}")
            except Exception as e:
                issues.append(f"Error reading metadata: {e}")
        
        # Check downloaded images
        webp_files = list(post_folder.glob("image*.webp"))
        if not webp_files:
            issues.append("No WebP images found")
        else:
            for img_file in webp_files:
                # Check file size
                if img_file.stat().st_size < 100:  # Very small files likely corrupted
                    issues.append(f"Image too small: {img_file.name}")
                
                # Verify it's a valid WebP
                try:
                    with Image.open(img_file) as img:
                        if img.format != 'WEBP':
                            issues.append(f"Invalid WebP format: {img_file.name}")
                except Exception as e:
                    issues.append(f"Corrupted image {img_file.name}: {e}")
        
        # Check image sequence is complete
        expected_images = len(webp_files)
        if expected_images > 0:
            for i in range(1, expected_images + 1):
                expected_name = f"image{i:02d}.webp"
                if not (post_folder / expected_name).exists():
                    issues.append(f"Missing sequential image: {expected_name}")
        
        # Report results
        if issues:
            print(f"  ⚠️  {len(issues)} issue(s) found:")
            for issue in issues[:5]:  # Limit to first 5 issues
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    ... and {len(issues) - 5} more issues")
            return False
        else:
            html_size = html_file.stat().st_size if html_file.exists() else 0
            print(f"  ✓ All checks passed ({len(webp_files)} images, {html_size} bytes HTML)")
            return True

    def download_post(self, post):
        """Download a single blog post"""
        print(f"\nDownloading: {post['url']}")
        
        try:
            # Download HTML
            response = self.session.get(post['url'], timeout=30)
            
            # Check for 404 or other errors
            if response.status_code == 404:
                print("⚠️  URL returns 404 - skipping")
                return
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata from HTML
            title = self.extract_title(soup)
            date = self.extract_date(soup, post['url'])
            
            # Update post object with extracted metadata
            post['title'] = title
            post['date'] = date
            
            print(f"Title: {title}")
            print(f"Date: {date}")
            
            # Create post folder
            folder_name = self.create_folder_name(post)
            post_folder = self.output_dir / folder_name
            post_folder.mkdir(exist_ok=True)
            
            print(f"Folder: {post_folder}")
            
            # Extract main content
            main_content = self.extract_main_content(soup)
            
            # Create new minimal HTML document with just the main content
            new_soup = BeautifulSoup('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>', 'html.parser')
            
            # Add title
            title_tag = new_soup.new_tag('h1')
            title_tag.string = post['title']
            new_soup.body.append(title_tag)
            
            # Add date
            date_tag = new_soup.new_tag('p')
            date_tag.string = f"Published: {post['date']}"
            date_tag['style'] = "color: #666; font-style: italic; margin-bottom: 1em;"
            new_soup.body.append(date_tag)
            
            # Add original source link
            source_tag = new_soup.new_tag('p')
            source_tag['style'] = "color: #666; font-style: italic; margin-bottom: 2em;"
            source_text = new_soup.new_string("Originally published at ")
            source_link = new_soup.new_tag('a', href=post['url'])
            source_link.string = post['url']
            source_tag.append(source_text)
            source_tag.append(source_link)
            new_soup.body.append(source_tag)
            
            # Add main content
            if main_content:
                # Copy content to new document
                content_elements = list(main_content.children)
                for element in content_elements:
                    if hasattr(element, 'name'):
                        new_soup.body.append(element.extract())
            
            # Remove Amazon Polly audio content
            self.remove_polly_content(new_soup)
            
            # Process images
            print("Processing images...")
            self.process_images(new_soup, post['url'], post_folder)
            
            # Apply styling
            self.apply_basic_styling(new_soup)
            
            # Save HTML
            html_file = post_folder / "index.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(new_soup.prettify()))
            
            # Save metadata
            metadata = {
                'title': post['title'],
                'url': post['url'],
                'date': post['date'],
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            metadata_file = post_folder / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Successfully downloaded to {html_file}")
            
            # Perform sanity checks
            checks_passed = self.perform_sanity_checks(post_folder, post)
            if not checks_passed:
                print(f"⚠️  Post downloaded but failed sanity checks")
            
        except Exception as e:
            title = post.get('title', post['url'])
            print(f"✗ Failed to download {title}: {e}")
            
        # Add delay to be respectful
        time.sleep(2)

def main():
    parser = argparse.ArgumentParser(description='Download AWS blog posts')
    parser.add_argument('--urls', type=str, default='aws-blog-urls.txt',
                       help='Path to text file with blog post URLs (one per line)')
    parser.add_argument('--output', type=str, default='downloads',
                       help='Output directory for downloaded posts')
    parser.add_argument('--limit', type=int, default=3,
                       help='Number of posts to download (default: 3)')
    parser.add_argument('--start', type=int, default=0,
                       help='Starting index (default: 0)')
    
    args = parser.parse_args()
    
    downloader = AWSBlogDownloader(args.output)
    
    try:
        posts = downloader.load_posts(args.urls)
        print(f"Loaded {len(posts)} posts from {args.urls}")
        
        # Limit posts for testing
        posts_to_download = posts[args.start:args.start + args.limit]
        print(f"Downloading {len(posts_to_download)} posts...")
        
        successful_downloads = 0
        for post in posts_to_download:
            try:
                downloader.download_post(post)
                successful_downloads += 1
            except Exception as e:
                print(f"✗ Failed to download {post['title']}: {e}")
        
        print(f"\n✓ Completed! Successfully downloaded {successful_downloads}/{len(posts_to_download)} posts to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 