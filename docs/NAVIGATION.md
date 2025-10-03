# Documentation Navigation

## 🗂️ Table of Contents

### Getting Started
- [Project Overview](overview.md) - High-level introduction and features
- [Quick Start Guide](../README.md) - Installation and basic usage

### Core Documentation
- [Configuration Guide](configuration/README.md) - Complete configuration reference
- [Architecture Documentation](architecture/README.md) - System design and components
- [Development Guide](development/README.md) - Contributing and extending the project
- [Deployment Guide](deployment/README.md) - Production deployment and operations

### Reference
- [Pasture Types](configuration/README.md#pasture-types) - Supported content sources
- [Configuration Options](configuration/README.md#configuration-options) - All available settings
- [API Reference](development/README.md#adding-new-pasture-types) - Development interfaces

## 🎯 Quick Links

### For New Users
- [Installation Guide](deployment/README.md#local-development-deployment) - Setting up Pasture
- [Basic Configuration](configuration/README.md#basic-structure) - Creating your first config
- [Running the Application](deployment/README.md#local-development-deployment) - Starting the scraper

### For Developers
- [Adding New Pastures](development/README.md#adding-new-pasture-types) - Extending the system
- [Architecture Overview](architecture/README.md#system-overview) - Understanding the codebase
- [Development Setup](development/README.md#development-environment-setup) - Setting up your environment

### For Operations
- [Docker Deployment](deployment/README.md#docker-container-deployment) - Containerized deployment
- [Production Setup](deployment/README.md#production-deployment) - Production considerations
- [Monitoring & Backup](deployment/README.md#monitoring-and-logging) - Operational best practices

## 📚 Documentation Structure

```
docs/
├── overview.md                    # Project introduction and features
├── NAVIGATION.md                 # This file - navigation and TOC
├── README.md                     # Documentation index
├── configuration/
│   └── README.md                 # Complete configuration guide
├── architecture/
│   └── README.md                 # System architecture and design
├── development/
│   └── README.md                 # Development and contribution guide
└── deployment/
    └── README.md                 # Deployment and operations guide
```

## 🔄 Documentation Flow

### Learning Path
1. **Start Here** → [Project Overview](overview.md)
2. **Get Running** → [Configuration Guide](configuration/README.md)
3. **Understand** → [Architecture Documentation](architecture/README.md)
4. **Extend** → [Development Guide](development/README.md)
5. **Deploy** → [Deployment Guide](deployment/README.md)

### Task-Oriented Navigation

#### I want to...
- **Set up Pasture for the first time**
  - [Installation](deployment/README.md#local-development-deployment)
  - [Basic Configuration](configuration/README.md#basic-structure)
  - [Running the Application](deployment/README.md#local-development-deployment)

- **Configure specific pasture types**
  - [Reddit Pastures](configuration/README.md#reddit-pasture)
  - [HackerNews Pastures](configuration/README.md#hackernews-pasture)
  - [RSS Pastures](configuration/README.md#rss-pasture)

- **Deploy to production**
  - [Docker Deployment](deployment/README.md#docker-container-deployment)
  - [Production Configuration](deployment/README.md#production-environment)
  - [Monitoring & Backup](deployment/README.md#monitoring-and-logging)

- **Add a new content source**
  - [Development Setup](development/README.md#development-environment-setup)
  - [Pasture Implementation](development/README.md#adding-new-pasture-types)
  - [Testing & Debugging](development/README.md#testing-new-pastures)

- **Troubleshoot issues**
  - [Common Issues](deployment/README.md#troubleshooting-deployment-issues)
  - [Debug Mode](development/README.md#debug-mode)
  - [Error Handling](architecture/README.md#error-handling--resilience)

## 📖 Documentation Conventions

### Code Blocks
All code examples use the project's actual file paths:
```pasture/src/main.py#L10-20
# Example code with real file paths
def main():
    config = configparser.ConfigParser()
    config.read("config.ini")
```

### Cross-References
- Internal links use relative paths: `[Configuration Guide](configuration/README.md)`
- External links are clearly marked
- Related sections are cross-referenced

### Terminology
- **Pasture**: A content source (Reddit, HackerNews, RSS feed)
- **Configuration**: Settings in `config.ini`
- **Scraping**: Process of fetching and processing content
- **Normalization**: URL processing for duplicate detection

## 🆕 What's New

### Recent Updates
- Multi-source architecture with pasture abstraction
- Intelligent duplicate detection across sources
- Docker containerization with management scripts
- Comprehensive documentation system

### Planned Enhancements
- Additional pasture types (Twitter, custom APIs)
- Advanced filtering and analysis
- Plugin system for extensibility
- Database backend for large-scale deployments

## 🤝 Contributing to Documentation

We welcome improvements to this documentation! Please:
1. Follow the existing structure and conventions
2. Use clear, concise language
3. Include practical examples
4. Cross-reference related sections
5. Test all code examples

## 📞 Support Resources

- **Documentation Issues**: Open an issue in the repository
- **Feature Requests**: Use GitHub issues with the "enhancement" label
- **Questions**: Check existing documentation first, then open a discussion

---

*Last updated: Documentation version 1.0*  
*For the latest updates, check the project repository.*