# Hugging Face Blog Downloader

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/julsimon/post-downloader)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/julsimon/post-downloader)

A Python tool for downloading and archiving Hugging Face blog posts with image processing, HTML cleaning, and local organization.

## Demo

See the processed results in action:
- **[Hugging Face Blog Posts](https://www.julien.org/huggingface-blog-posts.html)** - 25 Hugging Face blog posts (2021-2024)

This page demonstrates the clean, organized output that this tool produces.

## Features

- **Blog Post Download**: Downloads Hugging Face blog posts with all content
- **Image Processing**: Downloads and processes images from posts
- **WebP Conversion**: Converts images to WebP format for better compression
- **Sequential Naming**: Uses sequential naming for images (image01.webp, image02.webp, etc.)
- **HTML Cleaning**: Removes unwanted Hugging Face-specific attributes and classes
- **Local Archiving**: Creates self-contained local archives
- **Error Handling**: Robust error handling with detailed logging
- **Rate Limiting**: Implements throttling to avoid being blocked

## Project Structure

```
huggingface/
├── README.md                           # This documentation
├── huggingface_blog_downloader.py     # Main processing script
├── requirements.txt                    # Python dependencies
├── huggingface-blog-urls.txt          # Hugging Face blog URLs to process
├── source-posts.html                  # Source HTML file for URL extraction
└── downloads/                          # Processed posts organized by date
    ├── 2021-01-15_post-title-1/
    ├── 2021-02-20_post-title-2/
    └── ...
```

## Installation

1. **Navigate to the huggingface directory**:
   ```bash
   cd huggingface
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Process All Hugging Face Blog Posts

To process all Hugging Face blog posts listed in `huggingface-blog-urls.txt`:

```bash
python huggingface_blog_downloader.py
```

### Process Specific URLs

To process specific URLs, edit the `huggingface-blog-urls.txt` file and add the URLs you want to process:

```txt
https://huggingface.co/blog/post-title-1
https://huggingface.co/blog/post-title-2
```

### What the Processing Does

The script will:
- Download each Hugging Face blog post
- Extract all images from the post
- Download and convert images to WebP format
- Clean HTML by removing Hugging Face-specific attributes
- Update image links to reference local files
- Create organized directories for each post
- Save cleaned HTML as `index.html`

### Output Format

Each processed post will be in its own directory with the following structure:

```
downloads/YYYY-MM-DD_Post-Title/
├── index.html          # Cleaned HTML file
├── image01.webp        # Downloaded and converted images
├── image02.webp
└── ...
```

## How It Works

1. **URL Processing**: Reads URLs from `huggingface-blog-urls.txt`
2. **HTML Download**: Downloads each blog post using requests
3. **Image Extraction**: Finds all images in the HTML content
4. **Image Download**: Downloads images from Hugging Face CDN
5. **Format Conversion**: Converts images to WebP format using Pillow
6. **Sequential Naming**: Uses image01.webp, image02.webp, etc.
7. **HTML Cleaning**: Removes unwanted Hugging Face-specific attributes
8. **Link Updates**: Updates HTML to reference local images
9. **File Organization**: Creates individual directories for each post

## Image Processing

The script handles image processing with the following features:

- **Download**: Downloads images from Hugging Face CDN with proper headers
- **Conversion**: Converts all images to WebP format for better compression
- **Optimization**: Uses WebP compression with quality setting
- **Sequential Naming**: Uses image01.webp, image02.webp, etc. for consistent organization
- **Error Handling**: Continues processing even if some images fail to download

## HTML Cleaning

The script automatically cleans up unwanted Hugging Face-specific elements:

- **Data Attributes**: Removes Hugging Face-specific data attributes
- **CSS Classes**: Removes unnecessary CSS classes
- **Clean Output**: Produces clean, semantic HTML without Hugging Face-specific clutter

## Rate Limiting

The script implements throttling to avoid being blocked by Hugging Face servers:

- **Base Delay**: Delay between downloads to avoid overwhelming servers
- **Error Handling**: Handles HTTP errors gracefully
- **Resume Capability**: Can resume processing from where it left off

## Troubleshooting

### Rate Limiting Issues

If you encounter HTTP 429 (Too Many Requests) errors:

1. **Wait**: The script will automatically wait and retry
2. **Resume**: If interrupted, simply run the script again - it will resume from where it left off
3. **Manual Delay**: You can increase the delay in the script if needed

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
- **requests>=2.28.0**: HTTP client for downloading content
- **beautifulsoup4>=4.11.0**: HTML parsing and manipulation
- **Pillow>=9.0.0**: Image processing and WebP conversion
- **lxml>=4.9.0**: Fast XML/HTML parser for BeautifulSoup

### Python Version
- **Python 3.8+**: Required for type hints and pathlib features

### Installation
```bash
pip install -r requirements.txt
```

## Configuration

The script uses a simple configuration approach:

- **URLs**: Edit `huggingface-blog-urls.txt` to specify which posts to download
- **Image Quality**: Adjustable in the script (default: 85)
- **Download Delay**: Configurable delay between downloads
- **Output Directory**: Defaults to `downloads/`

## Example Output

After processing, you'll have a clean, organized archive:

```
downloads/
├── 2021-01-15_post-title-1/
│   ├── index.html
│   ├── image01.webp
│   └── image02.webp
├── 2021-02-20_post-title-2/
│   ├── index.html
│   ├── image01.webp
│   ├── image02.webp
│   └── image03.webp
└── ...
```

Each directory contains:
- **index.html**: Clean, self-contained HTML file
- **image*.webp**: Downloaded and converted images
- **Local links**: All image references point to local files

## License

This project is part of the post-downloader repository and is provided as-is for educational and archival purposes.

## Contributing

Feel free to submit issues or pull requests to improve the Hugging Face blog downloader.
