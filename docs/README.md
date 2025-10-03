# Pasture Documentation

Welcome to the comprehensive documentation for the **Pasture** project - a sophisticated multi-source content scraping system. This documentation provides detailed information about all aspects of the project, from basic usage to advanced development and deployment.

## 📚 Documentation Sections

### [Project Overview](overview.md)
- Introduction and core philosophy
- Key features and capabilities
- Supported pasture types
- Technical foundation and use cases

### [Configuration Guide](configuration/README.md)
- Configuration file structure and syntax
- Global and pasture-specific settings
- Pasture types and their options
- Advanced configuration features
- Auto-detection rules and examples

### [Architecture Documentation](architecture/README.md)
- System architecture and component overview
- Data flow and processing pipeline
- Pasture implementation details
- URL normalization and duplicate detection
- Extension points and performance considerations

### [Development Guide](development/README.md)
- Development environment setup
- Adding new pasture types
- Code style and best practices
- Debugging and troubleshooting
- Performance optimization techniques

### [Deployment Guide](deployment/README.md)
- Local development deployment
- Docker container deployment
- Production deployment considerations
- Monitoring, backup, and maintenance
- Troubleshooting deployment issues

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd pasture

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Configuration
Create `config.ini`:
```ini
[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin
interval = 60
```

### Running the Application
```bash
# Single run
python src/main.py

# Or use Docker
./run-docker.sh
```

## 🎯 Key Features

- **Multi-Source Support**: Modular architecture for Reddit, HackerNews, RSS feeds
- **Intelligent Filtering**: Configurable blacklists and content filtering
- **Duplicate Detection**: Global URL tracking across all sources
- **Scheduled Execution**: Configurable scraping intervals
- **Docker Support**: Containerized deployment with management scripts
- **Robust Error Handling**: Comprehensive fallback mechanisms

## 🔧 Supported Pasture Types

| Type | Description | Auto-detection |
|------|-------------|----------------|
| **Reddit** | Fetches from Reddit JSON endpoints | `reddit.com` in URL |
| **HackerNews** | Uses Hacker News Firebase API | `hackernews` or `news.ycombinator.com` |
| **RSS** | Supports RSS, Atom, and RDF feeds | `.rss`, `.xml`, `/rss`, `/feed` |

## 📁 Project Structure

```
pasture/
├── src/                    # Source code
│   ├── pastures/          # Pasture implementations
│   ├── core/              # Shared utilities
│   └── main.py            # Application entry point
├── docs/                  # This documentation
├── output/               # Generated content
├── config.ini           # Configuration file
└── Dockerfile           # Container configuration
```

## 🤝 Contributing

We welcome contributions! Please see the [Development Guide](development/README.md) for:
- Setting up your development environment
- Adding new pasture types
- Code style guidelines
- Testing procedures

## 📞 Support

- **Issues**: Report bugs or request features via GitHub issues
- **Documentation**: This documentation is your primary resource
- **Community**: Join discussions in the project repository

## 📄 License

This project is provided as-is without warranty. Use responsibly and in compliance with website terms of service.

---

**Next Steps**: 
- Start with the [Project Overview](overview.md) for a high-level understanding
- Check the [Configuration Guide](configuration/README.md) for setup instructions
- Refer to the [Development Guide](development/README.md) for contributing
- Review the [Deployment Guide](deployment/README.md) for production setups