# Frequently Asked Questions (FAQ)

## General Questions

### What is Pasture?
Pasture is a sophisticated multi-source content scraping system that aggregates content from various online sources including Reddit, HackerNews, and RSS feeds. It processes external URLs into clean Markdown format with intelligent duplicate detection and filtering.

### What types of content sources does Pasture support?
- **Reddit**: Any subreddit JSON endpoint
- **HackerNews**: Official Firebase API for top stories
- **RSS Feeds**: RSS 2.0, Atom, and RDF formats
- The system is extensible and supports adding custom pasture types

### Is Pasture free to use?
Yes, Pasture is open source and free to use. However, users are responsible for complying with the terms of service of the websites they scrape and respecting API rate limits.

### What programming language is Pasture written in?
Pasture is written in Python 3.11+ and uses modern Python features including type hints and async patterns where appropriate.

## Installation & Setup

### What are the system requirements?
- Python 3.11 or higher
- Firefox browser
- 2GB+ RAM (4GB+ recommended for production)
- Stable internet connection
- 10GB+ storage (depending on content volume)

### Do I need to install Firefox separately?
Yes, Firefox is required for web scraping. The system uses Selenium with Firefox for reliable content extraction. Firefox ESR is recommended for server deployments.

### How do I install GeckoDriver?
You don't need to install GeckoDriver manually. Pasture includes a `CachedGeckoDriverManager` that automatically downloads and caches the appropriate GeckoDriver version, avoiding GitHub API rate limits.

### Can I run Pasture in a Docker container?
Yes, Pasture includes comprehensive Docker support with:
- Pre-configured Dockerfile
- Docker Compose configuration
- Management script (`run-docker.sh`) for easy container operations

## Configuration

### How do I configure which content to scrape?
Edit the `config.ini` file in the project root. The configuration uses INI format with sections for each pasture (content source) and optional global settings.

### What's the difference between pasture types?
- **Reddit**: Fetches from Reddit JSON APIs, filters stickied and self-posts
- **HackerNews**: Uses official Firebase API, filters job posts and Ask HN
- **RSS**: Parses RSS/Atom feeds, supports date-based filtering

### How does auto-detection work for pasture types?
Pasture automatically detects the pasture type from URL patterns:
- URLs containing `reddit.com` → Reddit pasture
- URLs containing `hackernews` or `news.ycombinator.com` → HackerNews pasture  
- URLs ending with `.rss`, `.xml` or containing `/rss/`, `/feed/` → RSS pasture

### Can I use multiple pastures of the same type?
Yes, you can configure multiple pastures of the same type. Each pasture section in `config.ini` is treated as a separate content source.

## Content Processing

### How does duplicate detection work?
Pasture uses intelligent duplicate detection:
1. URLs are normalized by removing tracking parameters (utm_source, ref, fbclid, etc.)
2. Normalized URLs are hashed using SHA256
3. Hashes are stored in `output/processed_urls.json`
4. Before scraping any URL, the system checks if it's already processed

### What HTML tags are removed by default?
The system removes common non-content tags by default:
- `script`, `style`, `noscript`, `iframe`
- `button`, `svg`, `footer`, `nav`
- Additional tags can be configured via `remove_tags` setting

### Can I customize which HTML tags are removed?
Yes, using Gentoo-style override syntax:
- `header, aside` - Add tags to removal list
- `-nav, -footer` - Remove tags from global list (keep these)
- No `remove_tags` - Use only global tags

### How is content converted to Markdown?
The system uses `markdownify` library to convert cleaned HTML to Markdown format, preserving:
- Headers, paragraphs, and text formatting
- Links and images (when appropriate)
- Code blocks and lists

## Operation & Performance

### How often does Pasture scrape content?
Scraping intervals are configurable per pasture via the `interval` setting (in minutes). If no intervals are configured, Pasture runs once and exits.

### Can I run Pasture continuously?
Yes, when any pasture has an `interval` configured, Pasture runs in continuous mode with scheduled scraping.

### How much storage does Pasture use?
Storage usage depends on:
- Number of active pastures
- Scraping frequency
- Content volume from sources
- Retention policy for output files

A typical deployment might use 1-10GB per month.

### Does Pasture respect website rate limits?
While Pasture includes configurable intervals, users are responsible for:
- Setting appropriate scraping intervals
- Respecting API rate limits
- Complying with website terms of service
- Using the tool ethically and legally

## Troubleshooting

### Why am I getting "GeckoDriver not found" errors?
This usually indicates:
1. Network issues preventing GeckoDriver download
2. GitHub API rate limits
3. File permission issues

Solutions:
- The system automatically falls back to system Firefox
- Check network connectivity
- Verify `.webdriver_cache/` directory permissions

### Why are some URLs not being scraped?
Common reasons:
- URL is already in processed URLs list (duplicate)
- URL points to media content (images, videos)
- Network timeout or connection error
- Website blocking the scraper

### How can I debug scraping issues?
Enable debug logging by modifying `src/main.py`:
```python
root_logger.setLevel(logging.DEBUG)
```

### Why is my Docker container exiting immediately?
Check:
- Volume mounts are properly configured
- `config.ini` file exists and is valid
- Output directory is writable
- Use `./run-docker.sh logs` to view container logs

## Advanced Usage

### Can I add custom pasture types?
Yes, the system is designed for extensibility:
1. Create a class inheriting from `Pasture` base class
2. Implement required abstract methods
3. Register with `PastureFactory.register_pasture_type()`
4. Update auto-detection logic if needed

### How can I process content differently?
You can extend the system by:
- Overriding HTML processing methods
- Adding custom filtering logic
- Implementing specialized URL normalization
- Creating custom output formats

### Can I use a database instead of file storage?
The current version uses file-based storage, but the architecture supports database integration. This is planned for future versions.

### Is there a plugin system?
While not currently implemented, the modular architecture makes it easy to add plugin support for:
- Custom content processors
- Advanced filtering
- Output format handlers
- Monitoring and analytics

## Legal & Ethical Considerations

### Is web scraping legal?
Web scraping exists in a legal gray area and depends on:
- Website terms of service
- Jurisdiction and local laws
- How the scraped data is used
- Respect for robots.txt files

### What are my responsibilities as a user?
- Comply with website terms of service
- Respect API rate limits and robots.txt
- Use appropriate scraping intervals
- Obtain proper permissions when required
- Use scraped content ethically and legally

### Can I use Pasture for commercial purposes?
Pasture is provided as-is without warranty. Commercial use is permitted but users are responsible for ensuring compliance with all applicable laws and regulations.

### How can I avoid being blocked by websites?
- Use reasonable scraping intervals
- Respect robots.txt directives
- Use appropriate User-Agent headers
- Consider using official APIs when available
- Monitor for rate limiting responses

## Support & Community

### Where can I get help?
- Check this documentation first
- Review existing GitHub issues
- Create new issues for bugs or feature requests
- Join community discussions

### How can I contribute to Pasture?
- Report bugs and issues
- Suggest new features
- Submit pull requests
- Improve documentation
- Share your use cases and configurations

### Is there a community or forum?
Check the project repository for:
- GitHub Discussions
- Issue tracker
- Wiki pages
- Community-contributed examples

### How often is Pasture updated?
The project follows semantic versioning with regular updates for:
- Bug fixes and security patches
- New features and pasture types
- Performance improvements
- Documentation updates

---

*This FAQ is regularly updated. Check the project repository for the latest information.*