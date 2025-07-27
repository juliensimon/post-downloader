#!/usr/bin/env python3
"""
Script to fix remaining external links that should be localized.
This handles the specific cases found in the search results.
"""

import os
import re
from pathlib import Path

def create_remaining_external_mapping():
    """Create mapping for remaining external links that should be localized."""
    external_mapping = {
        # Additional BecomingHuman links that should be localized
        "https://becominghuman.ai/johnny-pi-i-am-your-father-part-1-moving-around-e09fe95bbfce": "../2017-08-21_Johnny-Pi--I-am-your-father---part-1--moving-around/index.html",
        "https://becominghuman.ai/johnny-pi-i-am-your-father-part-2-the-joystick-db8ac067e86": "../2017-08-28_Johnny-Pi--I-am-your-father---part-2--the-joystick/index.html",
        "https://becominghuman.ai/an-introduction-to-the-mxnet-api-part-1-848febdcf8ab": "../2017-04-09_An-introduction-to-the-MXNet-API---part-1/index.html",
        "https://becominghuman.ai/training-mxnet-part-2-cifar-10-c7b0b729c33c": "../2017-04-24_Training-MXNet---part-2--CIFAR-10/index.html",
        "https://becominghuman.ai/tumbling-down-the-sgd-rabbit-hole-part-1-740fa402f0d7": "../2018-03-14_Tumbling-down-the-SGD-rabbit-hole---part-1/index.html",
        
        # Additional TowardsDataScience links that should be localized
        "https://towardsdatascience.com/an-introduction-to-the-mxnet-api-part-4-df22560b83fe": "../2017-04-14_An-introduction-to-the-MXNet-API---part-4/index.html",
        "https://towardsdatascience.com/tensorflow-performance-analysis-314b56dceb59": "../2019-12-04_Making-Amazon-SageMaker-and-TensorFlow-Work-for-You/index.html",
        "https://towardsdatascience.com/how-to-do-deep-learning-on-graphs-with-graph-convolutional-networks-7d2250723780": "../2019-12-22_A-primer-on-Graph-Neural-Networks-with-Amazon-Neptune-and-the-Deep-Graph-Library/index.html"
    }
    return external_mapping

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
    """Main function to fix remaining external links."""
    processed_dir = Path("processed_posts")
    
    # Create mapping
    external_mapping = create_remaining_external_mapping()
    
    total_external_fixes = 0
    files_processed = 0
    
    # Process all HTML files (including the duplicate ones)
    for html_file in processed_dir.rglob("*.html"):
        external_fixes = localize_external_links_in_file(html_file, external_mapping)
        
        if external_fixes > 0:
            print(f"Fixed {external_fixes} external links in {html_file}")
            total_external_fixes += external_fixes
            files_processed += 1
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total external links localized: {total_external_fixes}")

if __name__ == "__main__":
    main() 