#!/usr/bin/env python3
"""
Hugging Face Blog Post Downloader CLI Tool

Downloads Hugging Face blog posts from huggingface-blog-urls.txt, extracts main content,
downloads and converts images to WebP, and applies basic styling.
"""

from datetime import datetime

import argparse
import io
import json
import re
import requests
import sys
import time
from bs4 import BeautifulSoup
from pathlib import Path
from PIL import Image
from urllib.parse import urljoin, urlparse


class HuggingFaceBlogDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

    def load_posts(self, urls_file):
        """Load blog posts from text file with URLs"""
        with open(urls_file, 'r') as f:
            urls = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith('#')
            ]

        return [{'url': url} for url in urls]

    def extract_title(self, soup):
        """Extract title from HTML soup"""
        title_selectors = [
            'meta[property="og:title"]',
            'meta[name="twitter:title"]',
            'title',
            'h1',
            '.prose h1',
            'article h1',
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    title = element.get('content')
                else:
                    title = element.get_text().strip()
                if title:
                    # Clean title - remove " | Hugging Face" etc
                    title = re.sub(r'\s*\|\s*.*$', '', title)
                    title = re.sub(r'\s*-\s*Hugging Face.*$', '', title)
                    return title.strip()

        return "Unknown Title"

    def extract_date(self, soup, url):
        """Extract date from HTML soup or URL"""
        # First try to extract the visible publication date from the page
        try:
            # Look for the visible publication date in the HTML
            # Pattern: "Published March 20, 2024" or similar
            date_pattern = r'Published\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})'
            date_match = re.search(date_pattern, str(soup))
            if date_match:
                date_str = date_match.group(1)
                # Parse the date (e.g., "March 20, 2024")
                parsed_date = datetime.strptime(date_str, '%B %d, %Y')
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass

        # Fallback: try to extract from JSON data embedded in the page
        try:
            # Look for publishedAt in JSON data
            json_pattern = r'"publishedAt":"([^"]+)"'
            json_match = re.search(json_pattern, str(soup))
            if json_match:
                date_str = json_match.group(1)
                if 'T' in date_str:
                    parsed_date = datetime.fromisoformat(
                        date_str.replace('Z', '+00:00')
                    )
                    return parsed_date.strftime('%Y-%m-%d')
        except:
            pass

        # Try standard meta tags
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[property="article:modified_time"]',
            'time[datetime]',
            '.prose time',
            'article time',
            '[data-testid="article-date"]',
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
                            parsed_date = datetime.fromisoformat(
                                date_str.replace('Z', '+00:00')
                            )
                        else:
                            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        continue

        # Fallback: extract date from URL if it contains date patterns
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"

        # Another fallback: look for date in URL path
        date_match = re.search(r'/(\d{4})-(\d{2})-(\d{2})/', url)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"

        return "2021-01-01"  # fallback

    def extract_authors(self, soup):
        """Extract author names from HTML soup"""
        authors = []

        # Try to extract from JSON data embedded in the page
        try:
            # Look for fullname in JSON data
            json_pattern = r'"fullname":"([^"]+)"'
            json_matches = re.findall(json_pattern, str(soup))

            for author in json_matches:
                # Clean up the author name
                clean_author = author.strip()

                # Remove unwanted parts like [open/acc]
                clean_author = re.sub(r'\s*\[[^\]]+\]\s*', '', clean_author)

                # Filter out unwanted strings and organizations
                if (
                    clean_author
                    and clean_author not in authors
                    and len(clean_author) > 1
                    and clean_author.lower()
                    not in [
                        'update on github',
                        'upvote',
                        'guest',
                        'avatar',
                        'icon',
                        'logo',
                        'favicon',
                        'open/acc',
                        'intel',
                        'huggingface',
                        'microsoft',
                        'google',
                        'amazon',
                        'meta',
                        'openai',
                    ]
                    and not any(
                        username in clean_author.lower()
                        for username in [
                            'juliensimon',
                            'echarlaix',
                            'ofirzaf',
                            'imargulis',
                            'guybd',
                            'moshew',
                            'tonic',
                            'lunarflu',
                            'jiqing',
                            'katarinayuan',
                            'sywangyi',
                            'matrixyao',
                            'chrisallenming',
                            'kding1',
                        ]
                    )
                ):
                    authors.append(clean_author)
        except:
            pass

        return authors

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
        # Try different selectors for Hugging Face blog main content
        selectors = [
            '.prose',
            'article .prose',
            'main article',
            'article.post',
            '[role="main"] article',
            '.main-content article',
            'div.article-content',
            'div[data-testid="article-content"]',
            '.markdown',
            'article .markdown',
        ]

        main_content = None
        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            # Fallback: look for content with typical blog indicators
            content_divs = soup.find_all(
                'div', class_=re.compile(r'content|post|article|main|prose', re.I)
            )
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

    def remove_huggingface_specific_content(self, soup):
        """Remove Hugging Face specific content that's not part of the main article"""
        # Remove navigation elements
        nav_selectors = [
            'nav',
            '.navbar',
            '.header',
            '.sidebar',
            '.footer',
            '[data-testid="navigation"]',
            '[data-testid="sidebar"]',
        ]

        for selector in nav_selectors:
            elements = soup.find_all(selector)
            for element in elements:
                element.decompose()

        # Remove social sharing buttons
        social_selectors = [
            '.social-share',
            '.share-buttons',
            '[data-testid="social-share"]',
            '.twitter-share',
            '.linkedin-share',
        ]

        for selector in social_selectors:
            elements = soup.find_all(selector)
            for element in elements:
                element.decompose()

        # Remove related articles sections
        related_selectors = [
            '.related-articles',
            '.recommended-posts',
            '[data-testid="related-articles"]',
        ]

        for selector in related_selectors:
            elements = soup.find_all(selector)
            for element in elements:
                element.decompose()

    def remove_content_between_title_and_first_image(self, soup):
        """Remove navigation and metadata content before the first image"""
        # Remove all unwanted elements that appear after the title
        unwanted_selectors = [
            # GitHub update button
            'a[href*="github.com/huggingface/blog"]',
            '.btn[href*="github.com"]',
            # Upvote section
            '[data-target="UpvoteControl"]',
            '.flex.flex-wrap.items-center.gap-2\\.5',
            # Avatar and user information
            'ul.flex.items-center.flex-row',
            'li[title]',
            'a[title]',
            'img[alt=""]',
            # Guest labels
            'button.btn.bg-linear-to-br',
            'span:-soup-contains("guest")',
            # Publication date elements
            'div.mb-6.flex.items-center.gap-x-4',
            'span.text-sm.sm\\:text-base',
            # Author information sections
            '[data-target="BlogAuthorsByline"]',
            '.not-prose .mb-12',
            '.flex.items-center.font-sans',
            # Any elements containing specific text
            '*:-soup-contains("Update on GitHub")',
            '*:-soup-contains("Upvote")',
            '*:-soup-contains("guest")',
            '*:-soup-contains("avatar")',
            '*:-soup-contains("juliensimon")',
            '*:-soup-contains("echarlaix")',
            '*:-soup-contains("ofirzaf")',
            '*:-soup-contains("imargulis")',
            '*:-soup-contains("guybd")',
            '*:-soup-contains("moshew")',
            # Navigation elements
            '.mb-4',
            '[data-testid="navigation"]',
            '.navigation',
            '.breadcrumb',
            '.back-link',
        ]

        for selector in unwanted_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

        # Remove elements by text content
        for element in soup.find_all(string=True):
            if element.parent:
                text = element.strip().lower()
                if any(
                    keyword in text
                    for keyword in [
                        'update on github',
                        'upvote',
                        'guest',
                        'avatar',
                        'juliensimon',
                        'echarlaix',
                        'ofirzaf',
                        'imargulis',
                        'guybd',
                        'moshew',
                    ]
                ):
                    # Remove the parent element if it's a small container
                    parent = element.parent
                    if (
                        parent.name in ['span', 'a', 'button', 'div']
                        and len(parent.get_text().strip()) < 100
                    ):
                        parent.decompose()

        # Remove duplicate titles and metadata that come before the first image
        elements_to_remove = []
        first_image = soup.find('img')
        current = soup.find()

        while current and current != first_image:
            if hasattr(current, 'name') and current.name:
                # Remove navigation-like elements
                if current.name in ['div', 'nav', 'header'] and (
                    'back' in current.get_text().lower()
                    or 'navigation' in current.get_text().lower()
                    or 'breadcrumb' in current.get_text().lower()
                ):
                    elements_to_remove.append(current)
                # Remove duplicate titles
                elif current.name == 'h1' and current != soup.find('h1'):
                    elements_to_remove.append(current)
            current = current.next_sibling

        # Remove the elements
        for element in elements_to_remove:
            element.decompose()

    def remove_title_icons(self, soup):
        """Remove icons and links from titles"""
        # Remove header links and icons from all headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # Remove header link elements
            header_links = heading.find_all('a', class_='block')
            for link in header_links:
                link.decompose()

            # Remove SVG icons
            svg_elements = heading.find_all('svg')
            for svg in svg_elements:
                svg.decompose()

            # Remove span elements with header-link class
            header_spans = heading.find_all('span', class_='header-link')
            for span in header_spans:
                span.decompose()

            # Remove any remaining anchor tags that might be icons
            icon_links = heading.find_all('a', href=lambda x: x and x.startswith('#'))
            for link in icon_links:
                link.decompose()

            # Remove complex div structures that contain buttons and icons
            # These are often siblings or parents of headings
            complex_divs = heading.find_all('div', class_='absolute')
            for div in complex_divs:
                div.decompose()

            # Remove button elements that might be icons
            buttons = heading.find_all('button')
            for button in buttons:
                button.decompose()

            # Remove peer spans that contain interactive elements
            peer_spans = heading.find_all('span', class_='peer')
            for span in peer_spans:
                span.decompose()

    def remove_duplicate_titles(self, soup):
        """Remove duplicate h1 titles from the content"""
        # Find all h1 elements
        h1_elements = soup.find_all('h1')
        if len(h1_elements) <= 1:
            return  # No duplicates to remove

        # Keep the first h1 (our main title) and remove any subsequent h1s with the same text
        main_title = h1_elements[0].get_text().strip()

        for h1 in h1_elements[1:]:
            if h1.get_text().strip() == main_title:
                h1.decompose()

    def remove_complex_structures(self, soup):
        """Remove complex interactive structures from all elements"""
        # Remove complex div structures that contain buttons and icons
        complex_divs = soup.find_all('div', class_='absolute')
        for div in complex_divs:
            div.decompose()

        # Remove button elements that might be icons
        buttons = soup.find_all('button')
        for button in buttons:
            button.decompose()

        # Remove peer spans that contain interactive elements
        peer_spans = soup.find_all('span', class_='peer')
        for span in peer_spans:
            span.decompose()

        # Remove SVG elements
        svg_elements = soup.find_all('svg')
        for svg in svg_elements:
            svg.decompose()

        # Remove avatar images and user-related content
        avatar_selectors = [
            'img[src*="avatar"]',
            'img[src*="cdn-avatars"]',
            'img[alt*="avatar"]',
            'img[alt*="Avatar"]',
            'img[alt*="profile"]',
            'img[alt*="Profile"]',
        ]
        for selector in avatar_selectors:
            avatars = soup.select(selector)
            for avatar in avatars:
                avatar.decompose()

        # Remove user-related divs and spans
        user_selectors = [
            'div[class*="user"]',
            'span[class*="user"]',
            'div[class*="profile"]',
            'span[class*="profile"]',
            'div[class*="avatar"]',
            'span[class*="avatar"]',
        ]
        for selector in user_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

        # Remove empty divs and spans
        empty_elements = soup.find_all(['div', 'span'])
        for element in empty_elements:
            if not element.get_text().strip() and not element.find_all(
                ['img', 'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
            ):
                element.decompose()

        # Remove SVELTE_HYDRATER elements (they're usually empty containers)
        svelte_elements = soup.find_all('div', class_='SVELTE_HYDRATER')
        for element in svelte_elements:
            if not element.get_text().strip():
                element.decompose()

        # Remove navigation and breadcrumb elements
        nav_selectors = [
            'nav',
            '.navigation',
            '.breadcrumb',
            '.breadcrumbs',
            '[role="navigation"]',
            '[aria-label*="navigation"]',
            '[aria-label*="breadcrumb"]',
        ]
        for selector in nav_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

        # Remove social sharing elements
        social_selectors = [
            '.social-share',
            '.share-buttons',
            '.social-media',
            '[class*="share"]',
            '[class*="social"]',
        ]
        for selector in social_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

        # Remove comment sections and discussion elements
        comment_selectors = [
            '.comments',
            '.comment',
            '.discussion',
            '[class*="comment"]',
            '[class*="discussion"]',
            '[id*="comment"]',
            '[id*="discussion"]',
        ]
        for selector in comment_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

        # Remove related articles sections
        related_selectors = [
            '.related-articles',
            '.recommended-posts',
            '.similar-posts',
            '[class*="related"]',
            '[class*="recommended"]',
            '[class*="similar"]',
        ]
        for selector in related_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

    def process_images(self, soup, base_url, post_folder):
        """Download images and update their URLs in the HTML"""
        images = soup.find_all('img')
        image_counter = 1

        for img in images:
            src = img.get('src')
            if not src:
                continue

            # Skip small icons and avatars
            if any(
                skip in src.lower() for skip in ['avatar', 'icon', 'logo', 'favicon']
            ):
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
        /* Hugging Face specific styling */
        .prose {
            max-width: none;
        }
        .prose pre {
            background: #1e293b;
            color: #e2e8f0;
        }
        .prose code {
            background: #f1f5f9;
            color: #dc2626;
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
            print(
                f"  ✓ All checks passed ({len(webp_files)} images, {html_size} bytes HTML)"
            )
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
            authors = self.extract_authors(soup)

            # Update post object with extracted metadata
            post['title'] = title
            post['date'] = date
            post['authors'] = authors

            print(f"Title: {title}")
            print(f"Date: {date}")
            if authors:
                print(f"Authors: {', '.join(authors)}")

            # Create post folder
            folder_name = self.create_folder_name(post)
            post_folder = self.output_dir / folder_name
            post_folder.mkdir(exist_ok=True)

            print(f"Folder: {post_folder}")

            # Extract main content
            main_content = self.extract_main_content(soup)

            # Create new minimal HTML document with just the main content
            new_soup = BeautifulSoup(
                '<!DOCTYPE html><html><head><meta charset="utf-8"></head><body></body></html>',
                'html.parser',
            )

            # Add title
            title_tag = new_soup.new_tag('h1')
            title_tag.string = post['title']
            new_soup.body.append(title_tag)

            # Add date
            date_tag = new_soup.new_tag('p')
            date_tag.string = f"Published: {post['date']}"
            date_tag['style'] = "color: #666; font-style: italic; margin-bottom: 1em;"
            new_soup.body.append(date_tag)

            # Add authors if available
            if post.get('authors'):
                authors_tag = new_soup.new_tag('p')
                authors_tag.string = f"Authors: {', '.join(post['authors'])}"
                authors_tag[
                    'style'
                ] = "color: #666; font-style: italic; margin-bottom: 1em;"
                new_soup.body.append(authors_tag)

            # Add original source link
            source_tag = new_soup.new_tag('p')
            source_tag['style'] = "color: #666; font-style: italic; margin-bottom: 2em;"
            source_text = new_soup.new_string("Originally published at ")
            source_link = new_soup.new_tag('a', href=post['url'])
            source_link.string = post['url']
            source_tag.append(source_text)
            source_tag.append(source_link)
            new_soup.body.append(source_tag)

            # Remove content between original title and first image from main_content
            self.remove_content_between_title_and_first_image(main_content)

            # Add main content
            if main_content:
                # Copy content to new document
                content_elements = list(main_content.children)
                for element in content_elements:
                    if hasattr(element, 'name'):
                        new_soup.body.append(element.extract())

            # Remove Hugging Face specific content
            self.remove_huggingface_specific_content(new_soup)

            # Remove icons from titles
            self.remove_title_icons(new_soup)

            # Remove duplicate titles
            self.remove_duplicate_titles(new_soup)

            # Remove complex interactive structures from all elements
            self.remove_complex_structures(new_soup)

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
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            }

            # Add authors to metadata if available
            if post.get('authors'):
                metadata['authors'] = post['authors']

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
    parser = argparse.ArgumentParser(description='Download Hugging Face blog posts')
    parser.add_argument(
        '--urls',
        type=str,
        default='huggingface-blog-urls.txt',
        help='Path to text file with blog post URLs (one per line)',
    )
    parser.add_argument(
        '--output',
        type=str,
        default='downloads',
        help='Output directory for downloaded posts',
    )
    parser.add_argument(
        '--limit', type=int, default=3, help='Number of posts to download (default: 3)'
    )
    parser.add_argument(
        '--start', type=int, default=0, help='Starting index (default: 0)'
    )

    args = parser.parse_args()

    downloader = HuggingFaceBlogDownloader(args.output)

    try:
        posts = downloader.load_posts(args.urls)
        print(f"Loaded {len(posts)} posts from {args.urls}")

        # Limit posts for testing
        posts_to_download = posts[args.start : args.start + args.limit]
        print(f"Downloading {len(posts_to_download)} posts...")

        successful_downloads = 0
        for post in posts_to_download:
            try:
                downloader.download_post(post)
                successful_downloads += 1
            except Exception as e:
                print(f"✗ Failed to download {post['title']}: {e}")

        print(
            f"\n✓ Completed! Successfully downloaded {successful_downloads}/{len(posts_to_download)} posts to {args.output}"
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
