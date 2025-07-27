#!/usr/bin/env python3
"""
Script to fix remaining cross-links that weren't caught by the main cross-link fixer.
This handles cases where links are more generic and need context analysis.
"""

import os
import re
from pathlib import Path

def create_series_mapping():
    """Create a comprehensive mapping of series and their posts."""
    series_mapping = {
        "MXNet API": {
            "part 1": "2017-04-09_An-introduction-to-the-MXNet-API---part-1",
            "part 2": "2017-04-10_An-introduction-to-the-MXNet-API---part-2", 
            "part 3": "2017-04-12_An-introduction-to-the-MXNet-API---part-3",
            "part 4": "2017-04-14_An-introduction-to-the-MXNet-API---part-4",
            "part 5": "2017-04-15_An-introduction-to-the-MXNet-API---part-5",
            "part 6": "2017-04-16_An-introduction-to-the-MXNet-API---part-6",
        },
        "Training MXNet": {
            "part 1": "2017-04-18_Training-MXNet---part-1--MNIST",
            "part 2": "2017-04-24_Training-MXNet---part-2--CIFAR-10",
            "part 3": "2017-04-28_Training-MXNet---part-3--CIFAR-10-redux",
            "part 4": "2017-05-05_Training-MXNet---part-4--distributed-training",
        },
        "ImageNet": {
            "part 1": "2017-09-19_ImageNet---part-1--going-on-an-adventure",
            "part 2": "2017-09-24_ImageNet---part-2--the-road-goes-ever-on-and-on",
        },
        "Keras shoot-out": {
            "part 1": "2017-09-03_Keras-shoot-out--TensorFlow-vs-MXNet",
            "part 2": "2017-09-08_Keras-shoot-out--part-2--a-deeper-look-at-memory-usage",
            "part 3": "2017-09-10_Keras-shoot-out--part-3--fine-tuning",
        },
        "Speeding up MXNet": {
            "part 1": "2017-09-09_Speeding-up-Apache-MXNet-with-the-NNPACK-library",
            "part 2": "2017-09-15_Speeding-up-Apache-MXNet-with-the-NNPACK-library--Raspberry-Pi-edition-",
            "part 3": "2017-11-17_Speeding-up-Apache-MXNet--part-3--let-s-smash-it-with-C5-and-Intel-MKL",
        },
        "GANs": {
            "part 1": "2017-11-13_Generative-Adversarial-Networks-on-Apache-MXNet--part-1",
        },
        "Deep Learning Projects": {
            "part 1": "2017-07-02_10-Deep-Learning-projects-based-on-Apache-MXNet",
            "part 2": "2018-02-25_Yet-another-10-Deep-Learning-projects-based-on-Apache-MXNet",
        },
    }
    return series_mapping

def fix_remaining_cross_links_in_file(file_path, series_mapping):
    """Fix remaining cross-links in a specific HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    original_content = content
    changes_made = False
    
    # Look for patterns like "Part X" followed by a link to index.html
    # This handles the case in the "Getting started" post
    for series_name, parts in series_mapping.items():
        for part_name, post_dir in parts.items():
            # Pattern to match "Part X" followed by a link to index.html
            patterns = [
                rf'· <a href="index\.html"[^>]*>Part {part_name.split()[-1]}</a>',
                rf'· <a href="index\.html"[^>]*>Part {part_name.split()[-1]}[^<]*</a>',
                rf'<a href="index\.html"[^>]*>Part {part_name.split()[-1]}</a>',
                rf'<a href="index\.html"[^>]*>Part {part_name.split()[-1]}[^<]*</a>',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    relative_path = f'../{post_dir}/index.html'
                    new_link = match.replace('href="index.html"', f'href="{relative_path}"')
                    content = content.replace(match, new_link)
                    changes_made = True
                    print(f"  Fixed cross-link to {post_dir} in {file_path.parent.name}")
    
    # Also look for links that mention specific content and link to index.html
    # This handles cases like "recognizing images with Inception v3" linking to index.html
    content_patterns = [
        (r'NDArray API', '2017-04-09_An-introduction-to-the-MXNet-API---part-1'),
        (r'Symbol API', '2017-04-10_An-introduction-to-the-MXNet-API---part-2'),
        (r'Module API', '2017-04-12_An-introduction-to-the-MXNet-API---part-3'),
        (r'Inception v3', '2017-04-14_An-introduction-to-the-MXNet-API---part-4'),
        (r'VGG16 and ResNet-152', '2017-04-15_An-introduction-to-the-MXNet-API---part-5'),
        (r'Raspberry Pi', '2017-04-16_An-introduction-to-the-MXNet-API---part-6'),
        (r'MNIST', '2017-04-18_Training-MXNet---part-1--MNIST'),
        (r'CIFAR-10', '2017-04-24_Training-MXNet---part-2--CIFAR-10'),
        (r'AdaDelta', '2017-04-28_Training-MXNet---part-3--CIFAR-10-redux'),
        (r'distributed training', '2017-05-05_Training-MXNet---part-4--distributed-training'),
        (r'TensorFlow vs MXNet', '2017-09-03_Keras-shoot-out--TensorFlow-vs-MXNet'),
        (r'memory usage', '2017-09-08_Keras-shoot-out--part-2--a-deeper-look-at-memory-usage'),
        (r'fine-tuning', '2017-09-10_Keras-shoot-out--part-3--fine-tuning'),
        (r'NNPACK', '2017-09-09_Speeding-up-Apache-MXNet-with-the-NNPACK-library'),
        (r'Intel MKL', '2017-11-17_Speeding-up-Apache-MXNet--part-3--let-s-smash-it-with-C5-and-Intel-MKL'),
        (r'MNIST-like images', '2017-11-13_Generative-Adversarial-Networks-on-Apache-MXNet--part-1'),
    ]
    
    for content_pattern, post_dir in content_patterns:
        # Look for the content pattern followed by a link to index.html
        pattern = rf'<a href="index\.html"[^>]*>.*?{re.escape(content_pattern)}[^<]*</a>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            relative_path = f'../{post_dir}/index.html'
            new_link = match.replace('href="index.html"', f'href="{relative_path}"')
            content = content.replace(match, new_link)
            changes_made = True
            print(f"  Fixed content-based cross-link to {post_dir} in {file_path.parent.name}")
    
    if changes_made:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file_path}")
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False
    
    return False

def main():
    """Main function to fix remaining cross-links."""
    print("Creating series mapping...")
    series_mapping = create_series_mapping()
    
    print(f"Found {len(series_mapping)} series with detailed mappings")
    
    print("\nFixing remaining cross-links...")
    total_fixed = 0
    
    # Process all HTML files in processed_posts
    for html_file in Path("processed_posts").rglob("*.html"):
        if html_file.name == "index.html":
            print(f"  Processing {html_file.parent.name}...")
            if fix_remaining_cross_links_in_file(html_file, series_mapping):
                total_fixed += 1
    
    print(f"\nTotal files updated: {total_fixed}")

if __name__ == "__main__":
    main() 