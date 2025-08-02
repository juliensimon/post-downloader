# Post Downloader

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/julsimon/post-downloader)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/julsimon/post-downloader)

A comprehensive toolset for downloading and archiving blog posts from various platforms. This project includes tools for processing Medium, AWS, and Hugging Face blog posts with image downloads, HTML cleaning, and local archiving.

## Demo

See the processed results in action:
- **[AWS Blog Posts](https://www.julien.org/aws-blog-posts.html)** - 68 AWS blog posts (2018-2021)
- **[Hugging Face Blog Posts](https://www.julien.org/huggingface-blog-posts.html)** - 25 Hugging Face blog posts (2021-2024)
- **[Medium Blog Posts](https://www.julien.org/medium-blog-posts.html)** - 25+ Medium blog posts (2015-2021)

These pages demonstrate the clean, organized output that this tool produces.

## Project Structure

```
post-downloader/
├── README.md                           # This documentation
├── extract_juliensimon_urls.py        # URL extraction utilities
├── extract_all_juliensimon_urls.py    # Comprehensive URL extraction
├── extract_single_medium_post.py      # Single Medium post extractor
├── requirements_simple.txt             # Dependencies for single post extractor
├── medium/                             # Medium posts processor
│   ├── README.md                      # Medium-specific documentation
│   ├── process_posts.py               # Main Medium processing script
│   ├── requirements.txt               # Python dependencies
│   ├── posts/                         # Original Medium HTML files
│   └── posts_by_year/                 # Processed posts organized by year
├── aws/                               # AWS blog processor
│   ├── README.md                      # AWS-specific documentation
│   ├── aws_blog_downloader.py         # AWS blog processing script
│   ├── requirements.txt               # Python dependencies
│   ├── aws-blog-urls.txt             # AWS blog URLs
│   └── downloads/                     # Processed AWS posts
└── huggingface/                       # Hugging Face blog processor
    ├── README.md                      # Hugging Face-specific documentation
    ├── huggingface_blog_downloader.py # Hugging Face blog processing script
    ├── requirements.txt               # Python dependencies
    ├── huggingface-blog-urls.txt     # Hugging Face blog URLs
    └── downloads/                     # Processed Hugging Face posts
```

## Features

### Single Medium Post Extractor
- **Real Date Conversion**: Converts relative dates ("2 days ago") to actual calendar dates
- **Content Cleaning**: Removes unwanted UI elements between subtitle and image
- **Clean Metadata**: Extracts title, author, real date, and source URL
- **Organized Filenames**: Uses date and title for better file organization
- **Rate Limiting**: Respectful delays to avoid being blocked
- **Error Handling**: Robust error handling with graceful fallbacks

### Medium Posts Processor (Batch)
- **Image Processing**: Downloads remote images and converts them to WebP format
- **HTML Cleaning**: Removes unwanted Medium-specific attributes and classes
- **Internal Link Processing**: Updates links between posts to reference local files
- **Year Organization**: Automatically organizes processed posts by year
- **Rate Limiting**: Implements aggressive throttling to avoid being blocked

### AWS Blog Processor
- **Comprehensive Download**: Downloads AWS blog posts with images
- **WebP Conversion**: Converts images to WebP format for better compression
- **Sequential Naming**: Uses sequential naming for images (image01.webp, etc.)
- **Error Handling**: Robust error handling with detailed logging

### Hugging Face Blog Processor
- **Blog Post Download**: Downloads Hugging Face blog posts
- **Image Processing**: Downloads and processes images from posts
- **Local Archiving**: Creates self-contained local archives

## Quick Start

### Single Medium Post Extraction

For extracting individual Medium posts with clean formatting:

1. **Install dependencies**:
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Extract a single post**:
   ```bash
   python extract_single_medium_post.py "https://medium.com/@username/post-url"
   ```

3. **Extract with custom output directory**:
   ```bash
   python extract_single_medium_post.py "https://medium.com/@username/post-url" --output-dir my_posts
   ```

**Features**:
- ✅ **Real Date Extraction**: Converts "2 days ago" to actual dates (e.g., "2025-07-31")
- ✅ **Content Cleaning**: Removes unwanted UI elements between subtitle and image
- ✅ **Clean Filenames**: Uses date and title for organized filenames
- ✅ **Metadata Extraction**: Title, author, date, and source URL
- ✅ **Rate Limiting**: Respectful delays to avoid being blocked

### Medium Posts (Batch Processing)

1. **Navigate to the medium directory**:
   ```bash
   cd medium
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Process all posts**:
   ```bash
   python process_posts.py
   ```

### AWS Blog Posts

1. **Navigate to the aws directory**:
   ```bash
   cd aws
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Process AWS blog posts**:
   ```bash
   python aws_blog_downloader.py
   ```

### Hugging Face Blog Posts

1. **Navigate to the huggingface directory**:
   ```bash
   cd huggingface
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Process Hugging Face blog posts**:
   ```bash
   python huggingface_blog_downloader.py
   ```

## URL Extraction

The project includes utilities for extracting URLs from various sources:

- **`extract_juliensimon_urls.py`**: Basic URL extraction from HTML files
- **`extract_all_juliensimon_urls.py`**: Comprehensive URL extraction with filtering

## Common Features Across All Processors

### Image Processing
- **Download**: Downloads images from various CDNs with proper headers
- **Conversion**: Converts images to WebP format for better compression
- **Sequential Naming**: Uses consistent naming (image01.webp, image02.webp, etc.)
- **Error Handling**: Continues processing even if some images fail

### HTML Processing
- **Cleaning**: Removes platform-specific attributes and classes
- **Link Updates**: Updates image and internal links to reference local files
- **Self-Contained**: Creates fully local archives that work offline

### Rate Limiting
- **Throttling**: Implements delays between downloads to avoid being blocked
- **Exponential Backoff**: Handles HTTP 429 errors with increasing delays
- **Resume Capability**: Can resume processing from where it left off

### Testing
- **Comprehensive Test Suites**: Each processor includes thorough testing
- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test end-to-end processing workflows
- **Mock Testing**: Network calls are mocked for reliable testing

## Output Structure

Each processor creates organized output directories:

```
processed_posts/
├── YYYY-MM-DD_Post-Title/
│   ├── index.html          # Cleaned HTML file
│   ├── image01.webp        # Downloaded and converted images
│   ├── image02.webp
│   └── ...
└── ...
```

## Demo Results

The tools in this project have been used to create clean, organized archives of blog posts:

- **[AWS Blog Posts](https://www.julien.org/aws-blog-posts.html)** - 68 AWS blog posts (2018-2021) processed with the AWS blog downloader
- **[Hugging Face Blog Posts](https://www.julien.org/huggingface-blog-posts.html)** - 25 Hugging Face blog posts (2021-2024) processed with the Hugging Face blog downloader
- **[Medium Blog Posts](https://www.julien.org/medium-blog-posts.html)** - 25+ Medium blog posts (2015-2021) processed with the Medium posts processor

These pages demonstrate the clean, organized output that these tools produce - self-contained archives with local images, clean HTML, and proper cross-linking between posts.

## Dependencies

### Common Dependencies
- **beautifulsoup4**: HTML parsing and manipulation
- **Pillow**: Image processing and WebP conversion
- **lxml**: Fast XML/HTML parser for BeautifulSoup

### Platform-Specific Dependencies
- **requests**: HTTP client for downloading content
- **urllib**: Alternative HTTP client for some processors

## Troubleshooting

### Rate Limiting Issues
- The scripts implement automatic throttling and retry logic
- If interrupted, simply run the script again - it will resume from where it left off
- You can adjust delay times in the scripts if needed

### Image Download Failures
- Some images may fail due to network issues or rate limiting
- The scripts log failures and continue processing other content
- Failed downloads don't stop the overall processing

### Memory Issues
- The scripts process content one at a time to minimize memory usage
- For very large archives, consider processing in smaller batches

## Code Quality

The project uses pre-commit hooks to ensure consistent code quality and formatting.

### Pre-commit Setup

Install and configure pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Or use the setup script
./setup_pre_commit.sh
```

### Pre-commit Hooks

The following hooks run automatically on every commit:

- **black**: Code formatting (Python)
- **isort**: Import sorting (Python)
- **trailing-whitespace**: Remove trailing whitespace
- **end-of-file-fixer**: Ensure files end with newline
- **check-yaml**: Validate YAML files
- **check-added-large-files**: Prevent large files (>1MB)
- **check-merge-conflict**: Prevent merge conflicts

### Manual Formatting

Run formatting manually:

```bash
# Format all files
pre-commit run --all-files

# Format specific files
pre-commit run black --files path/to/file.py
pre-commit run isort --files path/to/file.py
```

### Configuration

- **black**: 88 character line length, Python 3.8+ compatible
- **isort**: Black-compatible profile, organized imports
- **pyproject.toml**: Centralized configuration for all tools

## Testing

The project includes a comprehensive test suite to ensure all functionality works correctly.

### Quick Tests
Run basic functionality tests (no network access required):
```bash
cd medium
python test_basic.py
```

### Simple Tests
Run comprehensive tests without network calls:
```bash
cd medium
python test_simple.py
```

### Full Test Suite
Run the complete test suite (includes mocked network tests):
```bash
cd medium
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

## Contributing

Feel free to submit issues or pull requests to improve the tools. Each platform processor is designed to be extensible for other similar platforms.

## License

This project is provided as-is for educational and archival purposes. Please respect the terms of service of the platforms you're downloading content from.
