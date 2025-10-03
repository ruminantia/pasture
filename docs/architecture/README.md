# Architecture Documentation

## System Overview

Pasture is built on a modular, extensible architecture that separates concerns between content sources ("pastures"), core scraping functionality, and application orchestration. The system follows a pipeline-based approach where content flows through multiple processing stages.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Pasture       │    │   Core Scraper  │    │   Output        │
│   Implementations│    │                 │    │   Management    │
│                 │    │                 │    │                 │
│ • Reddit        │◄──►│ • URL Processing │◄──►│ • File Storage  │
│ • HackerNews    │    │ • HTML Cleaning  │    │ • URL Tracking  │
│ • RSS           │    │ • Markdown Conv  │    │ • Organization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Configuration  │    │   Browser       │    │   Scheduling    │
│   Management     │    │   Automation    │    │   Engine        │
│                  │    │                 │    │                 │
│ • INI Parser     │    │ • Selenium      │    │ • Interval-based│
│ • Auto-detection │    │ • Firefox       │    │ • Task Queues   │
│ • Validation     │    │ • Headless Mode │    │ • Job Management│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Pasture Abstraction Layer

#### Base Pasture Class (`src/pastures/base/__init__.py`)

The abstract `Pasture` class defines the interface that all pasture implementations must follow:

```python
class Pasture(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.processed_urls: Set[str] = set()

    @abstractmethod
    def fetch_posts(self) -> List[Dict[str, Any]]
    @abstractmethod
    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]
    @abstractmethod
    def get_url_from_post(self, post: Dict[str, Any]) -> str
    
    # Concrete implementations
    def get_output_directory(self, base_output_dir: str) -> str
    def should_scrape_url(self, url: str, processed_urls: Set[str]) -> bool
    def mark_url_processed(self, url: str, processed_urls: Set[str]) -> None
    def get_tags_to_remove(self) -> List[str]
    def hash_url(url: str) -> str
```

#### Pasture Factory (`src/pastures/__init__.py`)

The factory pattern is used to create pasture instances based on configuration:

```python
class PastureFactory:
    _pasture_types = {
        "reddit": RedditPasture,
        "hackernews": HackerNewsPasture,
        "rss": RSSPasture,
    }

    @classmethod
    def create_pasture(cls, name: str, config: Dict[str, Any]) -> Pasture
    @classmethod
    def _determine_pasture_type(cls, config: Dict[str, Any]) -> str
    @classmethod
    def register_pasture_type(cls, pasture_type: str, pasture_class: Type[Pasture])
```

### 2. Core Scraper (`src/core/scraper.py`)

The core scraper provides shared functionality used by all pastures:

#### URL Processing
- **URL Normalization**: Removes tracking parameters for duplicate detection
- **URL Hashing**: SHA256-based URL identification
- **Media Detection**: Identifies and skips image/video URLs

#### Browser Management
- **CachedGeckoDriverManager**: Manages GeckoDriver with local caching
- **Driver Creation**: Creates Selenium WebDriver instances with retry logic
- **Fallback Mechanisms**: Graceful degradation when Docker unavailable

#### Content Processing
- **HTML Cleaning**: Removes unwanted tags while preserving content
- **Markdown Conversion**: Converts cleaned HTML to readable Markdown
- **Error Handling**: Comprehensive fallback for scraping failures

### 3. Application Orchestration (`src/main.py`)

The main application coordinates all components:

```python
def main() -> None:
    # Configuration loading
    config = configparser.ConfigParser()
    config.read("config.ini")
    
    # Mode detection
    if should_run_scheduled_mode(config):
        # Continuous mode with scheduler
        run_single_scrape(config)
        setup_scheduler(config)
        schedule.run_pending()  # Continuous loop
    else:
        # Single run mode
        run_single_scrape(config)
```

## Data Flow

### Content Processing Pipeline

1. **Configuration Loading**
   - Parse `config.ini` file
   - Auto-detect pasture types from URLs
   - Load global and pasture-specific settings

2. **Content Fetching** (Pasture-specific)
   - Reddit: Fetch JSON from Reddit API
   - HackerNews: Fetch from Firebase API
   - RSS: Parse RSS/Atom feeds

3. **Content Filtering**
   - Apply blacklist filters
   - Remove unwanted post types (stickied, self-posts, jobs)
   - Filter by date (RSS pastures)

4. **URL Processing**
   - Normalize URLs (remove tracking parameters)
   - Check against processed URLs set
   - Skip media URLs and duplicates

5. **Web Scraping**
   - Launch headless Firefox via Selenium
   - Navigate to target URL
   - Extract page content

6. **Content Processing**
   - Remove unwanted HTML tags
   - Clean and sanitize content
   - Convert to Markdown format

7. **Output Management**
   - Create organized directory structure
   - Save processed content as Markdown files
   - Update processed URLs tracking

## Pasture Implementations

### Reddit Pasture (`src/pastures/reddit/`)

#### Data Structure
```python
{
    "data": {
        "children": [
            {
                "data": {
                    "title": "Post Title",
                    "url": "https://external.com/article",
                    "selftext": "",  # Empty for external links
                    "stickied": False,
                    "is_self": False
                }
            }
        ]
    }
}
```

#### Filtering Logic
- Excludes stickied posts
- Excludes self-posts (text-only)
- Applies blacklist to post titles
- Only processes external URLs

### HackerNews Pasture (`src/pastures/hackernews/`)

#### Data Structure
```python
{
    "id": 12345678,
    "title": "Story Title",
    "url": "https://external.com/article",
    "type": "story",
    "score": 42
}
```

#### Filtering Logic
- Fetches top 50 stories by default
- Excludes "Ask HN" and job posts
- Applies blacklist to story titles
- Uses official Firebase API

### RSS Pasture (`src/pastures/rss/`)

#### Data Structure
```python
{
    "title": "Item Title",
    "link": "https://external.com/article",
    "description": "Item description",
    "published": "2023-01-01T12:00:00Z"
}
```

#### Filtering Logic
- Supports RSS 2.0, Atom, and RDF formats
- Applies blacklist to titles and descriptions
- Optional date-based filtering
- Auto-detects feed type from URL

## URL Normalization System

### Tracking Parameter Removal

The system removes 50+ common tracking parameters to prevent duplicate content:

```python
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'ref', 'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
    '_ke', 'trk', 'trkCampaign', 'source', 'CMP', 'ito',
    # ... and many more
}
```

### Duplicate Detection

```python
def normalize_url(url: str) -> str:
    # Remove tracking parameters
    # Standardize URL format
    # Return normalized URL
    
def hash_url(url: str) -> str:
    # SHA256 hash of normalized URL
    # Used for duplicate detection
```

## Browser Management

### CachedGeckoDriverManager

- **Local Caching**: Avoids GitHub API rate limits
- **Automatic Updates**: Checks for driver updates periodically
- **Fallback Support**: Uses system Firefox when Docker unavailable
- **Error Recovery**: Retry logic with exponential backoff

### Driver Configuration

```python
def create_driver_with_retry() -> WebDriver:
    options = FirefoxOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
```

## Scheduling System

### Mode Detection

The system automatically detects the operational mode:

- **Single Run**: No intervals configured → run once and exit
- **Continuous Mode**: Any pasture has interval → run scheduled tasks

### Task Scheduling

```python
def setup_scheduler(config: ConfigParser) -> None:
    for section in config.sections():
        if section == "global":
            continue
            
        interval = config[section].get("interval", "60")
        schedule.every(interval).minutes.do(
            lambda section=section: scrape_scheduled_pasture(section, config)
        )
```

## Error Handling & Resilience

### Comprehensive Error Recovery

1. **Network Errors**: Retry logic with exponential backoff
2. **Browser Issues**: Fallback to system Firefox
3. **API Failures**: Graceful degradation with logging
4. **File System**: Safe file operations with backup
5. **Configuration**: Auto-detection and validation

### Logging System

- **Structured Format**: Timestamp | Level | Module | Message
- **Color Coding**: Different colors for info, warning, error
- **Module Identification**: Clean module names for readability
- **Duplicate Prevention**: Centralized configuration

## Extension Points

### Adding New Pasture Types

1. **Create Implementation**
   ```python
   from .base import Pasture
   
   class CustomPasture(Pasture):
       def fetch_posts(self) -> List[Dict[str, Any]]:
           # Custom fetching logic
           
       def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
           # Custom filtering logic
           
       def get_url_from_post(self, post: Dict[str, Any]) -> str:
           # URL extraction logic
   ```

2. **Register with Factory**
   ```python
   PastureFactory.register_pasture_type("custom", CustomPasture)
   ```

3. **Configuration Support**
   ```ini
   [custom_pasture]
   type = custom
   url = https://custom-source.com/api
   blacklist = unwanted,terms
   interval = 30
   ```

### Custom Processing Hooks

The architecture supports custom processing through:
- Tag removal overrides
- Custom filtering logic
- Specialized URL processing
- Output format customization

## Performance Considerations

### Memory Management
- **Lazy Loading**: Pastures loaded only when needed
- **URL Tracking**: Efficient set-based duplicate detection
- **Stream Processing**: Process posts sequentially to minimize memory usage

### Network Efficiency
- **Connection Reuse**: Persistent HTTP sessions
- **Caching**: Driver and content caching where appropriate
- **Rate Limiting**: Configurable intervals prevent overwhelming targets

### Storage Optimization
- **Content Deduplication**: Avoids storing duplicate content
- **Efficient Hashing**: SHA256 for reliable URL identification
- **Organized Output**: Date-based directory structure

This modular architecture provides a solid foundation for content aggregation while maintaining flexibility for future enhancements and custom implementations.