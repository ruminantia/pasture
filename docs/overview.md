# Pasture Project Overview

## Introduction

Pasture is a sophisticated, multi-source content scraping system designed to aggregate and process content from various online sources. Originally developed as a Reddit-focused scraper, the project has evolved into a modular, extensible platform supporting multiple content sources ("pastures") including Reddit, HackerNews, and RSS feeds.

## Core Philosophy

Pasture operates on the principle of intelligent content aggregation with built-in deduplication and filtering. The system is designed to:

- **Aggregate** content from diverse sources
- **Filter** unwanted content based on configurable criteria  
- **Process** external URLs into clean, readable Markdown
- **Deduplicate** content across all sources to avoid redundancy
- **Schedule** scraping operations for continuous content flow

## Key Features

### Multi-Source Architecture
- **Modular Design**: Clean separation of concerns with pasture-specific implementations
- **Extensible Framework**: Easy addition of new content sources
- **Auto-detection**: Intelligent pasture type detection from URLs

### Content Processing Pipeline
- **Web Scraping**: Headless browser automation for reliable content extraction
- **HTML Cleaning**: Removal of unwanted elements while preserving meaningful content
- **Markdown Conversion**: Clean, readable output format
- **URL Normalization**: Removal of tracking parameters for accurate deduplication

### Intelligent Filtering
- **Blacklist System**: Configurable term-based content exclusion
- **Duplicate Detection**: Global URL tracking across all pastures
- **Media Filtering**: Automatic skipping of image/video URLs
- **Pasture-Specific Logic**: Custom filtering rules per content source

### Operational Excellence
- **Scheduled Execution**: Configurable scraping intervals per pasture
- **Robust Error Handling**: Comprehensive fallback mechanisms
- **Docker Support**: Containerized deployment with management scripts
- **Structured Logging**: Color-coded, emoji-enhanced logging system

## Architecture Overview

```
pasture/
├── src/
│   ├── pastures/           # Pasture implementations
│   │   ├── base/          # Abstract Pasture class
│   │   ├── reddit/        # Reddit pasture implementation
│   │   ├── hackernews/    # HackerNews pasture implementation
│   │   └── rss/           # RSS feed pasture implementation
│   ├── core/              # Shared utilities
│   │   └── scraper.py     # Core scraping functions
│   └── main.py            # Application entry point
├── docs/                  # Comprehensive documentation
├── output/               # Generated content storage
└── config.ini           # User configuration
```

## Supported Pasture Types

### Reddit Pasture
- **Type**: `reddit`
- **Sources**: Any Reddit JSON endpoint
- **Features**: Stickied post filtering, self-post exclusion, subreddit-specific content

### HackerNews Pasture  
- **Type**: `hackernews`
- **Sources**: Hacker News Firebase API
- **Features**: Top stories, Ask HN filtering, job post exclusion

### RSS Pasture
- **Type**: `rss`
- **Sources**: RSS 2.0, Atom, and RDF feeds
- **Features**: Date-based filtering, feed auto-detection, description parsing

## Technical Foundation

### Dependencies
- **Selenium**: Headless browser automation
- **BeautifulSoup4**: HTML parsing and manipulation
- **Requests**: HTTP client for API calls
- **Markdownify**: HTML to Markdown conversion
- **Schedule**: Task scheduling for interval-based operations

### Browser Integration
- **Firefox ESR**: Primary browser engine
- **GeckoDriver**: WebDriver implementation with caching
- **Headless Mode**: Background operation without UI
- **System Fallback**: Graceful degradation when Docker unavailable

## Use Cases

### Content Aggregation
- Building personal news feeds from multiple sources
- Creating topic-specific content collections
- Monitoring specific subreddits or RSS feeds

### Research & Analysis
- Collecting data for NLP and machine learning
- Tracking content trends across platforms
- Building datasets for academic research

### Content Curation
- Filtering unwanted topics or sources
- Creating clean, readable versions of web content
- Building archives of specific content types

## Project Status

Pasture is a production-ready system with:
- ✅ Modular, extensible architecture
- ✅ Comprehensive error handling
- ✅ Docker containerization
- ✅ Detailed documentation
- ✅ Multiple source integrations

The project maintains backward compatibility while providing a solid foundation for future enhancements and custom pasture implementations.

## Next Steps

For detailed information on specific aspects of the project, refer to:
- [Configuration Guide](../configuration/README.md)
- [Architecture Documentation](../architecture/README.md)  
- [Development Guide](../development/README.md)
- [Deployment Guide](../deployment/README.md)