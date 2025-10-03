# 🐮 Pasture - Multi-Source Content Aggregator

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Pasture** is a sophisticated content scraping and aggregation engine designed to systematically harvest raw web content from a wide array of sources. Its core function is to ingest this diverse and often messy HTML and transform it into a standardized, **rough, LLM-readable Markdown** format. This process involves stripping away non-essential visual clutter like complex navigation, ads, and scripts, while preserving the core textual and structural information—headings, lists, paragraphs, and links—in a way that is optimally structured for machine parsing.

It is crucial to understand that the goal of Pasture is not to generate polished, user-facing Markdown documents. Instead, its purpose is to act as the foundational first step in a larger data pipeline, efficiently gathering a massive corpus of raw, semi-structured web content. This aggregated data serves as the essential raw material for subsequent, more complex LLM pipelines.


## ✨ Features

- **🌐 Multi-Source Support** - Reddit, HackerNews, RSS feeds, and extensible architecture
- **🧠 Intelligent Deduplication** - Global URL tracking prevents duplicate content across sources
- **⚡ Smart Filtering** - Configurable blacklists and content filtering
- **📝 Clean Output** - Converts web content to readable Markdown format
- **⏰ Scheduled Scraping** - Configurable intervals for continuous operation
- **🐳 Docker Ready** - Containerized deployment with management scripts
- **🔧 Extensible** - Easy to add new content sources and custom processing

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ or Docker
- Firefox browser (for local deployment)

### Installation & Running

**Option 1: Local Python**
```bash
# Clone and setup
git clone https://github.com/ruminantia/pasture.git
cd pasture

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run once
python src/main.py
```

**Option 2: Docker (Recommended)**
```bash
# Use the management script
chmod +x run-docker.sh

# Run once
./run-docker.sh

# Or run in background
./run-docker.sh start

# View logs
./run-docker.sh logs
```

## ⚙️ Configuration

Create `config.ini` to define your content sources:

```ini
[global]
remove_tags = script, style, noscript, iframe

# Reddit pastures (auto-detected)
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30

[technology]
url = https://www.reddit.com/r/technology.json
blacklist = cryptocurrency, bitcoin
interval = 60

# HackerNews pasture
[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin
interval = 60

# RSS pasture
[tech_blog_rss]
type = rss
url = https://example.com/feed.rss
max_age_days = 7
interval = 120
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `type` | Pasture type (reddit, hackernews, rss) | Auto-detected |
| `url` | Source URL or API endpoint | Required |
| `blacklist` | Comma-separated terms to exclude | - |
| `interval` | Scraping interval in minutes | 60 |
| `max_age_days` | Maximum age for RSS items (RSS only) | - |

## 🏗️ Architecture

Pasture uses a modular architecture with pasture implementations for different content sources:

```
pasture/
├── src/
│   ├── pastures/           # Pasture implementations
│   │   ├── base/          # Abstract Pasture class
│   │   ├── reddit/        # Reddit implementation
│   │   ├── hackernews/    # HackerNews implementation
│   │   └── rss/           # RSS implementation
│   ├── core/              # Shared utilities
│   └── main.py            # Application entry point
├── output/                # Generated content
└── config.ini            # Configuration
```

### How It Works

1. **Content Fetching** - Pastures fetch posts from configured sources
2. **Filtering** - Apply blacklists and pasture-specific criteria
3. **URL Processing** - Normalize URLs and check for duplicates
4. **Web Scraping** - Use headless Firefox to fetch external content
5. **Content Processing** - Clean HTML and convert to Markdown
6. **Storage** - Save organized content with URL tracking

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Using Management Script
```bash
./run-docker.sh start    # Start in background
./run-docker.sh stop     # Stop container
./run-docker.sh logs     # View logs
./run-docker.sh status   # Check status
./run-docker.sh help     # Show all commands
```

## 📁 Output Structure

```
output/
├── 2024-01-15/           # Date-based organization
│   ├── worldnews/        # Pasture-specific directories
│   │   ├── abc123def456.md
│   │   └── xyz789uvw012.md
│   └── hackernews_top/
│       └── def456ghi789.md
└── processed_urls.json   # Global URL tracking
```

Each URL is stored as a Markdown file with a SHA256 hash of the normalized URL as the filename.

## 🔧 Advanced Usage

### Adding Custom Pasture Types

1. Create a class inheriting from `Pasture` base class
2. Implement required methods: `fetch_posts()`, `filter_posts()`, `get_url_from_post()`
3. Register with `PastureFactory.register_pasture_type()`

Example:
```python
from pastures.base import Pasture

class CustomPasture(Pasture):
    def fetch_posts(self) -> List[Dict[str, Any]]:
        # Your fetching logic
        pass

    # ... implement other required methods
```

### Tag Removal Configuration

Use Gentoo-style override syntax for HTML tag removal:

```ini
[global]
remove_tags = script, style, noscript, iframe, footer, nav

[my_pasture]
# Add tags to global set
remove_tags = header, aside

# Or remove tags from global set
remove_tags = -nav, -footer
```

## 🛠️ Development

### Setting Up Development Environment
```bash
git clone https://github.com/ruminantia/pasture.git
cd pasture
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
```bash
# Add your test commands here
python -m pytest tests/
```

## 📚 Documentation

For comprehensive documentation, see the [`docs/`](docs/) directory:

- [📖 Project Overview](docs/overview.md)
- [⚙️ Configuration Guide](docs/configuration/README.md)
- [🏗️ Architecture](docs/architecture/README.md)
- [🔧 Development Guide](docs/development/README.md)
- [🐳 Deployment Guide](docs/deployment/README.md)
- [❓ FAQ](docs/FAQ.md)
- [🐛 Troubleshooting](docs/TROUBLESHOOTING.md)

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/development/README.md) for:

- Setting up your development environment
- Code style guidelines
- Adding new pasture types
- Testing procedures

## ⚠️ Disclaimer

This tool is intended for educational and research purposes. Users are responsible for:

- Complying with API terms of service for each source
- Respecting website robots.txt files
- Obtaining proper permissions for web scraping
- Using the tool ethically and legally

## 📄 License

This project is provided as-is under the MIT License. Use responsibly and in compliance with website terms of service.

---

**Happy Scraping!** 🎉 If you find Pasture useful, please consider giving it a ⭐ on GitHub!
