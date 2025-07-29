#!/usr/bin/env python3
"""
Test suite for Medium Posts Processor

This module contains comprehensive tests for all functionality of the Medium posts processor.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from config import MediumConfig, load_config
from process_posts import MediumPostProcessor


class TestMediumConfig(unittest.TestCase):
    """Test the configuration system"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = MediumConfig()

    def test_default_config(self):
        """Test default configuration values"""
        self.assertEqual(self.test_config.author_username, "julsimon")
        self.assertEqual(self.test_config.author_display_name, "Julien Simon")
        self.assertEqual(self.test_config.medium_base_url, "https://medium.com")
        self.assertEqual(self.test_config.posts_dir, "posts")
        self.assertEqual(self.test_config.output_dir, "posts_by_year")
        self.assertEqual(self.test_config.image_quality, 85)
        self.assertEqual(self.test_config.download_delay, 3.0)

    def test_config_file_loading(self):
        """Test loading configuration from file"""
        # Create a temporary config file
        config_data = {
            "author_username": "test_author",
            "author_display_name": "Test Author",
            "posts_dir": "test_posts",
            "output_dir": "test_output",
            "image_quality": 90,
            "download_delay": 5.0,
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = MediumConfig(config_file)
            self.assertEqual(config.author_username, "test_author")
            self.assertEqual(config.author_display_name, "Test Author")
            self.assertEqual(config.posts_dir, "test_posts")
            self.assertEqual(config.output_dir, "test_output")
            self.assertEqual(config.image_quality, 90)
            self.assertEqual(config.download_delay, 5.0)
        finally:
            os.unlink(config_file)

    def test_config_saving(self):
        """Test saving configuration to file"""
        config = MediumConfig()
        config.author_username = "test_save"
        config.author_display_name = "Test Save"

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_file = f.name

        try:
            config.save_to_file(config_file)

            # Load the saved config and verify
            loaded_config = MediumConfig(config_file)
            self.assertEqual(loaded_config.author_username, "test_save")
            self.assertEqual(loaded_config.author_display_name, "Test Save")
        finally:
            os.unlink(config_file)

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


class TestMediumPostProcessor(unittest.TestCase):
    """Test the Medium post processor"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = MediumConfig()
        self.test_config.posts_dir = "test_posts"
        self.test_config.output_dir = "test_output"
        self.test_config.download_delay = 0.1  # Faster for testing

        # Create temporary directories
        self.test_dir = tempfile.mkdtemp()
        self.test_posts_dir = Path(self.test_dir) / "test_posts"
        self.test_output_dir = Path(self.test_dir) / "test_output"
        self.test_posts_dir.mkdir()
        self.test_output_dir.mkdir()

        # Update config paths
        self.test_config.posts_dir = str(self.test_posts_dir)
        self.test_config.output_dir = str(self.test_output_dir)

        self.processor = MediumPostProcessor(self.test_config)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        # Test normal filename
        self.assertEqual(
            self.processor.sanitize_filename("normal-file.html"), "normal-file.html"
        )

        # Test problematic characters
        self.assertEqual(
            self.processor.sanitize_filename("file<>:\"/\\|?*.html"),
            "file_________.html",
        )

        # Test long filename
        long_name = "a" * 300
        sanitized = self.processor.sanitize_filename(long_name)
        self.assertLessEqual(len(sanitized), 200)

    def test_generate_image_filename(self):
        """Test image filename generation"""
        filename = self.processor.generate_image_filename(1)
        self.assertEqual(filename, "image01.webp")

        filename = self.processor.generate_image_filename(15)
        self.assertEqual(filename, "image15.webp")

    def test_extract_image_urls(self):
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

    def test_extract_internal_links(self):
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

    def test_create_post_directory_name(self):
        """Test post directory name creation"""
        # Create a test HTML file
        test_file = self.test_posts_dir / "2017-05-19_Post-Title-uuid123.html"
        test_file.write_text("test content")

        dir_name = self.processor.create_post_directory_name(test_file)
        self.assertEqual(dir_name, "2017-05-19_Post-Title-uuid123")

    def test_clean_html(self):
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

    def test_update_html_images(self):
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

    @patch('process_posts.urllib.request.build_opener')
    def test_download_image_success(self, mock_opener):
        """Test successful image download"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'fake_image_data'

        mock_opener_instance = MagicMock()
        mock_opener_instance.open.return_value = mock_response
        mock_opener.return_value = mock_opener_instance

        # Create test output path
        output_path = self.test_output_dir / "test_image.webp"

        # Mock PIL Image and its methods
        with patch('process_posts.Image') as mock_pil:
            mock_image = MagicMock()
            mock_image.mode = 'RGB'
            mock_image.size = (100, 100)
            mock_image.save = MagicMock()
            mock_pil.open.return_value = mock_image

            result = self.processor.download_image(
                "https://example.com/image.jpg", output_path
            )

            self.assertTrue(result)
            # Note: The file might not actually be created due to mocking, but the function should return True

    @patch('process_posts.urllib.request.build_opener')
    def test_download_image_failure(self, mock_opener):
        """Test failed image download"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status = 404

        mock_opener_instance = MagicMock()
        mock_opener_instance.open.return_value = mock_response
        mock_opener.return_value = mock_opener_instance

        output_path = self.test_output_dir / "test_image.webp"

        result = self.processor.download_image(
            "https://example.com/image.jpg", output_path
        )

        self.assertFalse(result)
        # Note: The file won't exist due to the failed download


class TestLoadConfig(unittest.TestCase):
    """Test the load_config function"""

    def test_load_existing_config(self):
        """Test loading existing configuration"""
        # Create a temporary config file
        config_data = {
            "author_username": "test_author",
            "author_display_name": "Test Author",
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            # Create the expected filename
            expected_filename = f"config_test_author.json"
            shutil.copy(config_file, expected_filename)

            config = load_config("test_author")
            self.assertEqual(config.author_username, "test_author")
            self.assertEqual(config.author_display_name, "Test Author")

        finally:
            os.unlink(config_file)
            if os.path.exists(expected_filename):
                os.unlink(expected_filename)

    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration (should use defaults)"""
        config = load_config("nonexistent_author")
        self.assertEqual(config.author_username, "nonexistent_author")
        self.assertEqual(config.author_display_name, "Nonexistent Author")


def run_tests():
    """Run all tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes using the new method
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestMediumConfig))
    test_suite.addTest(loader.loadTestsFromTestCase(TestMediumPostProcessor))
    test_suite.addTest(loader.loadTestsFromTestCase(TestLoadConfig))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
