import hashlib
import json
import os
import time
import logging
from datetime import datetime
from typing import List, Set
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.firefox import GeckoDriverManager


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CachedGeckoDriverManager:
    """A cached version of GeckoDriverManager to avoid GitHub API rate limits."""

    def __init__(self, cache_dir: str = ".webdriver_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "geckodriver_version.txt"
        self.manager = GeckoDriverManager()

    def install(self) -> str:
        """Install GeckoDriver with caching to avoid GitHub API calls."""
        try:
            # Try to use cached driver first
            cached_path = self._get_cached_driver()
            if cached_path:
                logger.info("Using cached GeckoDriver")
                return str(cached_path)

            # If no cache, download and cache it
            logger.info("Downloading GeckoDriver (this may hit GitHub API limits)")
            driver_path = self.manager.install()
            self._cache_driver(driver_path)
            return driver_path

        except Exception as e:
            logger.warning(f"Failed to use webdriver-manager: {e}")
            # Fallback to system Firefox
            return self._fallback_to_system_firefox()

    def _get_cached_driver(self) -> Path | None:
        """Get cached driver path if available and valid."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                cached_path = Path(f.read().strip())

            if cached_path.exists() and cached_path.is_file():
                return cached_path
        except Exception:
            pass

        return None

    def _cache_driver(self, driver_path: str) -> None:
        """Cache the driver path for future use."""
        try:
            with open(self.cache_file, "w") as f:
                f.write(driver_path)
        except Exception as e:
            logger.warning(f"Failed to cache driver path: {e}")

    def _fallback_to_system_firefox(self) -> str:
        """Fallback to using system Firefox binary."""
        logger.info("Falling back to system Firefox")
        # Check for common Firefox binary locations
        firefox_paths = [
            "/usr/bin/firefox-bin",  # Your system path
            "/usr/bin/firefox",
            "/usr/local/bin/firefox",
            "/opt/firefox/firefox",
            "/usr/bin/firefox-esr",  # Common in Docker
        ]

        for path in firefox_paths:
            if os.path.exists(path):
                logger.info(f"Found Firefox at: {path}")
                return "geckodriver"  # This tells Selenium to use system binary

        # Try to find Firefox using which command
        import subprocess

        try:
            result = subprocess.run(
                ["which", "firefox"], capture_output=True, text=True
            )
            if result.returncode == 0:
                firefox_path = result.stdout.strip()
                if os.path.exists(firefox_path):
                    logger.info(f"Found Firefox via PATH: {firefox_path}")
                    return "geckodriver"
        except Exception as e:
            logger.warning(f"Error finding Firefox via which: {e}")

        logger.warning("No Firefox binary found in common locations")
        return "geckodriver"  # Still try system binary as last resort


def hash_url(url: str) -> str:
    """Hash a URL using SHA256.

    Args:
        url: URL to hash

    Returns:
        SHA256 hash of the URL
    """
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def post_process_html(file_path: str, tags_to_remove: List[str]) -> None:
    """Cleans up an HTML file using BeautifulSoup and converts it to Markdown.

    Args:
        file_path: Path to the HTML file
        tags_to_remove: List of HTML tag names to remove
    """
    logger.info(f"Post-processing {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Remove specified tags
        for tag in soup(tags_to_remove):
            tag.decompose()

        # Remove all attributes from all tags except for href and src
        for tag in soup.find_all(True):
            if tag.name == "a":
                if "href" in tag.attrs:
                    href = tag["href"]
                    if href.startswith("http"):
                        tag["href"] = "/" + href.split("/", 3)[-1]
            elif tag.name == "img":
                if "src" in tag.attrs:
                    src = tag["src"]
                    tag["src"] = os.path.basename(src)
            else:
                tag.attrs = {}

        # Get the story itself with minimal html tags for structure
        if soup.body:
            body_content = soup.body.prettify()
        else:
            body_content = ""

        if soup.title:
            title_content = soup.title.prettify()
        else:
            title_content = ""

        html_content = title_content + body_content
        markdown_content = md(html_content)

        # Save the markdown content to a new file
        md_file_path = os.path.splitext(file_path)[0] + ".md"
        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Remove the original HTML file
        os.remove(file_path)

        logger.info(f"Finished post-processing {file_path}")

    except Exception as e:
        logger.error(f"Error post-processing {file_path}: {e}")
        # Keep the original HTML file if processing fails
        if os.path.exists(file_path):
            logger.info(f"Keeping original HTML file: {file_path}")


def create_driver_with_retry(max_retries: int = 3) -> webdriver.Firefox:
    """Create a Firefox driver with retry logic for rate limiting.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Firefox WebDriver instance

    Raises:
        WebDriverException: If all retries fail
    """
    cached_manager = CachedGeckoDriverManager()

    for attempt in range(max_retries):
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Use cached driver manager
            driver_path = cached_manager.install()

            # Always set Firefox binary location explicitly
            firefox_paths = [
                "/usr/bin/firefox-bin",  # Your system path
                "/usr/bin/firefox",
                "/usr/local/bin/firefox",
                "/opt/firefox/firefox",
                "/usr/bin/firefox-esr",  # Common in Docker
            ]

            for firefox_path in firefox_paths:
                if os.path.exists(firefox_path):
                    logger.info(f"Using Firefox binary: {firefox_path}")
                    options.binary_location = firefox_path
                    break

            # Try to find Firefox using which command as last resort
            if not options.binary_location:
                import subprocess

                try:
                    result = subprocess.run(
                        ["which", "firefox"], capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        firefox_path = result.stdout.strip()
                        if os.path.exists(firefox_path):
                            logger.info(f"Using Firefox from PATH: {firefox_path}")
                            options.binary_location = firefox_path
                except Exception:
                    pass

            if driver_path == "geckodriver":
                # Use system binary
                driver = webdriver.Firefox(options=options)
            else:
                # Use downloaded driver
                service = Service(driver_path)
                driver = webdriver.Firefox(service=service, options=options)

            return driver

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to create driver: {e}")
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("All attempts to create driver failed")
                raise WebDriverException(
                    f"Failed to create Firefox driver after {max_retries} attempts: {e}"
                )


def scrape_url(url: str, output_dir: str, tags_to_remove: List[str]) -> bool:
    """Scrapes the content of a URL using Selenium.

    Args:
        url: URL to scrape
        output_dir: Directory to save the scraped content
        tags_to_remove: List of HTML tags to remove during processing

    Returns:
        True if scraping was successful, False otherwise
    """
    # Skip media URLs that don't contain HTML content
    if is_media_url(url):
        logger.info(f"Skipping media URL: {url}")
        return False
    driver = None
    try:
        logger.info(f"Scraping {url}")
        driver = create_driver_with_retry()

        # Set reasonable timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(15)

        driver.get(url)
        time.sleep(8)  # Allow more time for the page to load

        html = driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"
        )

        file_path = os.path.join(output_dir, f"{hash_url(url)}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

        post_process_html(file_path, tags_to_remove)
        logger.info(f"Successfully scraped {url}")
        return True

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        # Try fallback for timeout, DNS, or driver issues
        if any(
            error_type in str(e).lower()
            for error_type in ["timeout", "dns", "driver", "firefox", "navigation"]
        ):
            logger.info("Attempting fallback scraping method")
            return fallback_scrape_url(url, output_dir, tags_to_remove)
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")


def load_processed_urls(processed_urls_file: str) -> Set[str]:
    """Load processed URLs from a JSON file.

    Args:
        processed_urls_file: Path to the JSON file containing processed URLs

    Returns:
        Set of processed URL hashes
    """
    if os.path.exists(processed_urls_file):
        try:
            with open(processed_urls_file, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning(f"Error loading processed URLs: {e}")
            return set()
    else:
        return set()


def save_processed_urls(processed_urls_file: str, processed_urls: Set[str]) -> None:
    """Save processed URLs to a JSON file.

    Args:
        processed_urls_file: Path to the JSON file to save to
        processed_urls: Set of processed URL hashes to save
    """
    try:
        with open(processed_urls_file, "w") as f:
            json.dump(list(processed_urls), f)
    except Exception as e:
        logger.error(f"Error saving processed URLs: {e}")


def scrape_pasture(pasture, base_output_dir: str, processed_urls: Set[str]) -> Set[str]:
    """Scrape a single pasture.

    Args:
        pasture: Pasture instance to scrape
        base_output_dir: Base output directory
        processed_urls: Set of already processed URLs

    Returns:
        Updated set of processed URLs
    """
    try:
        posts = pasture.fetch_posts()
        filtered_posts = pasture.filter_posts(posts)

        output_dir = pasture.get_output_directory(base_output_dir)
        tags_to_remove = pasture.get_tags_to_remove()

        new_urls_scraped = 0
        for post in filtered_posts:
            external_url = pasture.get_url_from_post(post)

            # Skip media URLs early to avoid unnecessary processing
            if is_media_url(external_url):
                logger.info(f"Skipping media URL: {external_url}")
                continue

            if pasture.should_scrape_url(external_url, processed_urls):
                if scrape_url(external_url, output_dir, tags_to_remove):
                    pasture.mark_url_processed(external_url, processed_urls)
                    new_urls_scraped += 1
                else:
                    logger.warning(f"Failed to scrape {external_url}")
            else:
                logger.info(f"Skipping duplicate URL: {external_url}")

        logger.info(f"Scraped {new_urls_scraped} new URLs from {pasture.name}")
        return processed_urls

    except Exception as e:
        logger.error(f"Error scraping pasture {pasture.name}: {e}")
        return processed_urls


def is_media_url(url: str) -> bool:
    """Check if URL points to media content that shouldn't be scraped as HTML."""
    media_extensions = [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".webm",
    ]
    media_domains = ["v.redd.it", "i.redd.it"]

    # Check file extensions
    if any(url.lower().endswith(ext) for ext in media_extensions):
        return True

    # Check domains
    if any(domain in url for domain in media_domains):
        return True

    return False


def fallback_scrape_url(url: str, output_dir: str, tags_to_remove: List[str]) -> bool:
    """Fallback scraping method using requests + BeautifulSoup for simple sites.

    This is used when Selenium fails due to driver issues.
    """
    try:
        logger.info(f"Attempting fallback scrape for {url}")

        # Skip media URLs in fallback too
        if is_media_url(url):
            logger.info(f"Skipping media URL in fallback: {url}")
            return False

        # Add headers to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

        response = requests.get(url, headers=headers, timeout=45)
        response.raise_for_status()

        # Save the HTML content
        file_path = os.path.join(output_dir, f"{hash_url(url)}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        # Process the HTML
        post_process_html(file_path, tags_to_remove)
        logger.info(f"Successfully fallback-scraped {url}")
        return True

    except Exception as e:
        logger.error(f"Fallback scraping failed for {url}: {e}")
        return False
