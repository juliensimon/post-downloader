# Medium Posts Processor

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/julsimon/post-downloader)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/julsimon/post-downloader)

A Python tool for processing and archiving Medium blog posts by Julien Simon. This tool downloads posts, processes images, cleans HTML, and creates a self-contained local archive.

## Demo

See the processed results in action:
- **[AWS Blog Posts](https://www.julien.org/aws-blog-posts.html)** - 68 AWS blog posts (2018-2021)
- **[Hugging Face Blog Posts](https://www.julien.org/huggingface-blog-posts.html)** - 25 Hugging Face blog posts (2021-2024)
- **[Medium Blog Posts](https://www.julien.org/medium-blog-posts.html)** - 25+ Medium blog posts (2015-2021)

These pages demonstrate the clean, organized output that this tool produces.

## Features

- **Configurable**: Works with any Medium author, not just Julien Simon
- **Image Processing**: Downloads remote images and converts them to WebP format
- **Sequential Naming**: Uses sequential naming for images (image01.webp, image02.webp, etc.)
- **Link Updates**: Updates HTML files to reference local images instead of remote URLs
- **Internal Link Processing**: Updates links between posts to reference local files (two-pass approach)
- **HTML Cleaning**: Removes unwanted Medium-specific attributes, classes, and elements
- **Error Handling**: Robust error handling with detailed logging
- **Aggressive Throttling**: Implements configurable delays and exponential backoff for rate limiting
- **Resume Capability**: Can resume processing from where it left off if interrupted
- **Year Organization**: Automatically organizes processed posts by year

## Project Structure

```
medium/
├── README.md              # This documentation
├── process_posts.py       # Main processing script
├── config.py              # Configuration system
├── create_config.py       # Configuration creation utility
├── config_julsimon.json  # Julien Simon's configuration
├── requirements.txt       # Python dependencies
├── posts/                 # Original Medium HTML files
└── posts_by_year/        # Processed posts organized by year
    ├── 2016/
    ├── 2017/
    ├── 2018/
    ├── 2019/
    ├── 2020/
    ├── 2021/
    ├── 2022/
    ├── 2023/
    ├── 2024/
    └── 2025/
```

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd post-downloader/medium
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Process All Posts (Default Configuration)

To process all Medium posts in the `posts/` directory using the default configuration (Julien Simon):

```bash
python process_posts.py
```

### Process with Specific Configuration

To process posts using a specific configuration:

```bash
python process_posts.py --config julsimon
```

### Process for Different Author

To process posts for a different Medium author:

```bash
# Create configuration for new author
python create_config.py other_author

# Process posts for that author
python process_posts.py --config other_author
```

### Quick Author Setup

To quickly set up for a new author without creating a config file:

```bash
python process_posts.py --author other_author
```

### List Available Configurations

To see all available configurations:

```bash
python process_posts.py --list-configs
# or
python create_config.py --list
```

### What the Processing Does

The script will:
- Create directories for each post in `posts_by_year/`
- Download and convert images to WebP format
- Clean HTML by removing Medium-specific attributes
- Update image links to reference local files
- Update internal links between posts
- Organize posts by year

### Output Format

The processed posts create a clean, self-contained archive that can be:
- **Browsed locally** - Each post is a standalone HTML file with local images
- **Organized by year** - Posts are automatically sorted into year directories
- **Cross-linked** - Internal links between posts work locally
- **Clean HTML** - Removed Medium-specific clutter and attributes
- **WebP images** - Optimized image format for better performance

This creates a complete local archive similar to the demo pages shown above.

### Output Structure

Each processed post will be in its own directory with the following structure:

```
posts_by_year/YYYY/YYYY-MM-DD_Post-Title/
├── index.html          # Cleaned HTML file
├── image01.webp        # Downloaded and converted images
├── image02.webp
└── ...
```

## How It Works

1. **HTML Parsing**: Uses BeautifulSoup to parse HTML and extract image URLs and internal links
2. **Directory Creation**: Creates clean directory names by removing UUID-like parts
3. **Image Download**: Downloads images from Medium's CDN with proper headers
4. **Format Conversion**: Converts images to WebP format using Pillow
5. **Sequential Naming**: Uses sequential naming for images (image01.webp, image02.webp, etc.)
6. **HTML Cleaning**: Removes unwanted Medium-specific attributes, classes, and elements
7. **Link Updates**: Updates HTML `<img>` tags and internal links to reference local files
8. **File Organization**: Creates individual directories for each post, organized by year

## Image Processing

The script handles image processing with the following features:

- **Download**: Downloads images from Medium's CDN with proper user agent headers
- **Conversion**: Converts all images to WebP format for better compression
- **Optimization**: Uses WebP compression with quality setting of 85
- **Sequential Naming**: Uses image01.webp, image02.webp, etc. for consistent organization
- **Error Handling**: Continues processing even if some images fail to download

## Configuration

The tool is now configurable to work with any Medium author. Each author can have their own configuration file.

### Configuration Files

Configuration files are stored as JSON and follow the naming convention `config_{author_username}.json`. For example:
- `config_julsimon.json` - Configuration for Julien Simon
- `config_other_author.json` - Configuration for another author

### Configuration Options

Each configuration file can specify:
- **Author Information**: Username, display name, Medium URL
- **Processing Settings**: Image quality, download delays, retry settings
- **HTML Cleaning**: Which attributes and classes to remove
- **Directories**: Input and output directory paths
- **Internal Links**: Patterns for detecting links between posts

### Creating New Configurations

Use the configuration creator:

```bash
# Basic configuration
python create_config.py other_author

# With custom settings
python create_config.py other_author --display-name "Other Author" --output-dir "other_posts"

# List existing configurations
python create_config.py --list
```

## HTML Cleaning

The script automatically cleans up unwanted Medium-specific elements:

- **Data Attributes**: Removes `data-image-id`, `data-width`, `data-height`, `data-href`, etc.
- **Medium Classes**: Removes Medium-specific CSS classes (`graf`, `markup--*`, etc.)
- **Unwanted Elements**: Removes `iframe`, `script`, and other non-essential elements
- **Clean Output**: Produces clean, semantic HTML without Medium-specific clutter

## Internal Link Processing

The script automatically detects and updates internal links between posts:

- **Detection**: Finds all links to `medium.com/@julsimon/` posts
- **Mapping**: Creates a mapping from Medium URLs to local file paths
- **Updates**: Replaces all internal links with relative paths to local files
- **Self-Contained**: Creates a fully local archive that works offline

## Rate Limiting

The script implements aggressive throttling to avoid being blocked by Medium's CDN:

- **Base Delay**: 3 seconds between image downloads
- **Exponential Backoff**: 60 seconds, then 120 seconds on HTTP 429 errors
- **Resume Capability**: Can resume processing from where it left off
- **Error Handling**: Continues processing even if some images fail

## Troubleshooting

### Rate Limiting Issues

If you encounter HTTP 429 (Too Many Requests) errors:

1. **Wait**: The script will automatically wait and retry
2. **Resume**: If interrupted, simply run the script again - it will resume from where it left off
3. **Manual Delay**: You can increase the delay in `process_posts.py` if needed

### Image Download Failures

Some images may fail to download due to:
- Network issues
- Rate limiting
- Invalid URLs

The script will log these failures and continue processing other images.

### Memory Issues

For large numbers of posts, the script processes them one at a time to minimize memory usage.

## Dependencies

### Required Dependencies
- **beautifulsoup4>=4.12.2**: HTML parsing and manipulation
- **Pillow>=10.0.1**: Image processing and WebP conversion
- **lxml>=4.9.3**: Fast XML/HTML parser for BeautifulSoup

### Python Version
- **Python 3.8+**: Required for type hints and pathlib features

### Installation
```bash
pip install -r requirements.txt
```

## Testing

The project includes a comprehensive test suite to ensure all functionality works correctly.

### Quick Tests
Run basic functionality tests (no network access required):
```bash
python test_basic.py
```

### Simple Tests
Run comprehensive tests without network calls:
```bash
python test_simple.py
```

### Full Test Suite
Run the complete test suite (includes mocked network tests):
```bash
python test_medium_processor.py
```

### Test Coverage
The test suite covers:
- ✅ Configuration management
- ✅ HTML processing and cleaning
- ✅ Image URL extraction
- ✅ Internal link detection
- ✅ Filename sanitization
- ✅ Image filename generation
- ✅ Post directory name creation
- ✅ Configuration loading and saving

## License

This project is part of the post-downloader repository.

## Contributing

Feel free to submit issues or pull requests to improve the tool.
