#!/usr/bin/env python3
"""
Final script to fix remaining cross-links and localize external links.
This handles the specific cases that weren't caught by previous scripts.
"""

import os
import re
from pathlib import Path

def create_comprehensive_series_mapping():
    """Create a comprehensive mapping of all series and their posts."""
    series_mapping = {
        # Johnny Pi series
        "Johnny Pi": {
            "part 0": "2017-08-14_Johnny-Pi--I-am-your-father---part-0",
            "part 1": "2017-08-21_Johnny-Pi--I-am-your-father---part-1--moving-around", 
            "part 2": "2017-08-28_Johnny-Pi--I-am-your-father---part-2--the-joystick",
            "part 3": "2017-09-04_Johnny-Pi--I-am-your-father---part-3--adding-cloud-based-speech",
            "part 4": "2017-09-11_Johnny-Pi--I-am-your-father---part-4--adding-cloud-based-vision",
            "part 5": "2017-09-17_Johnny-Pi--I-am-your-father---part-5--adding-MXNet-for-local-image-classification",
            "part 6": "2017-10-05_Johnny-Pi--I-am-your-father---part-6--now-I-m-pushing-your-button--ha-",
            "part 7": "2017-11-01_Johnny-Pi--I-am-your-father---part-7--son--we-need-to-talk",
            "part 8": "2018-06-07_Johnny-Pi--I-am-your-father---part-8--reading--translating-and-more-"
        },
        
        # ImageNet series
        "ImageNet": {
            "part 1": "2017-09-19_ImageNet---part-1--going-on-an-adventure",
            "part 2": "2017-09-24_ImageNet---part-2--the-road-goes-ever-on-and-on"
        },
        
        # Keras shoot-out series
        "Keras shoot-out": {
            "part 1": "2017-09-03_Keras-shoot-out--TensorFlow-vs-MXNet",
            "part 2": "2017-09-08_Keras-shoot-out--part-2--a-deeper-look-at-memory-usage",
            "part 3": "2017-09-10_Keras-shoot-out--part-3--fine-tuning"
        },
        
        # SGD rabbit hole series
        "SGD rabbit hole": {
            "part 1": "2018-03-14_Tumbling-down-the-SGD-rabbit-hole---part-1",
            "part 2": "2018-03-17_Tumbling-down-the-SGD-rabbit-hole---part-2"
        },
        
        # 10 steps series
        "10 steps": {
            "part 1": "2018-01-12_10-steps-on-the-road-to-Deep-Learning--part-1-",
            "part 2": "2018-01-15_10-steps-on-the-road-to-Deep-Learning--part-2-"
        }
    }
    return series_mapping

def create_external_link_mapping():
    """Create mapping for external links that should be localized."""
    external_mapping = {
        # BecomingHuman links to local posts
        "https://becominghuman.ai/johnny-pi-i-am-your-father-part-1-moving-around-e09fe95bbfce": "../2017-08-21_Johnny-Pi--I-am-your-father---part-1--moving-around/index.html",
        "https://becominghuman.ai/johnny-pi-i-am-your-father-part-2-the-joystick-db8ac067e86": "../2017-08-28_Johnny-Pi--I-am-your-father---part-2--the-joystick/index.html",
        "https://becominghuman.ai/an-introduction-to-the-mxnet-api-part-1-848febdcf8ab": "../2017-04-09_An-introduction-to-the-MXNet-API---part-1/index.html",
        "https://becominghuman.ai/training-mxnet-part-2-cifar-10-c7b0b729c33c": "../2017-04-24_Training-MXNet---part-2--CIFAR-10/index.html",
        "https://becominghuman.ai/tumbling-down-the-sgd-rabbit-hole-part-1-740fa402f0d7": "../2018-03-14_Tumbling-down-the-SGD-rabbit-hole---part-1/index.html",
        
        # TowardsDataScience links to local posts
        "https://towardsdatascience.com/an-introduction-to-the-mxnet-api-part-4-df22560b83fe": "../2017-04-14_An-introduction-to-the-MXNet-API---part-4/index.html",
        "https://towardsdatascience.com/tensorflow-performance-analysis-314b56dceb59": "../2019-12-04_Making-Amazon-SageMaker-and-TensorFlow-Work-for-You/index.html",
        "https://towardsdatascience.com/how-to-do-deep-learning-on-graphs-with-graph-convolutional-networks-7d2250723780": "../2019-12-22_A-primer-on-Graph-Neural-Networks-with-Amazon-Neptune-and-the-Deep-Graph-Library/index.html"
    }
    return external_mapping

def fix_cross_links_in_file(file_path, series_mapping):
    """Fix cross-links in a specific file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Get the current post directory name
    current_dir = Path(file_path).parent.name
    
    # Check each series for cross-links
    for series_name, parts in series_mapping.items():
        for part_name, target_dir in parts.items():
            # Skip if this is the current post
            if target_dir == current_dir:
                continue
                
            # Look for patterns like "Part X: <a href="index.html">description</a>"
            patterns = [
                rf'Part\s+\d+:\s*<a\s+href="index\.html"[^>]*>{part_name}</a>',
                rf'<a\s+href="index\.html"[^>]*>{part_name}</a>',
                rf'<a\s+href="index\.html"[^>]*>.*?{part_name}.*?</a>'
            ]
            
            for pattern in patterns:
                replacement = f'<a href="../{target_dir}/index.html">{part_name}</a>'
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    content = new_content
                    changes_made += 1
    
    # Fix specific context-based cross-links
    context_fixes = [
        # Johnny Pi series specific fixes
        (r'<a href="index\.html"[^>]*>Previously</a>', f'<a href="../2017-10-05_Johnny-Pi--I-am-your-father---part-6--now-I-m-pushing-your-button--ha-/index.html">Previously</a>'),
        (r'<a href="index\.html"[^>]*>a sneak preview</a>', f'<a href="../2017-08-14_Johnny-Pi--I-am-your-father---part-0/index.html">a sneak preview</a>'),
        (r'<a href="index\.html"[^>]*>cloud-based speech</a>', f'<a href="../2017-09-04_Johnny-Pi--I-am-your-father---part-3--adding-cloud-based-speech/index.html">cloud-based speech</a>'),
        (r'<a href="index\.html"[^>]*>cloud-based vision</a>', f'<a href="../2017-09-11_Johnny-Pi--I-am-your-father---part-4--adding-cloud-based-vision/index.html">cloud-based vision</a>'),
        (r'<a href="index\.html"[^>]*>local vision</a>', f'<a href="../2017-09-17_Johnny-Pi--I-am-your-father---part-5--adding-MXNet-for-local-image-classification/index.html">local vision</a>'),
        (r'<a href="index\.html"[^>]*>local image classification with MXNet</a>', f'<a href="../2017-09-17_Johnny-Pi--I-am-your-father---part-5--adding-MXNet-for-local-image-classification/index.html">local image classification with MXNet</a>'),
        (r'<a href="index\.html"[^>]*>the IoT button</a>', f'<a href="../2017-10-05_Johnny-Pi--I-am-your-father---part-6--now-I-m-pushing-your-button--ha-/index.html">the IoT button</a>'),
        
        # ImageNet series specific fixes
        (r'<a href="index\.html"[^>]*>In a previous post</a>', f'<a href="../2017-09-19_ImageNet---part-1--going-on-an-adventure/index.html">In a previous post</a>'),
        
        # SageMaker specific fixes
        (r'<a href="index\.html"[^>]*>previous video</a>', f'<a href="../2017-11-30_Amazon-SageMaker/index.html">previous video</a>'),
        
        # Keras shoot-out series specific fixes
        (r'<a href="index\.html"[^>]*>In part 2</a>', f'<a href="../2017-09-08_Keras-shoot-out--part-2--a-deeper-look-at-memory-usage/index.html">In part 2</a>'),
        (r'<a href="index\.html"[^>]*>In part 3</a>', f'<a href="../2017-09-10_Keras-shoot-out--part-3--fine-tuning/index.html">In part 3</a>'),
    ]
    
    for pattern, replacement in context_fixes:
        new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        if new_content != content:
            content = new_content
            changes_made += 1
    
    if changes_made > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return 0

def localize_external_links_in_file(file_path, external_mapping):
    """Localize external links in a specific file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    for external_url, local_path in external_mapping.items():
        # Replace the external URL with local path
        new_content = content.replace(external_url, local_path)
        if new_content != content:
            content = new_content
            changes_made += 1
    
    if changes_made > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return changes_made
    
    return 0

def main():
    """Main function to fix all remaining cross-links and external links."""
    processed_dir = Path("processed_posts")
    
    # Create mappings
    series_mapping = create_comprehensive_series_mapping()
    external_mapping = create_external_link_mapping()
    
    total_cross_fixes = 0
    total_external_fixes = 0
    files_processed = 0
    
    # Process all HTML files
    for html_file in processed_dir.rglob("*.html"):
        if html_file.name == "index.html":  # Only process main index.html files
            cross_fixes = fix_cross_links_in_file(html_file, series_mapping)
            external_fixes = localize_external_links_in_file(html_file, external_mapping)
            
            if cross_fixes > 0 or external_fixes > 0:
                print(f"Fixed {cross_fixes} cross-links and {external_fixes} external links in {html_file}")
                total_cross_fixes += cross_fixes
                total_external_fixes += external_fixes
                files_processed += 1
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total cross-links fixed: {total_cross_fixes}")
    print(f"Total external links localized: {total_external_fixes}")

if __name__ == "__main__":
    main() 