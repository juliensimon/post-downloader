#!/usr/bin/env python3
"""
Script to fix cross-links in processed posts by replacing incorrect index.html references
with proper relative paths to other posts in the same series, and localize external links.
"""

import os
import re
import glob
from pathlib import Path

def find_series_posts():
    """Find all series posts and group them by series."""
    processed_dir = Path("processed_posts")
    series_map = {}
    
    # Define known series patterns
    series_patterns = {
        "MXNet API": r"An-introduction-to-the-MXNet-API---part-(\d+)",
        "Johnny Pi": r"Johnny-Pi--I-am-your-father---part-(\d+)",
        "Training MXNet": r"Training-MXNet---part-(\d+)",
        "ImageNet": r"ImageNet---part-(\d+)",
        "SGD Rabbit Hole": r"Tumbling-down-the-SGD-rabbit-hole---part-(\d+)",
        "10 Steps Deep Learning": r"10-steps-on-the-road-to-Deep-Learning--part-(\d+)",
        "Amazon AI Monthly": r"Amazon-AI-Monthly---([A-Za-z]+-\d{4})",
        "Scaling ML": r"Scaling-Machine-Learning-from-0-to-millions-of-users--part-(\d+)",
        "GANs": r"Generative-Adversarial-Networks-on-Apache-MXNet--part-(\d+)",
        "Deep Learning Projects": r"(\d+)-Deep-Learning-projects-based-on-Apache-MXNet",
        "Keras Shoot-out": r"Keras-shoot-out--part-(\d+)",
        "Speeding up MXNet": r"Speeding-up-Apache-MXNet--part-(\d+)",
    }
    
    for post_dir in processed_dir.iterdir():
        if not post_dir.is_dir():
            continue
            
        dir_name = post_dir.name
        
        # Check each series pattern
        for series_name, pattern in series_patterns.items():
            match = re.search(pattern, dir_name)
            if match:
                if series_name not in series_map:
                    series_map[series_name] = []
                series_map[series_name].append((dir_name, match.group(1)))
                break
    
    # Sort each series by part number
    for series_name in series_map:
        series_map[series_name].sort(key=lambda x: int(x[1]) if x[1].isdigit() else x[1])
    
    return series_map

def create_external_link_mapping():
    """Create a mapping of external links to local posts."""
    external_mapping = {
        # Towards Data Science links
        "https://towardsdatascience.com/a-map-for-machine-learning-on-aws-a285fcd8d932": "2019-12-08_A-map-for-Machine-Learning-on-AWS--December-2019-edition-",
        "https://towardsdatascience.com/tensorflow-performance-analysis-314b56dceb59": "2020-06-22_Deep-Dive-on-TensorFlow-training-with-Amazon-SageMaker-and-Amazon-S3",
        "https://towardsdatascience.com/how-to-do-deep-learning-on-graphs-with-graph-convolutional-networks-7d2250723780": "2019-12-22_A-primer-on-Graph-Neural-Networks-with-Amazon-Neptune-and-the-Deep-Graph-Library",
        "https://towardsdatascience.com/an-introduction-to-the-mxnet-api-part-4-df22560b83fe": "2017-04-14_An-introduction-to-the-MXNet-API---part-4",
        
        # Becoming Human links
        "https://becominghuman.ai/johnny-pi-i-am-your-father-part-1-moving-around-e09fe95bbfce": "2017-08-21_Johnny-Pi--I-am-your-father---part-1--moving-around",
    }
    return external_mapping

def fix_cross_links_in_file(file_path, series_map, external_mapping):
    """Fix cross-links in a specific HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    original_content = content
    changes_made = False
    
    # Get the current post directory name
    current_dir = Path(file_path).parent.name
    
    # Find which series this post belongs to
    current_series = None
    current_part = None
    
    for series_name, posts in series_map.items():
        for post_dir, part_num in posts:
            if post_dir == current_dir:
                current_series = series_name
                current_part = part_num
                break
        if current_series:
            break
    
    # Fix cross-links within series
    if current_series:
        series_posts = series_map[current_series]
        
        # Fix links to other parts in the same series
        for post_dir, part_num in series_posts:
            if post_dir != current_dir:
                # Look for patterns like "part X" or "Part X" that link to index.html
                patterns = [
                    rf'<a href="index\.html"[^>]*>.*?[Pp]art {part_num}[^<]*</a>',
                    rf'<a href="index\.html"[^>]*>.*?[Ii]n part {part_num}[^<]*</a>',
                    rf'<a href="index\.html"[^>]*>.*?[Pp]art {part_num}:[^<]*</a>',
                    rf'<a href="index\.html"[^>]*>.*?[Pp]art {part_num}\s*</a>',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Create the correct relative path
                        relative_path = f'../{post_dir}/index.html'
                        new_link = match.replace('href="index.html"', f'href="{relative_path}"')
                        content = content.replace(match, new_link)
                        changes_made = True
                        print(f"  Fixed cross-link to {post_dir} in {current_dir}")
    
    # Fix external links
    for external_url, local_post in external_mapping.items():
        # Find the local post directory
        local_post_dir = None
        for post_dir in Path("processed_posts").iterdir():
            if post_dir.is_dir() and local_post in post_dir.name:
                local_post_dir = post_dir.name
                break
        
        if local_post_dir:
            # Replace external links with local links
            relative_path = f'../{local_post_dir}/index.html'
            
            # Pattern to match the external link
            patterns = [
                rf'href="{re.escape(external_url)}"',
                rf'data-href="{re.escape(external_url)}"',
            ]
            
            for pattern in patterns:
                if re.search(pattern, content):
                    content = re.sub(pattern, f'href="{relative_path}"', content)
                    changes_made = True
                    print(f"  Localized external link {external_url} to {local_post_dir}")
    
    # Fix remaining generic index.html links that might be cross-references
    # Look for links that are clearly meant to be cross-references but don't match specific patterns
    if 'href="index.html"' in content:
        # This is a more conservative approach - we'll need to be more specific
        # about which links to replace based on context
        pass
    
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
    """Main function to fix all cross-links and external links."""
    print("Finding series posts...")
    series_map = find_series_posts()
    
    print(f"Found {len(series_map)} series:")
    for series_name, posts in series_map.items():
        print(f"  {series_name}: {len(posts)} posts")
        for post_dir, part_num in posts:
            print(f"    Part {part_num}: {post_dir}")
    
    print("\nCreating external link mapping...")
    external_mapping = create_external_link_mapping()
    print(f"Found {len(external_mapping)} external links to localize")
    
    print("\nFixing cross-links and external links...")
    total_fixed = 0
    
    # Process all HTML files in processed_posts
    for html_file in Path("processed_posts").rglob("*.html"):
        if html_file.name == "index.html":
            print(f"  Processing {html_file.parent.name}...")
            if fix_cross_links_in_file(html_file, series_map, external_mapping):
                total_fixed += 1
    
    print(f"\nTotal files updated: {total_fixed}")

if __name__ == "__main__":
    main() 