#!/usr/bin/env python3
"""
Basic tests for Medium Posts Processor

Quick tests to verify core functionality works correctly.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from config import MediumConfig, load_config

        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import config module: {e}")
        return False

    try:
        from process_posts import MediumPostProcessor

        print("✅ Process posts module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import process_posts module: {e}")
        return False

    try:
        from create_config import create_config

        print("✅ Create config module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import create_config module: {e}")
        return False

    return True


def test_config_creation():
    """Test configuration creation"""
    print("\nTesting configuration creation...")

    try:
        from config import MediumConfig

        # Test default config
        config = MediumConfig()
        assert config.author_username == "julsimon"
        assert config.author_display_name == "Julien Simon"
        print("✅ Default configuration created successfully")

        # Test custom config
        config.author_username = "test_author"
        config.author_display_name = "Test Author"
        assert config.author_username == "test_author"
        print("✅ Custom configuration created successfully")

        return True
    except Exception as e:
        print(f"❌ Configuration creation failed: {e}")
        return False


def test_processor_creation():
    """Test processor creation"""
    print("\nTesting processor creation...")

    try:
        from config import MediumConfig
        from process_posts import MediumPostProcessor

        config = MediumConfig()
        processor = MediumPostProcessor(config)

        # Test basic functionality
        assert processor.config.author_username == "julsimon"
        print("✅ Processor created successfully")

        # Test filename sanitization
        sanitized = processor.sanitize_filename("test<>:\"/\\|?*.html")
        assert "test_________.html" in sanitized
        print("✅ Filename sanitization works")

        # Test image filename generation
        filename = processor.generate_image_filename(1)
        assert filename == "image01.webp"
        print("✅ Image filename generation works")

        return True
    except Exception as e:
        print(f"❌ Processor creation failed: {e}")
        return False


def test_html_processing():
    """Test HTML processing functionality"""
    print("\nTesting HTML processing...")

    try:
        from config import MediumConfig
        from process_posts import MediumPostProcessor

        config = MediumConfig()
        processor = MediumPostProcessor(config)

        # Test image URL extraction
        html_content = """
        <html>
        <body>
            <img src="https://cdn-images-1.medium.com/max/800/image1.jpg">
            <img src="https://cdn-images-1.medium.com/max/1200/image2.png">
        </body>
        </html>
        """

        urls = processor.extract_image_urls(html_content)
        assert len(urls) == 2
        assert "https://cdn-images-1.medium.com/max/800/image1.jpg" in urls
        print("✅ Image URL extraction works")

        # Test internal link extraction
        html_content = """
        <html>
        <body>
            <a href="https://medium.com/@julsimon/post1">Internal link</a>
            <a href="https://example.com">External link</a>
        </body>
        </html>
        """

        links = processor.extract_internal_links(html_content)
        assert len(links) == 1
        assert "https://medium.com/@julsimon/post1" in links
        print("✅ Internal link extraction works")

        # Test HTML cleaning
        html_content = """
        <html>
        <body>
            <img data-image-id="1*test.jpg" data-width="800" src="image.jpg">
            <p class="graf graf--p">Text</p>
            <iframe src="https://example.com"></iframe>
        </body>
        </html>
        """

        cleaned_html = processor.clean_html(html_content)
        assert "data-image-id" not in cleaned_html
        assert "data-width" not in cleaned_html
        assert "graf graf--p" not in cleaned_html
        assert "<iframe" not in cleaned_html
        print("✅ HTML cleaning works")

        return True
    except Exception as e:
        print(f"❌ HTML processing failed: {e}")
        return False


def test_config_loading():
    """Test configuration loading"""
    print("\nTesting configuration loading...")

    try:
        from config import load_config

        # Test loading default config
        config = load_config("julsimon")
        assert config.author_username == "julsimon"
        print("✅ Default config loading works")

        # Test loading non-existent config (should create default)
        config = load_config("nonexistent")
        assert config.author_username == "nonexistent"
        print("✅ Non-existent config handling works")

        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


def main():
    """Run all basic tests"""
    print("Running basic tests for Medium Posts Processor...\n")

    tests = [
        test_imports,
        test_config_creation,
        test_processor_creation,
        test_html_processing,
        test_config_loading,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test {test.__name__} failed")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
