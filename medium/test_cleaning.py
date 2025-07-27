#!/usr/bin/env python3
"""
Test script to verify HTML cleaning functionality
"""

from process_posts import MediumPostProcessor

def test_html_cleaning():
    """Test the HTML cleaning functionality"""
    processor = MediumPostProcessor()
    
    # Sample HTML with unwanted attributes
    test_html = '''
    <html>
    <body>
        <img data-image-id="1*s3q_ob5bY1V-xB25zJE4iA.png" data-width="800" data-height="600" src="image01.webp">
        <a href="https://example.com" data-href="https://example.com" data-action="link" rel="noopener">Link</a>
        <div data-paragraph-count="3" name="test">Content</div>
        <p class="graf graf--p graf-after--h3">Text</p>
        <iframe src="https://example.com"></iframe>
        <script>alert('test');</script>
    </body>
    </html>
    '''
    
    print("Original HTML:")
    print(test_html)
    print("\n" + "="*50 + "\n")
    
    # Clean the HTML
    cleaned_html = processor.clean_html(test_html)
    
    print("Cleaned HTML:")
    print(cleaned_html)

if __name__ == "__main__":
    test_html_cleaning() 