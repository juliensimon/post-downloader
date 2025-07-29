# Arcee Blog Downloader

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/julsimon/post-downloader)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](https://github.com/julsimon/post-downloader)

A Python tool for downloading and archiving Arcee blog posts with image processing, HTML cleaning, and local organization.

## Features

- **Comprehensive Download**: Downloads Arcee blog posts with all associated images
- **WebP Conversion**: Converts images to WebP format for better compression
- **Sequential Naming**: Uses sequential naming for images (image01.webp, image02.webp, etc.)
- **HTML Cleaning**: Removes unwanted Arcee-specific attributes and classes
- **Error Handling**: Robust error handling with detailed logging
- **Rate Limiting**: Implements throttling to avoid being blocked
- **Resume Capability**: Can resume processing from where it left off

## Project Structure

```
arcee/
├── README.md                    # This documentation
├── arcee_blog_downloader.py    # Main processing script
├── requirements.txt             # Python dependencies
├── arcee-blog-urls.txt         # Arcee blog URLs to process
└── downloads/                   # Processed posts organized by date
    ├── 2025-04-17_the-case-for-small-language-model-inference-on-arm-cpus/
    ├── 2025-05-27_arcee-ai-small-language-models-on-together-ai-and-openrouter/
    └── ...
```

## Installation

1. **Navigate to the arcee directory**:
   ```bash
   cd arcee
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Process All Arcee Blog Posts

To process all Arcee blog posts listed in `arcee-blog-urls.txt`:

```bash
python arcee_blog_downloader.py
```

### Process Specific URLs

To process specific URLs, edit the `arcee-blog-urls.txt` file and add the URLs you want to process:

```txt
https://www.arcee.ai/blog/the-case-for-small-language-model-inference-on-arm-cpus
https://www.arcee.ai/blog/arcee-ai-small-language-models-on-together-ai-and-openrouter
```

### Command Line Options

```bash
python arcee_blog_downloader.py [OPTIONS]

Options:
  --urls TEXT     Path to text file with blog post URLs (default: arcee-blog-urls.txt)
  --output TEXT   Output directory for downloaded posts (default: downloads)
  --limit INT     Number of posts to download (default: 3)
  --start INT     Starting index (default: 0)
```

### What the Processing Does

The script will:
- Download each Arcee blog post
- Extract all images from the post
- Download and convert images to WebP format
- Clean HTML by removing Arcee-specific attributes
- Update image links to reference local files
- Create organized directories for each post
- Save cleaned HTML as `index.html`

### Output Format

Each processed post will be in its own directory with the following structure:

```
downloads/YYYY-MM-DD_Post-Title/
├── index.html          # Cleaned HTML file
├── metadata.json       # Post metadata
├── image01.webp        # Downloaded and converted images
├── image02.webp
└── ...
```

## How It Works

1. **URL Processing**: Reads URLs from `arcee-blog-urls.txt`
2. **HTML Download**: Downloads each blog post using requests
3. **Image Extraction**: Finds all images in the HTML content
4. **Image Download**: Downloads images from Arcee CDN
5. **WebP Conversion**: Converts images to WebP format for better compression
6. **HTML Cleaning**: Removes Arcee-specific content and branding
7. **Local Organization**: Creates organized directory structure
8. **Metadata Storage**: Saves post metadata in JSON format

## Content Extraction

The script specifically targets Arcee's blog structure:

- **Main Content**: Extracts content from `section.blog_body .richtext`
- **Title**: Extracts from meta tags and H1 elements
- **Date**: Extracts from meta tags or falls back to URL parsing
- **Images**: Downloads and converts all images to WebP format

## Content Cleaning

The script removes Arcee-specific elements:

- Blog CTA sections (`blog-cta`)
- Tip sections (`blog-tip`)
- Break lines (`break-line`)
- Arcee branding images
- Navigation and sidebar elements

## Error Handling

The script includes comprehensive error handling:

- **404 Detection**: Skips posts that return 404 errors
- **Image Download Failures**: Continues processing even if some images fail
- **Rate Limiting**: Includes delays between requests
- **Sanity Checks**: Validates downloaded content
- **Resume Capability**: Can restart from any point

## Dependencies

- `requests>=2.28.0` - HTTP requests
- `beautifulsoup4>=4.11.0` - HTML parsing
- `Pillow>=9.0.0` - Image processing
- `lxml>=4.9.0` - XML/HTML parser

## Examples

### Download First 3 Posts

```bash
python arcee_blog_downloader.py --limit 3
```

### Download Posts Starting from Index 5

```bash
python arcee_blog_downloader.py --start 5 --limit 2
```

### Custom Output Directory

```bash
python arcee_blog_downloader.py --output my-downloads
```

### Custom URLs File

```bash
python arcee_blog_downloader.py --urls my-urls.txt
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure you have write permissions to the output directory
2. **Network Timeouts**: The script includes timeouts, but you may need to adjust for slow connections
3. **Image Download Failures**: Some images may be protected or unavailable
4. **HTML Parsing Issues**: If the blog structure changes, the selectors may need updating

### Debug Mode

To see more detailed output, you can modify the script to include debug logging.

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License.
