# Deployment Guide

## Overview

Pasture supports multiple deployment options ranging from simple local execution to containerized production deployments. This guide covers all available deployment methods and their respective configurations.

## Deployment Options

### 1. Local Development Deployment
### 2. Docker Container Deployment  
### 3. Docker Compose Deployment
### 4. Production Deployment Considerations

## Local Development Deployment

### Prerequisites

- Python 3.11+
- Firefox browser
- GeckoDriver (automatically managed)

### Installation Steps

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd pasture
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure the Application**
   ```bash
   # Copy and edit configuration
   cp config.ini.example config.ini
   nano config.ini  # Edit with your preferred editor
   ```

3. **Test the Installation**
   ```bash
   # Single run test
   python src/main.py
   
   # Check output
   ls -la output/
   ```

### Local Configuration

#### Output Directory Structure
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

#### File Permissions
Ensure the application has write permissions to the output directory:
```bash
chmod 755 output/
```

## Docker Container Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose (optional, for multi-container setups)

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

### Manual Docker Commands

#### Build the Image
```bash
docker build -t pasture-scraper .
```

#### Run Single Execution
```bash
docker run --rm -v $(pwd)/output:/app/output -v $(pwd)/config.ini:/app/config.ini pasture-scraper
```

#### Run in Background (Daemon Mode)
```bash
docker run -d \
  --name pasture-scraper \
  --restart unless-stopped \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/config.ini:/app/config.ini \
  pasture-scraper
```

### Volume Mounts

- **Output Directory**: `-v $(pwd)/output:/app/output`
- **Configuration**: `-v $(pwd)/config.ini:/app/config.ini`

## Docker Compose Deployment

### Using Docker Compose

The project includes a `docker-compose.yml` file for simplified deployment:

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

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  pasture-scraper:
    build: .
    container_name: pasture-scraper
    restart: unless-stopped
    volumes:
      - ./output:/app/output
      - ./config.ini:/app/config.ini
    environment:
      - TZ=UTC
```

### Custom Docker Compose Configuration

For advanced setups, you can extend the configuration:

```yaml
version: '3.8'

services:
  pasture-scraper:
    build: .
    container_name: pasture-scraper
    restart: unless-stopped
    volumes:
      - ./output:/app/output
      - ./config.ini:/app/config.ini
      - ./logs:/app/logs  # Optional log directory
    environment:
      - TZ=America/New_York
      - LOG_LEVEL=INFO
    networks:
      - pasture-network

  # Optional: Add monitoring service
  monitor:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - pasture-network

networks:
  pasture-network:
    driver: bridge
```

## Production Deployment

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 2GB
- **Storage**: 10GB (depends on content volume)
- **Network**: Stable internet connection

#### Recommended Requirements
- **CPU**: 4 cores
- **RAM**: 4GB
- **Storage**: 50GB+ SSD
- **Network**: 100Mbps+ connection

### Security Considerations

#### File Permissions
```bash
# Secure configuration and output
chmod 600 config.ini
chmod 755 output/
```

#### Network Security
- Use HTTPS for external APIs when available
- Configure firewalls to allow outbound HTTP/HTTPS
- Consider using VPN for sensitive deployments

#### Container Security
```bash
# Run as non-root user in container
docker run --user 1000:1000 pasture-scraper

# Use read-only filesystem where possible
docker run --read-only -v $(pwd)/output:/app/output pasture-scraper
```

### Monitoring and Logging

#### Log Management
```bash
# View recent logs
docker logs --tail 100 pasture-scraper

# Follow logs in real-time
docker logs -f pasture-scraper

# Export logs to file
docker logs pasture-scraper > pasture.log 2>&1
```

#### Health Checks
Add health checks to your Docker configuration:

```yaml
services:
  pasture-scraper:
    # ... existing configuration
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Backup Strategies

#### Configuration Backup
```bash
# Backup configuration
cp config.ini config.ini.backup.$(date +%Y%m%d)

# Version control for configuration
git add config.ini
git commit -m "Update pasture configuration"
```

#### Output Backup
```bash
# Regular backup of output directory
tar -czf pasture-output-$(date +%Y%m%d).tar.gz output/

# Sync to remote storage
rsync -av output/ backup-server:/backups/pasture/
```

#### Processed URLs Backup
```bash
# Critical: Backup processed URLs to avoid re-scraping
cp output/processed_urls.json output/processed_urls.json.backup.$(date +%Y%m%d)
```

### Performance Tuning

#### Memory Optimization
```bash
# Limit container memory
docker run -d --memory=2g --memory-swap=2g pasture-scraper
```

#### CPU Limits
```bash
# Limit CPU usage
docker run -d --cpus=2 pasture-scraper
```

#### Storage Optimization
- Use SSD storage for better I/O performance
- Monitor disk usage and implement cleanup policies
- Consider compressed filesystems for large deployments

## Environment-Specific Configurations

### Development Environment

```ini
# config.ini (Development)
[global]
remove_tags = script, style, noscript, iframe

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election
interval = 30
```

### Staging Environment

```ini
# config.ini (Staging)
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election, spam
interval = 60

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin
interval = 120
```

### Production Environment

```ini
# config.ini (Production)
[global]
remove_tags = script, style, noscript, iframe, button, svg, footer, nav, header, aside

[worldnews]
url = https://www.reddit.com/r/worldnews.json
blacklist = politics, election, spam, offensive
interval = 120

[hackernews_top]
type = hackernews
blacklist = cryptocurrency, bitcoin, ethereum, spam
interval = 180

[tech_blog_rss]
type = rss
url = https://example.com/feed.rss
blacklist = sponsored, advertisement
max_age_days = 7
interval = 240
```

## Troubleshooting Deployment Issues

### Common Issues and Solutions

#### Container Startup Failures

**Problem**: Container exits immediately
**Solution**: Check logs and ensure proper volume mounts
```bash
docker logs pasture-scraper
```

**Problem**: Permission denied errors
**Solution**: Ensure proper file permissions
```bash
chmod 755 output/
chmod 644 config.ini
```

#### Browser/Driver Issues

**Problem**: GeckoDriver not found in container
**Solution**: The CachedGeckoDriverManager should handle this automatically

**Problem**: Firefox crashes in container
**Solution**: Ensure sufficient memory allocation
```bash
docker run -d --memory=2g pasture-scraper
```

#### Network Issues

**Problem**: Cannot reach external URLs
**Solution**: Check network configuration and DNS
```bash
# Test network from container
docker run --rm pasture-scraper ping -c 3 google.com
```

### Debug Mode

For troubleshooting, enable debug logging:

```python
# Temporary modification to src/main.py
root_logger.setLevel(logging.DEBUG)
```

Or set environment variable:
```bash
docker run -e LOG_LEVEL=DEBUG pasture-scraper
```

## Scaling Considerations

### Horizontal Scaling

For high-volume deployments, consider running multiple instances:

```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  pasture-scraper-1:
    build: .
    container_name: pasture-scraper-1
    volumes:
      - ./output-1:/app/output
      - ./config-1.ini:/app/config.ini

  pasture-scraper-2:
    build: .
    container_name: pasture-scraper-2
    volumes:
      - ./output-2:/app/output
      - ./config-2.ini:/app/config.ini
```

### Database Backend (Future Enhancement)

For large-scale deployments, consider replacing file-based storage with a database:

```python
# Example database configuration
DATABASE_URL = "postgresql://user:pass@localhost/pasture"
```

## Maintenance Procedures

### Regular Maintenance

1. **Monitor Disk Usage**
   ```bash
   du -sh output/
   ```

2. **Clean Old Output**
   ```bash
   # Keep only last 30 days
   find output/ -type d -name "202*" -mtime +30 -exec rm -rf {} \;
   ```

3. **Update Dependencies**
   ```bash
   pip install -r requirements.txt --upgrade
   docker compose build --no-cache
   ```

4. **Backup Critical Data**
   ```bash
   # Backup processed URLs
   cp output/processed_urls.json backup/processed_urls.json.$(date +%Y%m%d)
   ```

### Disaster Recovery

1. **Restore Configuration**
   ```bash
   cp config.ini.backup config.ini
   ```

2. **Restore Processed URLs**
   ```bash
   cp backup/processed_urls.json output/processed_urls.json
   ```

3. **Redeploy Application**
   ```bash
   docker compose down
   docker compose up -d
   ```

This deployment guide provides comprehensive instructions for deploying Pasture in various environments, from local development to production systems. Follow these guidelines to ensure reliable and scalable deployments.