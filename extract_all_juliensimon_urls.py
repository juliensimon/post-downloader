#!/usr/bin/env python3
"""
Extract ALL article URLs from Julien Simon's Hugging Face activity page
Uses Selenium to handle the "Load more" button and get all 25 articles
"""

import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Setup headless Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_article_urls_from_html(html_content):
    """Extract article URLs from HTML content"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    article_urls = []
    
    # Look for article links
    all_links = soup.find_all('a', href=True)
    for link in all_links:
        href = link.get('href')
        if href and '/articles/' in href:
            full_url = urljoin('https://huggingface.co', href)
            if full_url not in article_urls:
                article_urls.append(full_url)
    
    return article_urls

def get_all_article_urls():
    """Get all article URLs by clicking 'Load more' until all articles are loaded"""
    driver = setup_driver()
    
    try:
        # Navigate to the page
        url = "https://huggingface.co/juliensimon/activity/articles"
        print(f"Loading page: {url}")
        driver.get(url)
        
        # Wait for initial content to load
        time.sleep(3)
        
        article_count = 0
        max_attempts = 10  # Prevent infinite loop
        attempts = 0
        
        while attempts < max_attempts:
            # Get current article count
            current_urls = extract_article_urls_from_html(driver.page_source)
            current_count = len(current_urls)
            
            print(f"Current articles found: {current_count}")
            
            if current_count >= 25:
                print(f"Found all {current_count} articles!")
                break
            
            # Look for "Load more" button
            try:
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load more')]"))
                )
                
                print("Clicking 'Load more' button...")
                driver.execute_script("arguments[0].click();", load_more_button)
                
                # Wait for new content to load
                time.sleep(3)
                
                attempts += 1
                
            except Exception as e:
                print(f"No more 'Load more' button found or error: {e}")
                break
        
        # Get final list of URLs
        final_urls = extract_article_urls_from_html(driver.page_source)
        
        return final_urls
        
    finally:
        driver.quit()

def main():
    try:
        print("Extracting all article URLs from Julien Simon's activity page...")
        urls = get_all_article_urls()
        
        print(f"\nFound {len(urls)} article URLs:")
        print()
        
        for i, url in enumerate(urls, 1):
            print(f"{i:2d}. {url}")
        
        print()
        print(f"Total: {len(urls)} URLs")
        
        # Save to file
        with open('all_extracted_urls.txt', 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        print(f"\nURLs saved to all_extracted_urls.txt")
        
        # Also update the huggingface URLs file
        update_huggingface_urls_file(urls)
        
    except Exception as e:
        print(f"Error: {e}")

def update_huggingface_urls_file(urls):
    """Update the huggingface-blog-urls.txt file with the new URLs"""
    try:
        # Convert URLs to the blog format
        blog_urls = []
        for url in urls:
            # Extract the slug from the URL
            if '/articles/' in url:
                slug = url.split('/articles/')[-1]
                blog_url = f"https://huggingface.co/blog/{slug}"
                blog_urls.append(blog_url)
            else:
                blog_urls.append(url)
        
        # Create the new content
        content = "# Hugging Face Blog Posts URLs by Julien Simon (2021-2024)\n\n"
        content += "## 2024\n"
        
        # Group by year (this is a simple approach - you might want to improve this)
        for i, url in enumerate(blog_urls):
            if i < 4:  # First 4 are 2024
                content += f"{url}\n"
        
        content += "\n## 2023\n"
        for i, url in enumerate(blog_urls[4:], 4):
            if i < 15:  # Next 11 are 2023
                content += f"{url}\n"
        
        content += "\n## 2022\n"
        for i, url in enumerate(blog_urls[15:], 15):
            if i < 21:  # Next 6 are 2022
                content += f"{url}\n"
        
        content += "\n## 2021\n"
        for url in blog_urls[21:]:  # Rest are 2021
            content += f"{url}\n"
        
        content += f"\n# Total: {len(blog_urls)} blog posts\n"
        
        # Write to file
        with open('huggingface/huggingface-blog-urls.txt', 'w') as f:
            f.write(content)
        
        print(f"Updated huggingface/huggingface-blog-urls.txt with {len(blog_urls)} URLs")
        
    except Exception as e:
        print(f"Error updating URLs file: {e}")

if __name__ == "__main__":
    main() 