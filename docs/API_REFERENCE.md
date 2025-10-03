# API Reference

## Overview

This document provides detailed API reference for the core components of the Pasture project. It covers the main classes, methods, and functions that developers can use to extend and customize the system.

## Core Components

### Pasture Base Class

The abstract `Pasture` class defines the interface that all pasture implementations must follow.

#### Class: `Pasture`
```python
class Pasture(ABC):
    """Abstract base class for all pasture implementations."""
```

#### Constructor
```python
def __init__(self, name: str, config: Dict[str, Any]):
    """
    Initialize a pasture instance.
    
    Args:
        name: Name of the pasture section
        config: Configuration dictionary for the pasture
    """
```

#### Abstract Methods

##### `fetch_posts`
```python
@abstractmethod
def fetch_posts(self) -> List[Dict[str, Any]]:
    """
    Fetch posts/items from the pasture source.
    
    Returns:
        List of dictionaries containing post/item data
    """
```

##### `filter_posts`
```python
@abstractmethod
def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter posts based on pasture-specific criteria.
    
    Args:
        posts: List of posts to filter
        
    Returns:
        Filtered list of posts
    """
```

##### `get_url_from_post`
```python
@abstractmethod
def get_url_from_post(self, post: Dict[str, Any]) -> str:
    """
    Extract the external URL from a post/item.
    
    Args:
        post: Post/item dictionary
        
    Returns:
        External URL to scrape
    """
```

#### Concrete Methods

##### `get_output_directory`
```python
def get_output_directory(self, base_output_dir: str) -> str:
    """
    Get the output directory for this pasture.
    
    Args:
        base_output_dir: Base output directory
        
    Returns:
        Full path to pasture-specific output directory
    """
```

##### `should_scrape_url`
```python
def should_scrape_url(self, url: str, processed_urls: Set[str]) -> bool:
    """
    Check if a URL should be scraped.
    
    Args:
        url: URL to check
        processed_urls: Set of already processed URLs
        
    Returns:
        True if URL should be scraped, False otherwise
    """
```

##### `mark_url_processed`
```python
def mark_url_processed(self, url: str, processed_urls: Set[str]) -> None:
    """
    Mark a URL as processed.
    
    Args:
        url: URL to mark as processed
        processed_urls: Set to add the URL hash to
    """
```

##### `hash_url`
```python
@staticmethod
def hash_url(url: str) -> str:
    """
    Hash a URL using SHA256.
    
    Args:
        url: URL to hash
        
    Returns:
        SHA256 hash of the URL
    """
```

##### `get_tags_to_remove`
```python
def get_tags_to_remove(self) -> List[str]:
    """
    Get the list of HTML tags to remove during processing.
    
    Returns:
        List of tag names to remove
    """
```

### PastureFactory Class

The factory class for creating pasture instances based on configuration.

#### Class: `PastureFactory`
```python
class PastureFactory:
    """Factory class for creating pasture instances based on configuration."""
```

#### Methods

##### `create_pasture`
```python
@classmethod
def create_pasture(cls, name: str, config: Dict[str, Any]) -> Pasture:
    """
    Create a pasture instance based on configuration.
    
    Args:
        name: Name of the pasture section
        config: Configuration dictionary for the pasture
        
    Returns:
        Pasture instance
        
    Raises:
        ValueError: If pasture type cannot be determined from configuration
    """
```

##### `_determine_pasture_type`
```python
@classmethod
def _determine_pasture_type(cls, config: Dict[str, Any]) -> str:
    """
    Determine the pasture type from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        String representing the pasture type
    """
```

##### `register_pasture_type`
```python
@classmethod
def register_pasture_type(cls, pasture_type: str, pasture_class: Type[Pasture]) -> None:
    """
    Register a new pasture type.
    
    Args:
        pasture_type: String identifier for the pasture type
        pasture_class: Class implementing the Pasture interface
    """
```

## Core Scraper Functions

### URL Processing Functions

#### `normalize_url`
```python
def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing tracking parameters and standardizing format.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL without tracking parameters
    """
```

#### `hash_url`
```python
def hash_url(url: str) -> str:
    """
    Create a SHA256 hash of a URL for duplicate detection.
    
    Args:
        url: URL to hash
        
    Returns:
        SHA256 hash string
    """
```

#### `is_media_url`
```python
def is_media_url(url: str) -> bool:
    """
    Check if a URL points to media content (images, videos, etc.).
    
    Args:
        url: URL to check
        
    Returns:
        True if URL points to media content, False otherwise
    """
```

### Browser Management

#### `CachedGeckoDriverManager`
```python
class CachedGeckoDriverManager:
    """Manager for GeckoDriver with local caching to avoid GitHub rate limits."""
```

##### Methods

###### `install`
```python
def install(self) -> str:
    """
    Install or get cached GeckoDriver path.
    
    Returns:
        Path to GeckoDriver executable
    """
```

###### `_get_cached_driver`
```python
def _get_cached_driver(self) -> Optional[str]:
    """
    Get cached driver path if available and not expired.
    
    Returns:
        Path to cached driver or None if not available
    """
```

###### `_cache_driver`
```python
def _cache_driver(self, driver_path: str) -> None:
    """
    Cache a driver for future use.
    
    Args:
        driver_path: Path to the driver to cache
    """
```

###### `_fallback_to_system_firefox`
```python
def _fallback_to_system_firefox(self) -> str:
    """
    Fallback to system Firefox installation.
    
    Returns:
        Path to system Firefox executable
        
    Raises:
        RuntimeError: If Firefox is not found on system
    """
```

#### `create_driver_with_retry`
```python
def create_driver_with_retry(max_retries: int = 3, retry_delay: int = 5) -> WebDriver:
    """
    Create a Selenium WebDriver with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Configured Firefox WebDriver instance
    """
```

### Content Processing Functions

#### `scrape_url`
```python
def scrape_url(url: str, tags_to_remove: List[str]) -> Optional[str]:
    """
    Scrape content from a URL and convert to Markdown.
    
    Args:
        url: URL to scrape
        tags_to_remove: List of HTML tags to remove
        
    Returns:
        Processed Markdown content or None if scraping failed
    """
```

#### `post_process_html`
```python
def post_process_html(html: str, tags_to_remove: List[str]) -> str:
    """
    Process HTML content by removing unwanted tags and cleaning.
    
    Args:
        html: Raw HTML content
        tags_to_remove: List of HTML tags to remove
        
    Returns:
        Cleaned HTML content
    """
```

#### `fallback_scrape_url`
```python
def fallback_scrape_url(url: str, tags_to_remove: List[str]) -> Optional[str]:
    """
    Fallback scraping method using requests when Selenium fails.
    
    Args:
        url: URL to scrape
        tags_to_remove: List of HTML tags to remove
        
    Returns:
        Processed Markdown content or None if scraping failed
    """
```

### File Management Functions

#### `load_processed_urls`
```python
def load_processed_urls(file_path: str) -> Set[str]:
    """
    Load processed URLs from JSON file.
    
    Args:
        file_path: Path to the processed URLs JSON file
        
    Returns:
        Set of processed URL hashes
    """
```

#### `save_processed_urls`
```python
def save_processed_urls(file_path: str, processed_urls: Set[str]) -> None:
    """
    Save processed URLs to JSON file.
    
    Args:
        file_path: Path to save the processed URLs
        processed_urls: Set of processed URL hashes to save
    """
```

#### `scrape_pasture`
```python
def scrape_pasture(pasture: Pasture, output_base_dir: str, processed_urls: Set[str]) -> Set[str]:
    """
    Scrape all posts from a pasture.
    
    Args:
        pasture: Pasture instance to scrape
        output_base_dir: Base output directory
        processed_urls: Set of already processed URLs
        
    Returns:
        Updated set of processed URLs
    """
```

## Main Application Functions

### `setup_logging`
```python
def setup_logging() -> logging.Logger:
    """
    Configure logging for the entire application.
    
    Returns:
        Configured logger instance
    """
```

### `run_single_scrape`
```python
def run_single_scrape(config: configparser.ConfigParser) -> None:
    """
    Run a single scrape of all configured pastures.
    
    Args:
        config: Configuration parser with pasture sections
    """
```

### `scrape_scheduled_pasture`
```python
def scrape_scheduled_pasture(section: str, config: configparser.ConfigParser) -> None:
    """
    Scrape a single pasture when scheduled.
    
    Args:
        section: Name of the pasture section to scrape
        config: Configuration parser with pasture sections
    """
```

### `setup_scheduler`
```python
def setup_scheduler(config: configparser.ConfigParser) -> None:
    """
    Set up scheduled scraping based on config intervals.
    
    Args:
        config: Configuration parser with pasture sections
    """
```

### `should_run_scheduled_mode`
```python
def should_run_scheduled_mode(config: configparser.ConfigParser) -> bool:
    """
    Check if we should run in scheduled mode.
    
    Args:
        config: Configuration parser with pasture sections
        
    Returns:
        True if any pasture has an interval configured, False otherwise
    """
```

### `main`
```python
def main() -> None:
    """Main function to run the pasture scraper."""
```

## Data Structures

### Post Data Format

All pasture implementations should return posts in the following format:

```python
{
    "title": str,           # Post title
    "url": str,             # External URL to scrape
    "description": str,     # Optional: Post description/summary
    "published": str,       # Optional: Publication date
    "id": str,              # Optional: Unique identifier
    "author": str,          # Optional: Author name
    "categories": List[str] # Optional: List of categories/tags
}
```

### Configuration Format

Configuration is passed as a dictionary with the following structure:

```python
{
    "type": str,            # Pasture type (optional, auto-detected)
    "url": str,             # Source URL (required for most pastures)
    "blacklist": str,       # Comma-separated blacklist terms
    "remove_tags": str,     # Comma-separated HTML tags to remove
    "interval": str,        # Scraping interval in minutes
    "max_age_days": str     # Maximum age in days (RSS pastures only)
}
```

## Constants

### Tracking Parameters

The system removes the following tracking parameters during URL normalization:

```python
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'ref', 'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid',
    '_ke', 'trk', 'trkCampaign', 'source', 'CMP', 'ito',
    # ... and many more
}
```

### Default Settings

```python
DEFAULT_INTERVAL = 60  # minutes
DEFAULT_TIMEOUT = 30   # seconds
MAX_RETRIES = 3        # retry attempts
```

## Error Handling

### Custom Exceptions

The system uses standard Python exceptions but may raise the following:

- `ValueError`: Invalid configuration or missing required parameters
- `RuntimeError`: Browser/driver initialization failures
- `requests.RequestException`: Network/API request failures

### Logging Levels

- `INFO`: Normal operation messages
- `WARNING`: Non-critical issues that don't stop execution
- `ERROR`: Critical failures that may affect functionality
- `DEBUG`: Detailed debugging information

This API reference provides comprehensive documentation for all major components and functions in the Pasture system. Developers should refer to this document when extending the system or implementing custom functionality.