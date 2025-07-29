# URL Extraction Utilities

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/julsimon/post-downloader)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/julsimon/post-downloader)

Utility scripts for extracting URLs from various sources to prepare for blog post downloading and archiving.

## Overview

This project includes two main URL extraction utilities:

- **`extract_juliensimon_urls.py`**: Basic URL extraction from HTML files
- **`extract_all_juliensimon_urls.py`**: Comprehensive URL extraction with filtering

## Scripts

### Basic URL Extraction

**File**: `extract_juliensimon_urls.py`

A simple script for extracting URLs from HTML files containing blog post listings.

#### Features
- Extracts URLs from HTML files
- Filters for specific domains (Medium, AWS, Hugging Face)
- Outputs clean URL lists
- Handles various HTML structures

#### Usage
```bash
python extract_juliensimon_urls.py
```

#### Input
Expects HTML files in the current directory or specified path containing blog post listings.

#### Output
Creates `extracted_urls.txt` with one URL per line.

### Comprehensive URL Extraction

**File**: `extract_all_juliensimon_urls.py`

A comprehensive script that extracts URLs from multiple sources and creates organized output files.

#### Features
- Extracts URLs from multiple HTML sources
- Filters by platform (Medium, AWS, Hugging Face)
- Creates platform-specific output files
- Handles various HTML structures and formats
- Comprehensive error handling

#### Usage
```bash
python extract_all_juliensimon_urls.py
```

#### Input Sources
- HTML files containing blog post listings
- Various blog platform structures
- Multiple author pages and archives

#### Output Files
- `medium_urls.txt`: Medium blog post URLs
- `aws_urls.txt`: AWS blog post URLs
- `huggingface_urls.txt`: Hugging Face blog post URLs
- `all_extracted_urls.txt`: Combined URL list

## How It Works

### URL Extraction Process

1. **HTML Parsing**: Uses BeautifulSoup to parse HTML files
2. **Link Discovery**: Finds all `<a>` tags with `href` attributes
3. **URL Filtering**: Filters URLs by domain and pattern matching
4. **Deduplication**: Removes duplicate URLs
5. **Validation**: Ensures URLs are valid and accessible
6. **Output**: Creates organized text files

### Platform-Specific Filtering

#### Medium URLs
- Domain: `medium.com`
- Pattern: `https://medium.com/@julsimon/*`
- Filters: Blog posts, articles, excludes comments and user pages

#### AWS URLs
- Domain: `aws.amazon.com`
- Pattern: `https://aws.amazon.com/blogs/*`
- Filters: Blog posts, excludes documentation and marketing pages

#### Hugging Face URLs
- Domain: `huggingface.co`
- Pattern: `https://huggingface.co/blog/*`
- Filters: Blog posts, excludes model pages and documentation

## Usage Examples

### Extract Medium URLs Only
```bash
python extract_juliensimon_urls.py --platform medium
```

### Extract All URLs with Filtering
```bash
python extract_all_juliensimon_urls.py --output-dir urls/
```

### Custom Input File
```bash
python extract_juliensimon_urls.py --input my_blog_list.html
```

## Output Format

### URL List Format
Each output file contains URLs, one per line:

```txt
https://medium.com/@julsimon/post-title-1
https://medium.com/@julsimon/post-title-2
https://aws.amazon.com/blogs/machine-learning/post-title
https://huggingface.co/blog/post-title
```

### File Organization
```
project_root/
├── medium_urls.txt           # Medium blog URLs
├── aws_urls.txt             # AWS blog URLs
├── huggingface_urls.txt     # Hugging Face blog URLs
└── all_extracted_urls.txt   # Combined URL list
```

## Configuration

### Filtering Options
- **Platform filtering**: Extract URLs for specific platforms
- **Date filtering**: Filter by publication date ranges
- **Pattern matching**: Custom regex patterns for URL filtering
- **Output organization**: Separate files by platform

### Error Handling
- **Invalid URLs**: Logs and skips invalid URLs
- **Network errors**: Handles connection timeouts gracefully
- **File errors**: Continues processing if individual files fail
- **Duplicate detection**: Removes duplicate URLs automatically

## Dependencies

### Required Dependencies
- **beautifulsoup4**: HTML parsing and manipulation
- **lxml**: Fast XML/HTML parser for BeautifulSoup
- **urllib**: URL validation and processing

### Python Version
- **Python 3.8+**: Required for type hints and pathlib features

## Integration

These utilities are designed to work with the blog post downloaders:

1. **Extract URLs**: Use these scripts to create URL lists
2. **Copy to Downloaders**: Copy URL files to respective downloader directories
3. **Process Posts**: Use the downloaders to process the extracted URLs

### Example Workflow
```bash
# 1. Extract URLs
python extract_all_juliensimon_urls.py

# 2. Copy to Medium processor
cp medium_urls.txt medium/posts/

# 3. Process Medium posts
cd medium
python process_posts.py
```

## Troubleshooting

### Common Issues

**No URLs Found**
- Check input HTML file structure
- Verify URL patterns match expected format
- Ensure HTML contains proper `<a>` tags

**Invalid URLs**
- Script logs invalid URLs for review
- Check URL format and accessibility
- Verify domain filtering settings

**File Permissions**
- Ensure write permissions in output directory
- Check file paths and directory structure

## License

This project is part of the post-downloader repository and is provided as-is for educational and archival purposes.

## Contributing

Feel free to submit issues or pull requests to improve the URL extraction utilities.
