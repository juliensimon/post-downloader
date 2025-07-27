#!/usr/bin/env python3
"""
Extract article URLs from Julien Simon's Hugging Face activity page
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_article_urls(html_file):
    """Extract article URLs from the HTML file"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Look for article links
    article_urls = []
    
    # Method 1: Look for "view article" links
    view_article_links = soup.find_all('a', string=re.compile(r'view article', re.I))
    for link in view_article_links:
        href = link.get('href')
        if href:
            full_url = urljoin('https://huggingface.co', href)
            article_urls.append(full_url)
    
    # Method 2: Look for article titles that are links
    article_titles = soup.find_all('h4')
    for title in article_titles:
        link = title.find('a')
        if link:
            href = link.get('href')
            if href:
                full_url = urljoin('https://huggingface.co', href)
                article_urls.append(full_url)
    
    # Method 3: Look for any links that contain 'articles' in the path
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href')
        if href and '/articles/' in href:
            full_url = urljoin('https://huggingface.co', href)
            if full_url not in article_urls:
                article_urls.append(full_url)
    
    return article_urls

def main():
    html_file = 'juliensimon_articles.html'
    
    try:
        urls = extract_article_urls(html_file)
        
        print(f"Found {len(urls)} article URLs:")
        print()
        
        for i, url in enumerate(urls, 1):
            print(f"{i:2d}. {url}")
        
        print()
        print(f"Total: {len(urls)} URLs")
        
        # Save to file
        with open('extracted_urls.txt', 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"\nURLs saved to extracted_urls.txt")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 