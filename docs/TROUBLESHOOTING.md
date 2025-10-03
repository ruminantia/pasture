# Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when using the Pasture content scraping system. It covers installation problems, configuration errors, runtime issues, and performance optimization.

## Quick Diagnosis

### Check System Status
```bash
# Check if Pasture is running
ps aux | grep python | grep pasture

# Check Docker container status
docker ps | grep pasture

# Check output directory structure
ls -la output/
```

### Verify Configuration
```bash
# Check config file syntax
python -c "import configparser; configparser.ConfigParser().read('config.ini')"

# Validate pasture types
python -c "from src.pastures import PastureFactory; print('Pasture factory loaded successfully')"
```

## Common Issues and Solutions

### Installation Issues

#### Problem: Python Dependencies Fail to Install
**Symptoms**: `pip install` fails with dependency conflicts or missing packages

**Solutions**:
1. **Use Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Update pip**:
   ```bash
   pip install --upgrade pip
   ```

3. **Install System Dependencies** (Ubuntu/Debian):
   ```bash
   sudo apt-get update
   sudo apt-get install python3-dev python3-venv firefox-esr
   ```

#### Problem: GeckoDriver Installation Fails
**Symptoms**: "GeckoDriver not found" or GitHub API rate limit errors

**Solutions**:
1. **Use Cached Driver Manager**:
   ```python
   # The system automatically uses cached drivers
   # Check cache directory
   ls -la .webdriver_cache/
   ```

2. **Manual GeckoDriver Installation**:
   ```bash
   # Download and install manually
   wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz
   tar -xzf geckodriver-v0.33.0-linux64.tar.gz
   sudo mv geckodriver /usr/local/bin/
   ```

3. **System Firefox Fallback**:
   ```bash
   # Ensure Firefox is installed
   which firefox
   # Output should show Firefox path
   ```

### Configuration Issues

#### Problem: Pasture Type Not Detected
**Symptoms**: "Unknown pasture type" error or wrong pasture behavior

**Solutions**:
1. **Explicit Type Declaration**:
   ```ini
   [my_pasture]
   type = reddit  # Explicitly specify type
   url = https://www.reddit.com/r/worldnews.json
   ```

2. **Check URL Patterns**:
   - Reddit: URL must contain `reddit.com`
   - HackerNews: URL contains `hackernews` or `news.ycombinator.com`
   - RSS: URL ends with `.rss`, `.xml` or contains `/rss/`, `/feed/`

3. **Debug Auto-detection**:
   ```python
   # Add debug logging to PastureFactory._determine_pasture_type
   print(f"URL: {url}, Detected type: {pasture_type}")
   ```

#### Problem: Blacklist Not Working
**Symptoms**: Posts with blacklisted terms are still being processed

**Solutions**:
1. **Check Case Sensitivity**:
   ```ini
   # Blacklist is case-insensitive
   blacklist = Trump, COVID, election
   ```

2. **Verify Term Matching**:
   - Terms are matched anywhere in the title
   - Use specific terms to avoid false positives
   - Check for extra spaces or special characters

3. **Debug Filtering**:
   ```python
   # Add debug output to filter_posts method
   print(f"Checking title: {title}")
   print(f"Blacklist terms: {blacklist}")
   ```

### Runtime Issues

#### Problem: Browser/Driver Crashes
**Symptoms**: Selenium timeouts, Firefox crashes, or "WebDriverException"

**Solutions**:
1. **Increase Timeouts**:
   ```python
   # In create_driver_with_retry function
   driver.implicitly_wait(30)  # Increase from default
   driver.set_page_load_timeout(60)
   ```

2. **Memory Optimization**:
   ```bash
   # Run with memory limits in Docker
   docker run -d --memory=2g pasture-scraper
   ```

3. **Headless Mode Check**:
   ```python
   # Ensure headless mode is properly configured
   options.add_argument("--headless")
   options.add_argument("--no-sandbox")
   options.add_argument("--disable-dev-shm-usage")
   ```

#### Problem: Network Timeouts
**Symptoms**: "Connection timeout", "Read timeout", or slow scraping

**Solutions**:
1. **Adjust Timeout Settings**:
   ```python
   # In fetch_posts methods
   response = requests.get(url, timeout=60)  # Increase timeout
   ```

2. **Implement Retry Logic**:
   ```python
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

3. **Check Network Connectivity**:
   ```bash
   # Test connectivity to target sites
   curl -I https://www.reddit.com/r/worldnews.json
   ping -c 3 news.ycombinator.com
   ```

#### Problem: Duplicate Content
**Symptoms**: Same content scraped multiple times from different sources

**Solutions**:
1. **Check URL Normalization**:
   ```python
   # Test URL normalization
   from core.scraper import normalize_url
   print(normalize_url("https://example.com/article?utm_source=reddit&ref=twitter"))
   # Should output: https://example.com/article
   ```

2. **Verify Processed URLs File**:
   ```bash
   # Check if processed_urls.json is being updated
   cat output/processed_urls.json | wc -l
   ```

3. **Manual URL Hash Check**:
   ```python
   from pastures.base import Pasture
   url1 = "https://example.com/article?utm_source=reddit"
   url2 = "https://example.com/article?ref=twitter"
   print(Pasture.hash_url(url1) == Pasture.hash_url(url2))  # Should be True
   ```

### Docker Issues

#### Problem: Container Exits Immediately
**Symptoms**: Docker container starts and stops without processing

**Solutions**:
1. **Check Volume Mounts**:
   ```bash
   # Verify volumes are properly mounted
   docker run --rm -v $(pwd)/output:/app/output -v $(pwd)/config.ini:/app/config.ini pasture-scraper
   ```

2. **Check File Permissions**:
   ```bash
   # Ensure output directory is writable
   chmod 755 output/
   chmod 644 config.ini
   ```

3. **Run with Interactive Shell**:
   ```bash
   # Debug container startup
   docker run -it --entrypoint /bin/bash pasture-scraper
   ```

#### Problem: Firefox Not Available in Container
**Symptoms**: "Firefox not found" or browser initialization failures

**Solutions**:
1. **Rebuild Docker Image**:
   ```bash
   docker build --no-cache -t pasture-scraper .
   ```

2. **Check Dockerfile Firefox Installation**:
   ```dockerfile
   # Ensure Firefox is properly installed
   RUN apt-get update && apt-get install -y firefox-esr
   ```

3. **Use System Fallback**:
   ```python
   # The system should automatically fall back to system Firefox
   # Check logs for fallback messages
   ```

### Performance Issues

#### Problem: High Memory Usage
**Symptoms**: System becomes slow, memory usage spikes

**Solutions**:
1. **Limit Concurrent Scraping**:
   ```python
   # Process posts in smaller batches
   for i in range(0, len(posts), 10):  # Process 10 at a time
       batch = posts[i:i+10]
       # Process batch
   ```

2. **Optimize Browser Usage**:
   ```python
   # Reuse browser instances when possible
   # Close browsers promptly after use
   driver.quit()  # Ensure proper cleanup
   ```

3. **Monitor Resource Usage**:
   ```bash
   # Monitor memory usage
   docker stats pasture-scraper
   # Or for local execution
   top -p $(pgrep -f "python.*main.py")
   ```

#### Problem: Slow Scraping
**Symptoms**: Long processing times, timeouts

**Solutions**:
1. **Optimize Tag Removal**:
   ```ini
   # Remove only necessary tags
   remove_tags = script, style, noscript, iframe  # Minimal set
   ```

2. **Increase Timeouts**:
   ```python
   # In scrape_url function
   driver.set_page_load_timeout(120)  # Increase page load timeout
   ```

3. **Use Fallback Scraping**:
   ```python
   # The system automatically falls back to requests-based scraping
   # when Selenium fails
   ```

### Output Issues

#### Problem: No Output Files Generated
**Symptoms**: Process runs but no Markdown files are created

**Solutions**:
1. **Check Output Directory**:
   ```bash
   # Verify output directory exists and is writable
   ls -la output/
   touch output/test.txt  # Test write permissions
   ```

2. **Check Pasture Configuration**:
   ```ini
   # Ensure pastures have valid URLs and content
   [test_pasture]
   url = https://www.reddit.com/r/worldnews.json
   # Test with a known working pasture
   ```

3. **Enable Debug Logging**:
   ```python
   # Temporary modification to see scraping activity
   root_logger.setLevel(logging.DEBUG)
   ```

#### Problem: Incomplete or Malformed Content
**Symptoms**: Markdown files contain incomplete content or formatting issues

**Solutions**:
1. **Adjust Tag Removal**:
   ```ini
   # Keep more tags for better content preservation
   remove_tags = script, style, noscript  # Minimal removal
   ```

2. **Check HTML Processing**:
   ```python
   # Test HTML processing separately
   from core.scraper import post_process_html
   test_html = "<div>Test content</div>"
   processed = post_process_html(test_html, ["script", "style"])
   print(processed)
   ```

3. **Verify Markdown Conversion**:
   ```python
   # Test markdown conversion
   from markdownify import markdownify as md
   test_html = "<h1>Title</h1><p>Content</p>"
   markdown = md(test_html)
   print(markdown)
   ```

## Advanced Troubleshooting

### Debug Mode

Enable comprehensive debugging to identify issues:

```python
# In src/main.py, modify logging configuration
root_logger.setLevel(logging.DEBUG)

# Or set via environment variable
import os
os.environ['LOG_LEVEL'] = 'DEBUG'
```

### Network Debugging

```bash
# Check network connectivity from container
docker run --rm --network host pasture-scraper ping -c 3 google.com

# Test specific endpoints
docker run --rm pasture-scraper curl -I https://www.reddit.com/r/worldnews.json
```

### Browser Debugging

```python
# Enable browser debugging in development
options.add_argument("--headless")  # Remove for visible browser
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Add screenshot capture for debugging
driver.save_screenshot("debug_screenshot.png")
```

### Performance Profiling

```python
import time
import cProfile

def profile_scraping():
    start_time = time.time()
    # Your scraping code here
    end_time = time.time()
    print(f"Scraping took {end_time - start_time:.2f} seconds")

# Or use cProfile for detailed profiling
cProfile.run('profile_scraping()')
```

## Getting Help

If you're still experiencing issues:

1. **Check Logs**: Review application logs for error messages
2. **Review Documentation**: Consult the main documentation for configuration examples
3. **Community Support**: Check the project repository for existing issues or create a new one
4. **Provide Details**: When seeking help, include:
   - Configuration file (redacted if necessary)
   - Error logs and stack traces
   - System environment details
   - Steps to reproduce the issue

Remember to always respect website terms of service and rate limits when troubleshooting scraping issues.