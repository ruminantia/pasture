# Configuration Guide

## Overview

Pasture uses a flexible INI-based configuration system that supports multiple content sources ("pastures") with both global and pasture-specific settings. The configuration system provides intelligent auto-detection, backward compatibility, and extensible options for all pasture types.

## Configuration File Structure

The main configuration file is `config.ini` located in the project root. The file follows standard INI format with sections for global settings and individual pastures.

### Basic Structure

```ini
[global]
# Global settings apply to all pastures
remove_tags = script, style, noscript, iframe

# Pasture configurations
[worldnews]
type = reddit
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin
interval = 60

[tech_blog_rss]
type = rss
url = https://example.com/feed.rss
max_age_days = 7
interval = 120
```

## Global Configuration

The `[global]` section contains settings that apply to all pastures unless overridden.

### Global Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `remove_tags` | string | - | Comma-separated list of HTML tags to remove from all scraped content |

### Global Tags Example

```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav
```

## Pasture Configuration

Each pasture is defined in its own section with pasture-specific settings.

### Common Pasture Options

These options are available for all pasture types:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | No* | Pasture type (reddit, hackernews, rss) - auto-detected if not specified |
| `url` | string | Yes** | Source URL or API endpoint |
| `blacklist` | string | No | Comma-separated terms to exclude (case-insensitive) |
| `remove_tags` | string | No | HTML tags to add/remove from global configuration |
| `interval` | integer | No | Scraping interval in minutes (default: 60) |

\* Type is auto-detected from URL patterns if not specified  
\** Optional for HackerNews pastures

## Pasture Types

### Reddit Pasture

Reddit pastures fetch content from Reddit JSON endpoints.

#### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | No | Must be `reddit` (auto-detected from URL) |
| `url` | string | Yes | Reddit JSON endpoint URL |
| `blacklist` | string | No | Terms to exclude from post titles |
| `interval` | integer | No | Scraping interval in minutes |

#### Examples

```ini
# Basic subreddit
[worldnews]
type = reddit
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30

# Domain-specific content
[arstechnica]
url = https://www.reddit.com/domain/arstechnica.com.json
blacklist = Trump, COVID
interval = 60

# Auto-detected (type not required)
[LocalLLaMA]
url = https://www.reddit.com/r/LocalLLaMA.json
interval = 120
```

### HackerNews Pasture

HackerNews pastures fetch top stories from the Hacker News Firebase API.

#### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | No | Must be `hackernews` (auto-detected from URL) |
| `url` | string | No | Hacker News API endpoint (optional) |
| `blacklist` | string | No | Terms to exclude from story titles |
| `interval` | integer | No | Scraping interval in minutes |

#### Examples

```ini
# Top stories with blacklist
[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum
interval = 60

# Custom endpoint (rarely needed)
[hackernews_new]
type = hackernews
url = https://hacker-news.firebaseio.com/v0/newstories.json
blacklist = job, hiring
interval = 30
```

### RSS Pasture

RSS pastures fetch items from RSS, Atom, or RDF feeds.

#### Configuration Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `type` | string | No | Must be `rss` (auto-detected from URL) |
| `url` | string | Yes | RSS/Atom feed URL |
| `blacklist` | string | No | Terms to exclude from titles/descriptions |
| `max_age_days` | integer | No | Maximum age of items in days |
| `interval` | integer | No | Scraping interval in minutes |

#### Examples

```ini
# RSS feed with age limit
[tech_blog_rss]
type = rss
url = https://example.com/feed.rss
blacklist = sponsored, advertisement
max_age_days = 7
interval = 120

# Atom feed with auto-detection
[news_site_atom]
url = https://example.com/atom.xml
blacklist = 
max_age_days = 3
interval = 60
```

## Advanced Configuration

### Tag Removal System

Pasture supports flexible HTML tag removal with Gentoo-style override syntax.

#### Global Tags

Define tags that will be removed from all scraped sites:

```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav
```

#### Pasture-Specific Overrides

Modify global behavior for individual pastures:

```ini
[worldnews]
# Add tags to global set
remove_tags = header, aside, form

[arstechnica]
# Remove tags from global set (keep these)
remove_tags = -nav, -footer

[technews]
# Keep nav, add header and aside
remove_tags = -nav, header, aside
```

#### Override Syntax

- **No prefix**: Add tag to removal list (e.g., `header`, `aside`)
- **`-` prefix**: Remove tag from global list (e.g., `-nav`, `-footer`)
- **No `remove_tags`**: Use only global tags (if defined)
- **No `[global]` section**: Each pasture uses only its own tags

### Scheduling Configuration

#### Single Run Mode

If no pastures have `interval` configured, Pasture runs once and exits:

```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json
# No interval = single run
```

#### Continuous Mode

When any pasture has an `interval` configured, Pasture runs continuously:

```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json
interval = 30  # Run every 30 minutes

[hackernews_top]
type = hackernews
interval = 60  # Run every 60 minutes
```

## Auto-Detection Rules

Pasture automatically detects pasture types from URL patterns:

| Pattern | Detected Type |
|---------|---------------|
| `reddit.com` in URL | `reddit` |
| `hackernews` or `news.ycombinator.com` in URL | `hackernews` |
| URL ends with `.rss` or `.xml` | `rss` |
| `/rss` or `/feed` in URL | `rss` |
| No match | `reddit` (backward compatibility) |

## Configuration Examples

### Complete Configuration Example

```ini
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

# Reddit pastures
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
remove_tags = header, aside
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, bitcoin
interval = 60

# HackerNews pasture
[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum
remove_tags = -nav
interval = 60

# RSS pastures
[tech_blog_rss]
type = rss
url = https://example.com/feed.rss
blacklist = sponsored, advertisement
max_age_days = 7
interval = 120

[news_site_atom]
url = https://example.com/atom.xml
max_age_days = 3
interval = 60
```

### Minimal Configuration

```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json

[hackernews_top]
type = hackernews
```

## Best Practices

1. **Start Simple**: Begin with minimal configuration and add options as needed
2. **Use Blacklists**: Configure blacklists to filter unwanted content early
3. **Set Reasonable Intervals**: Avoid overwhelming target sites with frequent requests
4. **Test Configurations**: Use single-run mode to test new configurations
5. **Monitor Output**: Check generated content to refine tag removal settings
6. **Respect Rate Limits**: Be mindful of API rate limits and terms of service

## Troubleshooting

### Common Issues

- **Invalid URLs**: Ensure URLs are accessible and properly formatted
- **Missing Dependencies**: Verify all required Python packages are installed
- **Permission Errors**: Check file permissions for output directory
- **Browser Issues**: Ensure Firefox and GeckoDriver are properly installed

### Debug Mode

For troubleshooting, you can enable debug logging by modifying the logging configuration in `src/main.py`:

```python
root_logger.setLevel(logging.DEBUG)
```

This will provide detailed information about the scraping process and any issues encountered.