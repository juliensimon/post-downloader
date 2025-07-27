# Medium Posts Processor

This tool processes Medium blog posts by creating individual directories for each post, downloading remote images, converting them to WebP format, and updating the HTML to reference local images. It also updates internal links between posts to create a fully self-contained local archive.

## Features

- **Directory Creation**: Creates a separate directory for each Medium post
- **Clean Naming**: Removes UUID-like parts from directory names for cleaner organization
- **Image Download**: Downloads all remote images from Medium's CDN
- **WebP Conversion**: Converts all images to WebP format for better compression
- **Sequential Image Naming**: Uses sequential naming (image01.webp, image02.webp, etc.) like AWS blog downloader
- **Standardized File Names**: Renames HTML files to `index.html` for consistent structure
- **Link Updates**: Updates HTML files to reference local images instead of remote URLs
- **Internal Link Processing**: Updates links between posts to reference local files (two-pass approach)
- **HTML Cleaning**: Removes unwanted Medium-specific attributes, classes, and elements
- **Error Handling**: Robust error handling with detailed logging
- **Aggressive Throttling**: Implements 3-second delays and exponential backoff for rate limiting
- **Resume Capability**: Can resume processing from where it left off if interrupted

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation**:
   ```bash
   python process_posts.py --help
   ```

## Usage

### Basic Usage

Run the script from the `medium` directory:

```bash
cd medium
python process_posts.py
```

This will:
- Process all HTML files in the `posts/` directory
- Create a `processed_posts/` directory with individual post directories
- Download and convert all images to WebP format
- Update HTML files to reference local images
- Update internal links between posts to reference local files

### Two-Pass Processing

The script uses a two-pass approach:

1. **First Pass**: 
   - Creates directories for each post (removing UUID parts)
   - Downloads and converts images to WebP format
   - Updates image references in HTML files

2. **Second Pass**:
   - Scans all processed posts to create a mapping of Medium URLs to local files
   - Updates all internal links between posts to reference local files
   - Creates a fully self-contained local archive

### Directory Structure

After processing, your directory structure will look like:

```
medium/
├── posts/                           # Original HTML files
│   ├── 2017-05-19_post-title-uuid.html
│   └── ...
├── processed_posts/                 # Processed posts with local images
│   ├── 2017-05-19_post-title/      # Clean directory name (UUID removed)
│   │   ├── index.html              # Standardized HTML filename
│   │   ├── image01.webp            # Sequential image naming
│   │   └── image02.webp
│   └── ...
├── process_posts.py                 # Main processing script
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

### Custom Configuration

You can modify the script to change:

- **Input directory**: Change `posts_dir` in the `MediumPostProcessor` constructor
- **Output directory**: Change `output_dir` in the `MediumPostProcessor` constructor
- **Image quality**: Modify the `quality` parameter in the `image.save()` call (default: 85)
- **Download delay**: Adjust the `time.sleep()` value (default: 0.1 seconds)

## How It Works

1. **HTML Parsing**: Uses BeautifulSoup to parse HTML and extract image URLs and internal links
2. **Directory Creation**: Creates clean directory names by removing UUID-like parts
3. **Image Download**: Downloads images from Medium's CDN with proper headers
4. **Format Conversion**: Converts images to WebP format using Pillow
5. **Sequential Naming**: Uses sequential naming for images (image01.webp, image02.webp, etc.)
6. **HTML Cleaning**: Removes unwanted Medium-specific attributes, classes, and elements
7. **Link Updates**: Updates HTML `<img>` tags and internal links to reference local files
8. **File Organization**: Creates individual directories for each post

## Image Processing

- **Format Support**: Handles JPEG, PNG, GIF, and other common formats
- **Transparency**: Converts transparent images to white background for WebP compatibility
- **Optimization**: Uses WebP compression with quality setting of 85
- **Sequential Naming**: Uses image01.webp, image02.webp, etc. for consistent organization

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

## Error Handling

The script includes comprehensive error handling:

- **Download Failures**: Logs warnings for failed image downloads
- **Processing Errors**: Continues processing other posts if one fails
- **Invalid Images**: Skips images that can't be processed
- **File System Issues**: Handles permission and disk space issues gracefully
- **Link Mapping**: Handles missing or broken internal links gracefully

## Logging

The script provides detailed logging:

- **Info Level**: Progress updates and successful operations
- **Warning Level**: Non-critical issues (failed downloads, etc.)
- **Error Level**: Critical errors that prevent processing
- **Debug Level**: Detailed information for troubleshooting

## Performance Considerations

- **Download Rate**: Includes 3-second delays between downloads to avoid rate limiting
- **Rate Limiting**: Implements exponential backoff (60s, then 120s) for 429 errors
- **Memory Usage**: Processes images one at a time to minimize memory usage
- **Disk Space**: WebP conversion typically reduces file sizes by 25-50%
- **Two-Pass Processing**: Ensures all posts are processed before updating internal links
- **Resume Capability**: Skips already processed posts to allow resuming interrupted runs

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write permissions in the output directory
2. **Network Issues**: Check internet connection for image downloads
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Large Files**: Some posts may have many images; processing may take time
5. **Internal Links**: The two-pass approach ensures all internal links are properly updated

### Debug Mode

To see more detailed output, modify the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

## Example Output

```
2024-01-15 10:30:15,123 - INFO - Found 324 HTML files to process
2024-01-15 10:30:15,124 - INFO - === FIRST PASS: Processing posts and downloading images ===
2024-01-15 10:30:15,125 - INFO - Processing post 1/324: 2017-05-19_post-title-uuid.html
2024-01-15 10:30:15,126 - INFO - Found 8 images in 2017-05-19_post-title-uuid.html
2024-01-15 10:30:15,127 - INFO - Copied HTML to: processed_posts/2017-05-19_post-title/2017-05-19_post-title-uuid.html
2024-01-15 10:30:15,128 - INFO - Downloading: https://cdn-images-1.medium.com/max/2560/1*HFTl9S1HkefgZiFs3vv9Cw.jpeg
2024-01-15 10:30:16,234 - INFO - Saved as WebP: processed_posts/2017-05-19_post-title/image01.webp
2024-01-15 10:30:16,235 - INFO - Updated image link: https://cdn-images-1.medium.com/max/2560/1*HFTl9S1HkefgZiFs3vv9Cw.jpeg -> image01.webp
2024-01-15 10:30:20,456 - INFO - === SECOND PASS: Updating internal links ===
2024-01-15 10:30:20,457 - INFO - Creating link mapping...
2024-01-15 10:30:20,458 - INFO - Created mapping for 324 posts
2024-01-15 10:30:20,459 - INFO - Updated 5 internal links in 2017-05-19_post-title-uuid.html
```

## License

This script is provided as-is for processing Medium blog posts. Please respect Medium's terms of service and use responsibly. 