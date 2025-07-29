#!/usr/bin/env python3
"""
Configuration Creator for Medium Posts Processor

This script helps create new configuration files for different Medium authors.
"""

import argparse
import os

from config import MediumConfig


def create_config(
    author_username: str,
    author_display_name: str = None,
    output_dir: str = None,
    posts_dir: str = None,
):
    """
    Create a new configuration file for a Medium author

    Args:
        author_username: Medium username (e.g., 'julsimon')
        author_display_name: Display name (defaults to username)
        output_dir: Output directory (defaults to 'posts_by_year')
        posts_dir: Posts directory (defaults to 'posts')
    """
    # Create configuration
    config = MediumConfig()

    # Update for the new author
    config.author_username = author_username
    config.author_display_name = (
        author_display_name or author_username.replace('_', ' ').title()
    )
    config.author_url = f"{config.medium_base_url}/@{config.author_username}"

    # Update internal link patterns
    config.internal_link_patterns = [
        f"{config.medium_base_url}/@{config.author_username}/",
        f"{config.author_url}/",
    ]

    # Update directories if specified
    if output_dir:
        config.output_dir = output_dir
    if posts_dir:
        config.posts_dir = posts_dir

    # Save configuration
    config_file = f"config_{author_username}.json"
    config.save_to_file(config_file)

    print(f"Created configuration file: {config_file}")
    print(f"Author: {config.author_display_name}")
    print(f"Username: {config.author_username}")
    print(f"Posts directory: {config.posts_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Internal link patterns: {config.internal_link_patterns}")
    print()
    print("To use this configuration:")
    print(f"  python process_posts.py --config {author_username}")
    print()
    print("Or create the posts directory and run:")
    print(f"  mkdir -p {config.posts_dir}")
    print(f"  python process_posts.py --config {author_username}")


def list_configs():
    """List all available configuration files"""
    config_files = [
        f for f in os.listdir('.') if f.startswith('config_') and f.endswith('.json')
    ]

    if not config_files:
        print("No configuration files found.")
        return

    print("Available configurations:")
    for config_file in config_files:
        config_name = config_file.replace('config_', '').replace('.json', '')
        config = MediumConfig(config_file)
        print(
            f"  - {config_name}: {config.author_display_name} (@{config.author_username})"
        )


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Create configuration files for Medium authors'
    )
    parser.add_argument('author', nargs='?', help='Medium author username')
    parser.add_argument('--display-name', '-d', help='Author display name')
    parser.add_argument('--output-dir', '-o', help='Output directory')
    parser.add_argument('--posts-dir', '-p', help='Posts directory')
    parser.add_argument(
        '--list', '-l', action='store_true', help='List existing configurations'
    )

    args = parser.parse_args()

    if args.list:
        list_configs()
        return

    if not args.author:
        parser.print_help()
        return

    create_config(
        author_username=args.author,
        author_display_name=args.display_name,
        output_dir=args.output_dir,
        posts_dir=args.posts_dir,
    )


if __name__ == "__main__":
    main()
