# Blog Post Downloader

A Python CLI tool that downloads blog posts from URLs, automatically extracts titles and dates, downloads and converts images to WebP format, and creates self-contained offline-readable HTML files.

## Features

- 🔗 **URL-Based Input**: Works with simple text files containing URLs (one per line)
- 🏷️ **Auto-Metadata**: Automatically extracts titles and publication dates from HTML
- 📄 **Content Extraction**: Extracts main blog post content, filtering out navigation and peripheral elements
- 🖼️ **Image Processing**: Downloads all images and converts them to optimized WebP format
- 🔗 **Link Rewriting**: Rewrites image references to local paths for offline viewing
- 🎨 **Basic Styling**: Applies clean, readable CSS styling to extracted content
- 📁 **Organized Output**: Creates dated folders with descriptive names
- 🔊 **Content Cleanup**: Removes Amazon Polly audio content and branding
- 📍 **Source Attribution**: Adds "originally published at" links to source material
- ✅ **Sanity Checks**: Validates downloads with comprehensive quality checks

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `requests` - HTTP requests for downloading content
- `beautifulsoup4` - HTML parsing and manipulation
- `Pillow` - Image processing and WebP conversion
- `lxml` - Fast XML/HTML parser backend

## Usage

### Basic Usage

Download the first 3 posts from URLs file (default):
```bash
python aws_blog_downloader.py
```

### Command Line Options

```bash
python aws_blog_downloader.py [OPTIONS]
```

**Options:**
- `--urls PATH` - Path to text file with URLs (default: `aws-blog-urls.txt`)
- `--output DIR` - Output directory for downloads (default: `downloads`)
- `--limit N` - Number of posts to download (default: 3)
- `--start N` - Starting index in the file (default: 0)

### Examples

```bash
# Download first 5 posts
python aws_blog_downloader.py --limit 5

# Download posts 10-15 to custom directory
python aws_blog_downloader.py --start 10 --limit 5 --output my_downloads

# Use custom URLs file
python aws_blog_downloader.py --urls my_urls.txt --limit 10
```

## Input Format

Create a text file with URLs, one per line:

```
# Blog Post URLs - lines starting with # are ignored
https://example.com/blog/post-1/
https://example.com/blog/post-2/
https://example.com/blog/post-3/
```

The tool automatically extracts:
- **Title** from HTML meta tags or page title
- **Publication date** from meta tags or URL patterns
- **Content** from the main article section

## Output Structure

For each blog post, the tool creates:

```
downloads/
└── 2021-09-22_post-title-with-dashes/
    ├── index.html          # Main content with styling
    ├── metadata.json       # Post metadata and download info
    ├── image01.webp        # Downloaded WebP images
    └── image02.webp        # Sequential naming
```

### Generated HTML Structure

Each `index.html` contains:
- Post title as H1
- Publication date
- "Originally published at" link
- Main article content with local image references
- Embedded CSS for clean presentation

## Technical Details

### Content Extraction

The tool uses multiple CSS selectors to identify main content:
1. `section.blog-post-content` (AWS blog-specific)
2. `.blog-post-content`
3. `main article`
4. Fallback heuristics based on content length

### Image Processing Pipeline

1. **Discovery**: Finds all `<img>` tags in extracted content
2. **Download**: Fetches images with proper User-Agent headers
3. **Conversion**: Converts to WebP format (85% quality, optimized)
4. **Sequential Naming**: Names images as `image01.webp`, `image02.webp`, etc.
5. **Link Rewriting**: Updates `src` attributes to local filenames
6. **Cleanup**: Removes external link wrappers and `srcset` attributes

### Content Cleanup

- Removes Amazon Polly audio players and branding
- Filters out navigation elements and sidebars
- Strips AWS-specific peripheral content
- Maintains article structure and formatting

### CSS Styling

Applies responsive, clean styling including:
- Modern font stack (system fonts)
- Readable typography (1.6 line height)
- Responsive images with shadows
- Syntax highlighting for code blocks
- Proper spacing and hierarchy

### Sanity Checks

After each download, the tool performs comprehensive validation:
- **File Existence**: Verifies HTML, metadata, and image files are created
- **Content Validation**: Checks HTML contains post title and source attribution
- **Image Integrity**: Validates WebP format and file sizes
- **Reference Consistency**: Ensures HTML image references match downloaded files
- **Sequential Naming**: Verifies complete image sequence (image01.webp, image02.webp, etc.)
- **Metadata Completeness**: Confirms all required metadata fields are present

## Configuration

### User-Agent

The tool uses a standard browser User-Agent to ensure successful downloads:
```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
```

### Request Settings

- Timeout: 30 seconds per request
- Delay: 2 seconds between posts (respectful crawling)
- Session reuse for connection pooling

### Image Processing

- Format: WebP
- Quality: 85%
- Optimization: Enabled
- Color mode: RGB (RGBA/LA converted automatically)

## Error Handling

The tool includes robust error handling:
- Network timeouts and connection errors
- Invalid image formats
- Missing content selectors
- File system permissions

Failed downloads are logged but don't stop the overall process.

## Performance

- **Parallel Processing**: Images downloaded sequentially per post
- **Memory Efficient**: Streams image data, doesn't load entire files
- **Storage Optimized**: WebP typically 25-50% smaller than original formats
- **Respectful**: 2-second delays between requests

## Troubleshooting

### Common Issues

**"No content found"**: The blog structure may have changed. Check CSS selectors in `extract_main_content()`.

**Image download failures**: Usually network issues or changed URLs. Check connectivity and try again.

**Permission errors**: Ensure write permissions in the output directory.

### Debug Mode

Add debug prints by modifying the logging level in the script.

## Contributing

To modify content extraction:
1. Update CSS selectors in `extract_main_content()`
2. Test with various blog post URLs
3. Ensure compatibility with different AWS blog formats

## License

This tool is for educational and personal use. Respect AWS Terms of Service and robots.txt when using.

## Dependencies

See `requirements.txt` for exact versions:
- `requests>=2.28.0`
- `beautifulsoup4>=4.11.0`
- `Pillow>=9.0.0`
- `lxml>=4.9.0` 