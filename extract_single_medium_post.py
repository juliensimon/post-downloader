#!/usr/bin/env python3
"""
Simple Medium Post Extractor

This script downloads a single Medium post and extracts its content.
"""

import copy
from datetime import datetime, timedelta

import argparse
import logging
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MediumPostExtractor:
    def __init__(self):
        """Initialize the extractor"""
        self.session = urllib.request.build_opener()
        self.session.addheaders = [
            (
                'User-Agent',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            )
        ]

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

    def sanitize_filename(self, filename):
        """Sanitize filename for safe filesystem usage"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

    def clean_content(self, article_elem):
        """Clean the article content by removing unwanted elements and sections"""
        if not article_elem:
            return None

        # Create a copy to avoid modifying the original
        cleaned_article = copy.deepcopy(article_elem)

        # Remove unwanted elements
        for elem in cleaned_article.find_all(['script', 'style', 'iframe']):
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
            else:
                # Try to find any element with an img tag
                first_img_element = None
                for elem in subtitle.find_next_siblings():
                    if elem.find('img'):
                        first_img_element = elem
                        break

                if first_img_element:
                    # Remove all elements between subtitle and first img element
                    current_elem = subtitle.find_next_sibling()
                    while current_elem and current_elem != first_img_element:
                        next_elem = current_elem.find_next_sibling()
                        current_elem.decompose()
                        current_elem = next_elem

        # Additional cleaning: Remove specific unwanted elements by class or data attributes
        unwanted_selectors = [
            '[data-testid="authorPhoto"]',
            '[data-testid="authorName"]',
            '[data-testid="storyReadTime"]',
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
        ]

        for selector in unwanted_selectors:
            for elem in cleaned_article.select(selector):
                elem.decompose()

        return cleaned_article

    def extract_post_info(self, url):
        """Extract post information from URL"""
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
            # Try multiple selectors for date
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
                            # Convert ISO date to readable format
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
                            # Look for actual date patterns first
                            import re

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

    def save_post(self, post_info, output_dir="extracted_posts"):
        """Save the post to a file"""
        if not post_info:
            logger.error("No post info to save")
            return False

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Create filename from title
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

        filepath = output_path / filename

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
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-size: 0.9em; margin-bottom: 2em; }}
        .content {{ line-height: 1.8; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>{post_info['title'] or 'Untitled'}</h1>
    <div class="meta">
        <p><strong>Author:</strong> {post_info['author'] or 'Unknown'}</p>
        <p><strong>Date:</strong> {post_info['date'] or 'Unknown'}</p>
        <p><strong>Source:</strong> <a href="{post_info['url']}">{post_info['url']}</a></p>
    </div>
    <div class="content">
        {post_info['content'] or '<p>No content available</p>'}
    </div>
</body>
</html>"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Post saved to: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving post: {e}")
            return False

    def extract_post(self, url, output_dir="extracted_posts"):
        """Extract a single post from URL"""
        logger.info(f"Starting extraction of: {url}")

        # Extract post information
        post_info = self.extract_post_info(url)

        if not post_info:
            logger.error("Failed to extract post information")
            return False

        # Save the post
        success = self.save_post(post_info, output_dir)

        if success:
            logger.info("Post extraction completed successfully")
            return True
        else:
            logger.error("Failed to save post")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Extract a single Medium post')
    parser.add_argument('url', help='URL of the Medium post to extract')
    parser.add_argument(
        '--output-dir',
        default='extracted_posts',
        help='Output directory for extracted posts (default: extracted_posts)',
    )

    args = parser.parse_args()

    extractor = MediumPostExtractor()
    success = extractor.extract_post(args.url, args.output_dir)

    if success:
        print("✅ Post extracted successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to extract post")
        sys.exit(1)


if __name__ == "__main__":
    main()
