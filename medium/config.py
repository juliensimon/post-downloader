#!/usr/bin/env python3
"""
Configuration for Medium Posts Processor

This module contains configuration settings for processing Medium posts.
You can create different config files for different authors.
"""

from typing import Dict, List, Optional

import json
import os
from pathlib import Path


class MediumConfig:
    """Configuration class for Medium posts processing"""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration from file or use defaults

        Args:
            config_file: Path to JSON configuration file
        """
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        else:
            self.set_defaults()

    def set_defaults(self):
        """Set default configuration values"""
        self.author_username = "julsimon"
        self.author_display_name = "Julien Simon"
        self.medium_base_url = "https://medium.com"
        self.author_url = f"{self.medium_base_url}/@{self.author_username}"

        # Processing settings
        self.posts_dir = "posts"
        self.output_dir = "posts_by_year"
        self.image_quality = 85
        self.download_delay = 3.0
        self.max_retries = 3
        self.retry_delay = 60

        # HTML cleaning settings
        self.remove_data_attributes = [
            'data-image-id',
            'data-width',
            'data-height',
            'data-is-featured',
            'data-href',
            'data-action',
            'data-action-observe-only',
            'data-paragraph-count',
        ]

        self.remove_medium_classes = [
            'graf',
            'markup--anchor',
            'markup--p-anchor',
            'markup--li-anchor',
            'markup--em',
            'markup--strong',
            'markup--h3-anchor',
            'markup--h4-anchor',
            'graf--h3',
            'graf--p',
            'graf--h4',
            'graf--li',
            'graf--figure',
            'graf--iframe',
            'graf--layoutFillWidth',
            'graf--layoutOutsetCenter',
            'graf--layoutOutsetRow',
            'graf--leading',
            'graf--title',
            'graf--startsWithDoubleQuote',
            'graf-after--h3',
            'graf-after--p',
            'graf-after--h4',
            'graf-after--figure',
            'graf-after--li',
            'is-partialWidth',
            'graf--trailing',
            'section--body',
            'section--first',
            'section--last',
            'section-divider',
            'section-content',
            'section-inner',
            'sectionLayout--insetColumn',
            'sectionLayout--fullWidth',
            'sectionLayout--outsetColumn',
            'sectionLayout--outsetRow',
            'imageCaption',
            'graf-imageAnchor',
        ]

        self.remove_elements = ['iframe', 'script']

        # User agent for downloads
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

        # Internal link patterns
        self.internal_link_patterns = [
            f"{self.medium_base_url}/@{self.author_username}/",
            f"{self.author_url}/",
        ]

    def load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Load basic settings
        self.author_username = config_data.get('author_username', 'julsimon')
        self.author_display_name = config_data.get(
            'author_display_name', 'Julien Simon'
        )
        self.medium_base_url = config_data.get('medium_base_url', 'https://medium.com')
        self.author_url = f"{self.medium_base_url}/@{self.author_username}"

        # Load processing settings
        self.posts_dir = config_data.get('posts_dir', 'posts')
        self.output_dir = config_data.get('output_dir', 'posts_by_year')
        self.image_quality = config_data.get('image_quality', 85)
        self.download_delay = config_data.get('download_delay', 3.0)
        self.max_retries = config_data.get('max_retries', 3)
        self.retry_delay = config_data.get('retry_delay', 60)

        # Load HTML cleaning settings
        self.remove_data_attributes = config_data.get(
            'remove_data_attributes',
            [
                'data-image-id',
                'data-width',
                'data-height',
                'data-is-featured',
                'data-href',
                'data-action',
                'data-action-observe-only',
                'data-paragraph-count',
            ],
        )

        self.remove_medium_classes = config_data.get(
            'remove_medium_classes',
            [
                'graf',
                'markup--anchor',
                'markup--p-anchor',
                'markup--li-anchor',
                'markup--em',
                'markup--strong',
                'markup--h3-anchor',
                'markup--h4-anchor',
                'graf--h3',
                'graf--p',
                'graf--h4',
                'graf--li',
                'graf--figure',
                'graf--iframe',
                'graf--layoutFillWidth',
                'graf--layoutOutsetCenter',
                'graf--layoutOutsetRow',
                'graf--leading',
                'graf--title',
                'graf--startsWithDoubleQuote',
                'graf-after--h3',
                'graf-after--p',
                'graf-after--h4',
                'graf-after--figure',
                'graf-after--li',
                'is-partialWidth',
                'graf--trailing',
                'section--body',
                'section--first',
                'section--last',
                'section-divider',
                'section-content',
                'section-inner',
                'sectionLayout--insetColumn',
                'sectionLayout--fullWidth',
                'sectionLayout--outsetColumn',
                'sectionLayout--outsetRow',
                'imageCaption',
                'graf-imageAnchor',
            ],
        )

        self.remove_elements = config_data.get('remove_elements', ['iframe', 'script'])

        # Load user agent
        self.user_agent = config_data.get(
            'user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        # Load internal link patterns
        self.internal_link_patterns = config_data.get(
            'internal_link_patterns',
            [f"{self.medium_base_url}/@{self.author_username}/", f"{self.author_url}/"],
        )

    def save_to_file(self, config_file: str):
        """Save current configuration to JSON file"""
        config_data = {
            'author_username': self.author_username,
            'author_display_name': self.author_display_name,
            'medium_base_url': self.medium_base_url,
            'posts_dir': self.posts_dir,
            'output_dir': self.output_dir,
            'image_quality': self.image_quality,
            'download_delay': self.download_delay,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'remove_data_attributes': self.remove_data_attributes,
            'remove_medium_classes': self.remove_medium_classes,
            'remove_elements': self.remove_elements,
            'user_agent': self.user_agent,
            'internal_link_patterns': self.internal_link_patterns,
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def get_internal_link_patterns(self) -> List[str]:
        """Get patterns for detecting internal links"""
        return self.internal_link_patterns

    def is_internal_link(self, url: str) -> bool:
        """Check if a URL is an internal link"""
        return any(pattern in url for pattern in self.internal_link_patterns)


def load_config(config_name: str = "julsimon") -> MediumConfig:
    """
    Load configuration for a specific author

    Args:
        config_name: Name of the configuration (e.g., 'julsimon', 'other_author')

    Returns:
        MediumConfig instance
    """
    config_file = f"config_{config_name}.json"

    if os.path.exists(config_file):
        return MediumConfig(config_file)
    else:
        # Return default config if file doesn't exist
        config = MediumConfig()
        if config_name != "julsimon":
            # Update for different author
            config.author_username = config_name
            config.author_display_name = config_name.replace('_', ' ').title()
            config.author_url = f"{config.medium_base_url}/@{config.author_username}"
            config.internal_link_patterns = [
                f"{config.medium_base_url}/@{config.author_username}/",
                f"{config.author_url}/",
            ]
        return config
