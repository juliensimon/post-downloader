#!/usr/bin/env python3
"""
Simple tests for Medium Posts Processor

Quick tests that don't require network access.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from config import MediumConfig, load_config
from process_posts import MediumPostProcessor


class TestSimpleFunctionality(unittest.TestCase):
    """Test core functionality without network access"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = MediumConfig()
        self.test_config.download_delay = 0.1  # Faster for testing
        self.processor = MediumPostProcessor(self.test_config)

    def test_config_defaults(self):
        """Test default configuration"""
        self.assertEqual(self.test_config.author_username, "julsimon")
        self.assertEqual(self.test_config.author_display_name, "Julien Simon")
        self.assertEqual(self.test_config.image_quality, 85)

    def test_filename_sanitization(self):
        """Test filename sanitization"""
        # Test normal filename
        result = self.processor.sanitize_filename("normal-file.html")
        self.assertEqual(result, "normal-file.html")

        # Test problematic characters
        result = self.processor.sanitize_filename("file<>:\"/\\|?*.html")
        self.assertEqual(result, "file_________.html")

        # Test long filename
        long_name = "a" * 300
        result = self.processor.sanitize_filename(long_name)
        self.assertLessEqual(len(result), 200)

    def test_image_filename_generation(self):
        """Test image filename generation"""
        result = self.processor.generate_image_filename(1)
        self.assertEqual(result, "image01.webp")

        result = self.processor.generate_image_filename(15)
        self.assertEqual(result, "image15.webp")

    def test_image_url_extraction(self):
        """Test image URL extraction from HTML"""
        html_content = """
        <html>
        <body>
            <img src="https://cdn-images-1.medium.com/max/800/image1.jpg">
            <img src="https://cdn-images-1.medium.com/max/1200/image2.png">
            <img src="relative-image.jpg">
        </body>
        </html>
        """

        urls = self.processor.extract_image_urls(html_content)
        expected_urls = [
            "https://cdn-images-1.medium.com/max/800/image1.jpg",
            "https://cdn-images-1.medium.com/max/1200/image2.png",
        ]

        self.assertEqual(set(urls), set(expected_urls))

    def test_internal_link_extraction(self):
        """Test internal link extraction"""
        html_content = """
        <html>
        <body>
            <a href="https://medium.com/@julsimon/post1">Internal link 1</a>
            <a href="https://medium.com/@julsimon/post2">Internal link 2</a>
            <a href="https://medium.com/@other_author/post">External link</a>
            <a href="https://example.com">External link</a>
        </body>
        </html>
        """

        links = self.processor.extract_internal_links(html_content)
        expected_links = [
            "https://medium.com/@julsimon/post1",
            "https://medium.com/@julsimon/post2",
        ]

        self.assertEqual(set(links), set(expected_links))

    def test_html_cleaning(self):
        """Test HTML cleaning functionality"""
        html_content = """
        <html>
        <body>
            <img data-image-id="1*test.jpg" data-width="800" data-height="600" src="image.jpg">
            <a href="https://example.com" data-href="https://example.com" rel="noopener">Link</a>
            <p class="graf graf--p graf-after--h3">Text</p>
            <div data-paragraph-count="3" name="test">Content</div>
            <iframe src="https://example.com"></iframe>
            <script>alert('test');</script>
        </body>
        </html>
        """

        cleaned_html = self.processor.clean_html(html_content)

        # Check that unwanted attributes are removed
        self.assertNotIn("data-image-id", cleaned_html)
        self.assertNotIn("data-width", cleaned_html)
        self.assertNotIn("data-height", cleaned_html)
        self.assertNotIn("data-href", cleaned_html)
        self.assertNotIn("rel=\"noopener\"", cleaned_html)
        self.assertNotIn("data-paragraph-count", cleaned_html)
        self.assertNotIn("name=\"test\"", cleaned_html)

        # Check that unwanted elements are removed
        self.assertNotIn("<iframe", cleaned_html)
        self.assertNotIn("<script", cleaned_html)

        # Check that unwanted classes are removed
        self.assertNotIn("graf graf--p graf-after--h3", cleaned_html)

    def test_html_image_updating(self):
        """Test HTML image link updating"""
        html_content = """
        <html>
        <body>
            <img src="https://cdn-images-1.medium.com/max/800/image1.jpg">
            <img src="https://cdn-images-1.medium.com/max/1200/image2.png">
        </body>
        </html>
        """

        image_mapping = {
            "https://cdn-images-1.medium.com/max/800/image1.jpg": "image01.webp",
            "https://cdn-images-1.medium.com/max/1200/image2.png": "image02.webp",
        }

        updated_html = self.processor.update_html_images(html_content, image_mapping)

        self.assertIn("image01.webp", updated_html)
        self.assertIn("image02.webp", updated_html)
        self.assertNotIn(
            "https://cdn-images-1.medium.com/max/800/image1.jpg", updated_html
        )
        self.assertNotIn(
            "https://cdn-images-1.medium.com/max/1200/image2.png", updated_html
        )

    def test_post_directory_name_creation(self):
        """Test post directory name creation"""
        # Test with UUID
        filename = "2017-05-19_Post-Title-uuid123.html"
        result = self.processor.create_post_directory_name(Path(filename))
        self.assertEqual(result, "2017-05-19_Post-Title-uuid123")

        # Test without UUID
        filename = "2017-05-19_Post-Title.html"
        result = self.processor.create_post_directory_name(Path(filename))
        self.assertEqual(result, "2017-05-19_Post-Title")

    def test_config_loading(self):
        """Test configuration loading"""
        # Test loading default config
        config = load_config("julsimon")
        self.assertEqual(config.author_username, "julsimon")

        # Test loading non-existent config (should create default)
        config = load_config("nonexistent")
        self.assertEqual(config.author_username, "nonexistent")

    def test_internal_link_detection(self):
        """Test internal link detection"""
        config = MediumConfig()
        config.author_username = "test_author"
        config.author_url = "https://medium.com/@test_author"
        config.internal_link_patterns = [
            "https://medium.com/@test_author/",
            "https://medium.com/@test_author",
        ]

        # Test internal links
        self.assertTrue(
            config.is_internal_link("https://medium.com/@test_author/some-post")
        )
        self.assertTrue(config.is_internal_link("https://medium.com/@test_author"))

        # Test external links
        self.assertFalse(
            config.is_internal_link("https://medium.com/@other_author/some-post")
        )
        self.assertFalse(config.is_internal_link("https://example.com"))


def run_simple_tests():
    """Run simple tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test class
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestSimpleFunctionality))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running simple tests for Medium Posts Processor...")
    success = run_simple_tests()
    if success:
        print("\n🎉 All simple tests passed!")
    else:
        print("\n❌ Some simple tests failed!")
    exit(0 if success else 1)
