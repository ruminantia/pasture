# Pasture - Multi-Source Content Scraper with Scheduled Scraping

The Pasture component is responsible for scraping content from multiple sources (pastures) including Reddit, HackerNews, and other websites. It fetches posts from configured sources, filters them based on configurable criteria, processes the external content into clean Markdown format, and can run continuously with scheduled scraping intervals.

## Features

- **Multi-Source Support**: Modular architecture supporting Reddit, HackerNews, and custom sources
- **Content Filtering**: Filters out unwanted posts and posts containing blacklisted terms
- **Web Scraping**: Uses Selenium with headless Firefox to scrape external URLs
- **HTML Processing**: Cleans HTML content by removing unwanted tags and attributes
- **Markdown Conversion**: Converts processed HTML to clean Markdown format
- **Duplicate Detection**: Maintains history of processed URLs to avoid duplicates
- **Scheduled Scraping**: Runs continuously with configurable intervals per pasture
- **Extensible Architecture**: Easy to add new pasture types

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

Edit `config.ini` to configure which pastures to monitor:

```ini
[global]
# Global settings apply to all pastures unless overridden
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

# Pasture configuration examples
# Each pasture section represents a source to scrape
# Supported types: reddit, hackernews, etc.

[worldnews]
# Reddit pasture (auto-detected from URL)
type = reddit
url = https://www.reddit.com/r/worldnews.json
blacklist = Trump, Netanyahu, Israel, Hamas, Palestine, Palestinian, Iran, Qatar, Russia, Ukraine
interval = 30

[arstechnica]
# Reddit pasture with custom tag removal
type = reddit
url = https://www.reddit.com/domain/arstechnica.com.json
blacklist = Trump, COVID, government
remove_tags = -nav, -footer
interval = 60

[LocalLLaMA]
# Reddit pasture with no blacklist
type = reddit
url = https://www.reddit.com/r/LocalLLaMA.json
blacklist =
interval = 120

# HackerNews pasture (working implementation)
[hackernews_top]
type = hackernews
# URL is optional for HackerNews - uses default API if not provided
# url = https://hacker-news.firebaseio.com/v0/topstories.json
blacklist = cryptocurrency, bitcoin, ethereum
interval = 60

# Example custom pasture (commented out for future use)
# [tech_blog]
# type = custom
# url = https://example.com/tech-feed.json
# blacklist = sponsored, advertisement
# interval = 120
```

### Configuration Options
- **Section Name**: Arbitrary identifier for the pasture
- **type**: Pasture type (reddit, hackernews, etc.) - auto-detected if not specified
- **url**: The source URL or API endpoint (optional for HackerNews)
- **blacklist**: Comma-separated list of terms to exclude (case-insensitive)
- **remove_tags**: Comma-separated list of HTML tags to remove during processing
- **interval**: Scraping interval in minutes (optional, defaults to 60 minutes)

### Tag Removal Configuration

Pasture supports flexible HTML tag removal with Gentoo-style override syntax:

#### Global Tags
Add a `[global]` section to define tags that will be removed from all scraped sites:
```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav
```

#### Pasture-Specific Tags
Add tags to individual pastures to modify the global behavior:
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
- **No `[global]` section**: Each pasture uses only its own tags

## Usage

### Running Pasture
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
│   └── arstechnica/
│       └── def456ghi789.md
└── processed_urls.json
```

Each scraped URL is stored as a Markdown file with a SHA256 hash of the URL as the filename.

## Architecture

The project uses a modular architecture with the following structure:

```
pasture/
├── src/
│   ├── pastures/           # Pasture implementations
│   │   ├── base/          # Base Pasture abstract class
│   │   ├── reddit/        # Reddit pasture implementation
│   │   ├── hackernews/    # HackerNews pasture implementation
│   │   └── __init__.py    # Pasture factory
│   ├── core/              # Core utilities
│   │   └── scraper.py     # Shared scraping functions
│   └── main.py            # Main application logic
├── config.ini             # Configuration file
├── requirements.txt       # Python dependencies
└── Dockerfile            # Container configuration
```

### Adding New Pasture Types

To add a new pasture type:

1. Create a new directory under `src/pastures/` (e.g., `src/pastures/custom/`)
2. Implement a class that inherits from `Pasture` base class
3. Register the new type in the PastureFactory

Example implementation:

```python
from typing import List, Dict, Any
from ..base import Pasture

class CustomPasture(Pasture):
    def fetch_posts(self) -> List[Dict[str, Any]]:
        # Implement fetching logic
        pass

    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Implement filtering logic
        pass

    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        # Extract URL from post
        pass
```

Register in `src/pastures/__init__.py`:

```python
from .custom import CustomPasture

class PastureFactory:
    _pasture_types = {
        "reddit": RedditPasture,
        "hackernews": HackerNewsPasture,
        "custom": CustomPasture,  # Add new type
    }
```

## How It Works

1. **Pasture Detection**: Determines pasture type from configuration or URL patterns
2. **Content Fetching**: Retrieves posts from configured sources using pasture-specific logic
3. **Content Filtering**: Removes unwanted posts based on pasture-specific criteria
4. **URL Processing**: Checks if URL has been processed before to avoid duplicates
5. **Web Scraping**: Uses headless Firefox via Selenium to fetch external content
6. **HTML Cleaning**: Removes scripts, styles, and unwanted tags while preserving links and images
7. **Markdown Conversion**: Converts cleaned HTML to Markdown format
8. **Storage**: Saves processed content with URL hash as filename
9. **Scheduled Execution**: Automatically re-scrapes pastures at configured intervals (if specified)

## Available Pasture Types

### Reddit Pasture
- **Type**: `reddit`
- **URL Format**: Reddit JSON endpoints (e.g., `https://www.reddit.com/r/subreddit.json`)
- **Features**: Filters stickied posts, self-posts, and blacklisted terms

### HackerNews Pasture
- **Type**: `hackernews`
- **URL Format**: Hacker News API endpoints (e.g., `https://hacker-news.firebaseio.com/v0/topstories.json`)
- **Features**: Fetches top 50 stories, filters based on title blacklist, excludes Ask HN and job posts
- **Note**: URL is optional - HackerNews pasture uses default API endpoints if not provided

## Configuration Examples

### HackerNews Pasture
```ini
[hackernews_top]
type = hackernews
# url = https://hacker-news.firebaseio.com/v0/topstories.json  # Optional
blacklist = cryptocurrency, bitcoin, ethereum
interval = 60
```

### Reddit Pasture (Auto-detected)
```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30
```

## Dependencies

- **requests**: HTTP requests for API calls
- **selenium**: Web browser automation
- **webdriver-manager**: GeckoDriver management
- **beautifulsoup4**: HTML parsing and manipulation
- **markdownify**: HTML to Markdown conversion
- **schedule**: Task scheduling for interval-based scraping

## Error Handling

Comprehensive error handling for:
- Network timeouts and connection errors
- Invalid API responses
- Web scraping failures
- File I/O operations
- Pasture-specific errors

## Docker Support

### Using the Management Script

The project includes a convenient `run-docker.sh` script for managing the scraper:

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

```bash
# Build and start in background
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down

# Run once (single execution)
docker compose run --rm -T pasture-scraper

# Build images
docker compose build
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation accordingly
4. Ensure error handling is comprehensive
5. When adding new pasture types, follow the abstract base class interface

## License

This project is provided as-is without warranty. Use responsibly and in compliance with website terms of service.

## Disclaimer

This tool is intended for educational and research purposes. Users are responsible for:
- Complying with API terms of service for each source
- Respecting website robots.txt files
- Obtaining proper permissions for web scraping
- Using the tool ethically and legally
