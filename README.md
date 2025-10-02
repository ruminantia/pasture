# Graze - Reddit/Web Content Scraper with Scheduled Scraping

The graze component is responsible for scraping content from Reddit and external websites. It fetches posts from specified subreddits, filters them based on configurable criteria, processes the external content into clean Markdown format, and can run continuously with scheduled scraping intervals.

## Features

- **Reddit API Integration**: Fetches posts from subreddit JSON feeds
- **Content Filtering**: Filters out stickied posts, self-posts, and posts containing blacklisted terms
- **Web Scraping**: Uses Selenium with headless Firefox to scrape external URLs
- **HTML Processing**: Cleans HTML content by removing unwanted tags and attributes
- **Markdown Conversion**: Converts processed HTML to clean Markdown format
- **Duplicate Detection**: Maintains history of processed URLs to avoid duplicates
- **Scheduled Scraping**: Runs continuously with configurable intervals per subreddit

## Installation

### Prerequisites
- Python 3.11+
- Firefox browser
- GeckoDriver (automatically managed by webdriver-manager)

### Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.ini` to configure which subreddits to monitor:

```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = Trump, Israel, Hamas, Palestine, Iran, Qatar, Russia, Ukraine
remove_tags = -nav, -footer  # Keep nav and footer tags for this subreddit

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = AI, ChatGPT, OpenAI, Microsoft, Google
remove_tags = header, aside, form  # Add additional tags to remove

[custom_site]
url = https://www.reddit.com/domain/example.com.json
blacklist = test, demo
# No remove_tags specified - uses only global tags
```

### Configuration Options
- **Section Name**: Arbitrary identifier for the subreddit
- **url**: The JSON endpoint of the subreddit (must end with `.json`)
- **blacklist**: Comma-separated list of terms to exclude (case-insensitive)
- **remove_tags**: Comma-separated list of HTML tags to remove during processing
- **interval**: Scraping interval in minutes (optional, defaults to 60 minutes)

### Tag Removal Configuration

Graze supports flexible HTML tag removal with Gentoo-style override syntax:

#### Global Tags
Add a `[global]` section to define tags that will be removed from all scraped sites:
```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav
```

#### Section-Specific Tags
Add tags to individual sections to modify the global behavior:
```ini
[worldnews]
remove_tags = header, aside, form  # Add tags to global set

[arstechnica]
remove_tags = -nav, -footer  # Remove tags from global set (keep these)

[technews]
remove_tags = -nav, header, aside  # Keep nav, add header and aside
```

#### Override Syntax
- **No prefix**: Add tag to removal list (e.g., `header`, `aside`)
- **`-` prefix**: Remove tag from global list (e.g., `-nav`, `-footer`)
- **No `remove_tags`**: Use only global tags (if defined)
- **No `[global]` section**: Each section uses only its own tags

### Configuration Examples

#### Example 1: Basic Global Configuration
```ini
[global]
remove_tags = script, style, noscript, iframe

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = AI, cryptocurrency
interval = 120
```
- **worldnews**: Removes `script, style, noscript, iframe`, scrapes every 60 minutes (default)
- **technology**: Removes `script, style, noscript, iframe`, scrapes every 120 minutes

#### Example 2: Global + Section Additions
```ini
[global]
remove_tags = script, style, noscript, iframe

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
remove_tags = button, svg, footer
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = AI, cryptocurrency
remove_tags = header, aside, form
interval = 60
```
- **worldnews**: Removes `script, style, noscript, iframe, button, svg, footer`, scrapes every 30 minutes
- **technology**: Removes `script, style, noscript, iframe, header, aside, form`, scrapes every 60 minutes

#### Example 3: Global + Section Overrides
```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
remove_tags = -nav, -footer  # Keep nav and footer
interval = 15

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = AI, cryptocurrency
remove_tags = -nav, header, aside  # Keep nav, add header and aside
interval = 45
```
- **worldnews**: Removes `script, style, noscript, iframe, button, svg` (keeps `nav, footer`), scrapes every 15 minutes
- **technology**: Removes `script, style, noscript, iframe, button, svg, footer, header, aside` (keeps `nav`), scrapes every 45 minutes

#### Example 4: No Global Section
```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
remove_tags = script, style, noscript
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = AI, cryptocurrency
# No remove_tags - uses default tags
interval = 60
```
- **worldnews**: Removes only `script, style, noscript`, scrapes every 30 minutes
- **technology**: Removes default tags `script, style, noscript, iframe, button, svg, footer, nav`, scrapes every 60 minutes

## Usage

### Running Graze
```bash
# Single run (for testing)
python src/main.py

# Continuous mode with scheduled scraping (production)
# The application automatically detects interval configuration and runs continuously
python src/main.py
```

### Output Structure
```
output/
├── year-month-day/
│   ├── worldnews/
│   │   ├── abc123def456.md
│   │   └── xyz789uvw012.md
│   └── technology/
│       └── def456ghi789.md
└── processed_urls.json
```

Each scraped URL is stored as a Markdown file with a SHA256 hash of the URL as the filename.

## How It Works

1. **Subreddit Fetching**: Retrieves posts from configured subreddit JSON feeds
2. **Content Filtering**: Removes stickied posts, self-posts, and posts containing blacklisted terms
3. **URL Processing**: Checks if URL has been processed before to avoid duplicates
4. **Web Scraping**: Uses headless Firefox via Selenium to fetch external content
5. **HTML Cleaning**: Removes scripts, styles, and unwanted tags while preserving links and images
6. **Markdown Conversion**: Converts cleaned HTML to Markdown format
7. **Storage**: Saves processed content with URL hash as filename
8. **Scheduled Execution**: Automatically re-scrapes subreddits at configured intervals (if specified)

## HTML Processing

Graze performs extensive HTML cleaning with configurable tag removal:

#### Default Tag Removal
If no configuration is specified, the following tags are removed:
- `script`, `style`, `noscript`, `iframe`, `button`, `svg`, `footer`, `nav`

#### Configurable Tag Removal
You can customize which tags are removed using the `remove_tags` configuration option:
- **Global configuration**: Applies to all scraped sites
- **Per-section configuration**: Modifies global behavior for specific sites
- **Gentoo-style syntax**: Use `-` prefix to keep specific tags

#### HTML Processing Features
- **Preserved Attributes**: Only `href` (for links) and `src` (for images) are kept
- **Link Processing**: External URLs are converted to relative paths
- **Image Processing**: Image filenames are extracted from URLs
- **Duplicate Prevention**: Global and section tags are combined without duplicates

## Dependencies

- **requests**: HTTP requests for Reddit API
- **selenium**: Web browser automation
- **webdriver-manager**: GeckoDriver management
- **beautifulsoup4**: HTML parsing and manipulation
- **markdownify**: HTML to Markdown conversion
- **schedule**: Task scheduling for interval-based scraping

## Error Handling

Comprehensive error handling for:
- Network timeouts and connection errors
- Invalid JSON responses from Reddit
- Web scraping failures
- File I/O operations

## Development

### Project Structure
```
graze/
├── src/
│   └── main.py          # Main application logic
├── tests/               # Unit tests
├── config.ini          # Configuration file
├── requirements.txt    # Python dependencies
└── Dockerfile          # Container configuration
```

### Running Tests
```bash
python -m pytest tests/
```

## Docker Support

### Using the Management Script

The project includes a convenient `run-docker.sh` script for managing the scraper. The script automatically detects and uses Docker Compose when available:

```bash
# Make the script executable (first time only)
chmod +x run-docker.sh

# Run the scraper once (for testing)
./run-docker.sh

# Start the scraper in background mode (recommended for production)
./run-docker.sh start

# View logs of running container
./run-docker.sh logs

# Stop the background container
./run-docker.sh stop

# Rebuild the Docker image
./run-docker.sh build

# Show container status
./run-docker.sh status

# Show help with all available commands
./run-docker.sh help
```

### Using Docker Compose

The project includes a `docker-compose.yml` file for container orchestration:

```bash
# Build and start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Run once (single execution)
docker compose run --rm -T graze-scraper

# Build images
docker compose build
```

### Manual Docker Commands

If you prefer to use Docker commands directly:

```bash
# Build the image
docker build -t graze .

# Run once with mounted volumes (single execution)
docker run --rm \
  -v $(pwd)/config.ini:/app/config.ini \
  -v $(pwd)/output:/app/output \
  graze

# Run in background (continuous mode with scheduled scraping)
docker run -d \
  --name graze-scraper \
  -v $(pwd)/config.ini:/app/config.ini \
  -v $(pwd)/output:/app/output \
  graze
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation accordingly
4. Ensure error handling is comprehensive

## License

This project is provided as-is without warranty. Use responsibly and in compliance with website terms of service.

## Disclaimer

This tool is intended for educational and research purposes. Users are responsible for:
- Complying with Reddit's API terms of service
- Respecting website robots.txt files
- Obtaining proper permissions for web scraping
- Using the tool ethically and legally
