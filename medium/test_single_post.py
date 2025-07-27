#!/usr/bin/env python3
"""
Test script to process a single Medium post
"""

import os
from pathlib import Path
from process_posts import MediumPostProcessor

def test_single_post():
    """Test processing a single post"""
    # Use a specific post that we know has images
    test_file = Path("posts/2017-05-19_Create-your-own-Basquiat-with-Deep-Learning-for-much-less-than--110-million-314aa07c9ba8.html")
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    print(f"Testing with file: {test_file}")
    
    # Create a test processor
    processor = MediumPostProcessor(output_dir="test_output")
    
    # Process just this one file
    processor.process_post(test_file)
    
    print("Test completed! Check the test_output directory.")

if __name__ == "__main__":
    test_single_post() 