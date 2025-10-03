# Development Guide

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Firefox browser
- Git

### Initial Setup

1. **Clone and Navigate to Project**
   ```bash
   git clone <repository-url>
   cd pasture
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   ```bash
   python src/main.py --help
   ```

### Development Dependencies

The project uses the following key dependencies:

- **selenium**: Browser automation
- **requests**: HTTP client for API calls
- **beautifulsoup4**: HTML parsing
- **markdownify**: HTML to Markdown conversion
- **schedule**: Task scheduling
- **webdriver-manager**: GeckoDriver management

## Project Structure

```
pasture/
├── src/
│   ├── pastures/           # Pasture implementations
│   │   ├── base/          # Abstract Pasture class
│   │   ├── reddit/        # Reddit pasture implementation
│   │   ├── hackernews/    # HackerNews pasture implementation
│   │   ├── rss/           # RSS feed pasture implementation
│   │   └── __init__.py    # Pasture factory
│   ├── core/              # Shared utilities
│   │   └── scraper.py     # Core scraping functions
│   └── main.py            # Application entry point
├── docs/                  # Documentation
├── output/               # Generated content
├── config.ini           # Configuration file
└── requirements.txt     # Python dependencies
```

## Adding New Pasture Types

### Step 1: Create Pasture Implementation

Create a new directory under `src/pastures/` for your pasture type:

```bash
mkdir src/pastures/custom
```

Create the pasture implementation file:

```python
# src/pastures/custom/__init__.py

from typing import List, Dict, Any
import requests
from ..base import Pasture


class CustomPasture(Pasture):
    """Custom pasture implementation for a new content source."""
    
    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch posts from the custom source.
        
        Returns:
            List of post dictionaries with source-specific structure
        """
        url = self.config.get("url")
        if not url:
            raise ValueError("URL is required for custom pasture")
            
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Transform API response to standard format
            posts = []
            for item in data.get("items", []):
                posts.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "description": item.get("description", ""),
                    "published": item.get("published"),
                    # Add any other relevant fields
                })
                
            return posts
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch from {url}: {e}")
            return []
    
    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter posts based on custom criteria.
        
        Args:
            posts: List of posts to filter
            
        Returns:
            Filtered list of posts
        """
        filtered_posts = []
        blacklist = self.config.get("blacklist", "").lower().split(",")
        blacklist = [term.strip() for term in blacklist if term.strip()]
        
        for post in posts:
            # Skip if title contains blacklisted terms
            title = post.get("title", "").lower()
            if any(term in title for term in blacklist):
                continue
                
            # Add custom filtering logic here
            # Example: Filter by date, score, etc.
            
            filtered_posts.append(post)
            
        return filtered_posts
    
    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from a post.
        
        Args:
            post: Post dictionary
            
        Returns:
            External URL to scrape
        """
        return post.get("url", "")
```

### Step 2: Register with Pasture Factory

Update `src/pastures/__init__.py` to include your new pasture type:

```python
from .base import Pasture
from .reddit import RedditPasture
from .hackernews import HackerNewsPasture
from .rss import RSSPasture
from .custom import CustomPasture  # Add import


class PastureFactory:
    """Factory class for creating pasture instances."""
    
    _pasture_types = {
        "reddit": RedditPasture,
        "hackernews": HackerNewsPasture,
        "rss": RSSPasture,
        "custom": CustomPasture,  # Add new type
    }
    
    @classmethod
    def _determine_pasture_type(cls, config: Dict[str, Any]) -> str:
        """Determine pasture type from configuration."""
        if "type" in config:
            return config["type"]
            
        url = config.get("url", "")
        
        # Add auto-detection for custom type
        if "custom-source.com" in url:
            return "custom"
        elif "reddit.com" in url:
            return "reddit"
        # ... existing detection logic
        
        return "reddit"  # Default
```

### Step 3: Test Your Implementation

Create a test configuration:

```ini
[custom_source]
type = custom
url = https://api.custom-source.com/feed
blacklist = spam, advertisement
interval = 60
```

Run the pasture to test:

```bash
python src/main.py
```

## Development Best Practices

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public methods
- Use descriptive variable names

### Error Handling

```python
def robust_method(self):
    """Example of proper error handling."""
    try:
        # Operation that might fail
        result = self.perform_operation()
        return result
    except SpecificException as e:
        self.logger.error(f"Operation failed: {e}")
        return fallback_value
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}")
        raise
```

### Logging

Use the centralized logging system:

```python
import logging

logger = logging.getLogger(__name__)

def some_method(self):
    logger.info("Starting operation")
    try:
        # Operation logic
        logger.debug("Detailed operation information")
    except Exception as e:
        logger.error(f"Operation failed: {e}")
```

### Testing New Pastures

1. **Unit Testing**: Test individual pasture methods
2. **Integration Testing**: Test pasture with real configuration
3. **End-to-End Testing**: Run full scraping pipeline

Example test structure:

```python
# tests/test_custom_pasture.py

import unittest
from src.pastures.custom import CustomPasture

class TestCustomPasture(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "https://api.example.com/feed",
            "blacklist": "spam"
        }
        self.pasture = CustomPasture("test", self.config)
    
    def test_fetch_posts(self):
        posts = self.pasture.fetch_posts()
        self.assertIsInstance(posts, list)
    
    def test_filter_posts(self):
        # Test filtering logic
        pass
```

## Debugging

### Common Issues and Solutions

#### Browser/Driver Issues

**Problem**: GeckoDriver not found or Firefox not installed
**Solution**: 
```bash
# Install Firefox
sudo apt-get install firefox-esr  # Ubuntu/Debian

# Or use the cached driver manager
python -c "from src.core.scraper import CachedGeckoDriverManager; manager = CachedGeckoDriverManager(); manager.install()"
```

**Problem**: Docker container can't access Firefox
**Solution**: Use system fallback mode or ensure proper Docker configuration

#### Network Issues

**Problem**: API requests timing out
**Solution**: Increase timeout values and implement retry logic

```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

#### Configuration Issues

**Problem**: Pasture type not detected correctly
**Solution**: Add explicit type configuration or extend auto-detection logic

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
# Temporary modification to src/main.py
root_logger.setLevel(logging.DEBUG)
```

## Performance Optimization

### Memory Management

- Process posts in batches for large datasets
- Use generators for memory-efficient iteration
- Clear browser cache between scrapes

```python
def process_posts_in_batches(self, posts, batch_size=100):
    """Process posts in batches to manage memory."""
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        yield from self.process_batch(batch)
```

### Network Optimization

- Implement connection pooling
- Cache frequently accessed resources
- Use appropriate timeouts

### Browser Optimization

- Reuse browser instances when possible
- Implement proper cleanup
- Use headless mode for production

## Contributing Guidelines

### Pull Request Process

1. **Fork the Repository**
2. **Create Feature Branch**: `git checkout -b feature/amazing-feature`
3. **Commit Changes**: `git commit -m 'Add amazing feature'`
4. **Push to Branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**

### Code Review Checklist

- [ ] Code follows project style guidelines
- [ ] Type hints are used appropriately
- [ ] Documentation is updated
- [ ] Tests are added or updated
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] No sensitive data is exposed

### Documentation Requirements

- Update README.md for user-facing changes
- Add docstrings for new public methods
- Update configuration examples if needed
- Document any breaking changes

## Advanced Development Topics

### Custom HTML Processing

Override the default HTML cleaning:

```python
def custom_html_processing(self, html: str) -> str:
    """Custom HTML processing logic."""
    # Add custom processing before standard cleaning
    processed_html = self.custom_clean(html)
    
    # Use standard processing
    from core.scraper import post_process_html
    return post_process_html(processed_html, self.get_tags_to_remove())
```

### Custom URL Normalization

Extend URL normalization for specific domains:

```python
def custom_normalize_url(self, url: str) -> str:
    """Custom URL normalization for specific domains."""
    from core.scraper import normalize_url
    
    normalized = normalize_url(url)
    
    # Add domain-specific normalization
    if "specific-domain.com" in normalized:
        # Custom normalization logic
        pass
        
    return normalized
```

### Plugin System (Future Enhancement)

The architecture supports a plugin system for advanced customization:

```python
# Example plugin interface
class PasturePlugin:
    def before_fetch(self, pasture):
        """Called before fetching posts."""
        pass
        
    def after_fetch(self, pasture, posts):
        """Called after fetching posts."""
        return posts
        
    def before_scrape(self, pasture, url):
        """Called before scraping a URL."""
        pass
        
    def after_scrape(self, pasture, url, content):
        """Called after scraping a URL."""
        return content
```

This development guide provides the foundation for extending and maintaining the Pasture project. Follow these guidelines to ensure consistent, high-quality contributions.