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

from core.stats import StatsTracker


# Set up logging - use centralized configuration from main
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
                logger.info("📦 Using cached GeckoDriver")
                return str(cached_path)

            # If no cache, download and cache it
            logger.info("⬇️  Downloading GeckoDriver")
            driver_path = self.manager.install()
            self._cache_driver(driver_path)
            return driver_path

        except Exception as e:
            logger.warning(f"⚠️  Driver download failed: {e}")
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
        logger.info("🦊 Falling back to system Firefox")
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
                logger.info(f"✅ Found Firefox at: {path}")
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
                    logger.info(f"✅ Found Firefox via PATH: {firefox_path}")
                    return "geckodriver"
        except Exception as e:
            logger.warning(f"⚠️  Error finding Firefox: {e}")

        logger.warning("⚠️  No Firefox binary found")
        return "geckodriver"  # Still try system binary as last resort


def normalize_url(url: str) -> str:
    """Normalize URL by removing tracking parameters and standardizing format.

    Args:
        url: URL to normalize

    Returns:
        Normalized URL without tracking parameters
    """
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

    try:
        parsed = urlparse(url)

        # Common tracking parameters to remove
        tracking_params = [
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "ref",
            "source",
            "medium",
            "campaign",
            "content",
            "term",
            "fbclid",
            "gclid",
            "msclkid",
            "trk",
            "tracking",
            "si",
            "igshid",
            "feature",
            "share",
            "mc_cid",
            "mc_eid",
            "_hsenc",
            "_hsmi",
            "hsCtaTracking",
            "mkt_tok",
            "pk_source",
            "pk_medium",
            "pk_campaign",
            "pk_keyword",
            "pk_content",
            "ncid",
            "CMP",
            "cmpid",
            "ito",
            "ito",
            "nr_email_referer",
            "via",
            "from",
            "shared",
            "fb_action_ids",
            "fb_ref",
            "wt_mc",
            "wt_zmc",
            "wt_zsrc",
            "CNDID",
            "mbid",
            "linkCode",
            "tag",
            "linkId",
            "creativeASIN",
            "ascsubtag",
            "psc",
            "ved",
            "ei",
            "gs_lcp",
            "oq",
            "aqs",
            "sourceid",
            "ie",
            "rlz",
            "gws_rd",
            "sa",
            "esrc",
            "form",
        ]

        # Remove tracking parameters from query string
        if parsed.query:
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            filtered_params = {}

            for key, value in query_params.items():
                # Keep parameter if it's not a tracking parameter
                if key.lower() not in [p.lower() for p in tracking_params]:
                    filtered_params[key] = value[0] if len(value) == 1 else value

            # Rebuild query string without tracking parameters
            new_query = urlencode(filtered_params, doseq=True)
        else:
            new_query = ""

        # Reconstruct URL without tracking parameters
        normalized = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
        )

        # Remove trailing slash for consistency
        if normalized.endswith("/") and len(normalized) > 1:
            normalized = normalized.rstrip("/")

        return normalized

    except Exception:
        # If normalization fails, return original URL
        return url


def hash_url(url: str) -> str:
    """Hash a URL using SHA256 after normalization.

    Args:
        url: URL to hash

    Returns:
        SHA256 hash of the normalized URL
    """
    normalized_url = normalize_url(url)
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()


def post_process_html(file_path: str, tags_to_remove: List[str], blacklist: List[str] = None) -> None:
    """Post-process an HTML file using BeautifulSoup and converts it to Markdown.

    Args:
        file_path: Path to the HTML file
        tags_to_remove: List of HTML tag names to remove
        blacklist: Optional list of blacklist terms to check against scraped content
    """
    filename = os.path.basename(file_path)
    logger.info(f"🔄 Processing {filename}")
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

        # Post-scrape blacklist check on the actual content
        if blacklist:
            # Get the first line (title) from the markdown
            with open(md_file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()

            # Check if the title matches any blacklist terms
            title_lower = first_line.lower()
            blacklist_matches = [term for term in blacklist if term.lower() in title_lower]

            if blacklist_matches:
                logger.info(f"🚫 Post-scrape blacklist match: '{first_line[:60]}...' matched terms: {blacklist_matches}")
                os.remove(md_file_path)
                logger.info(f"🗑️  Deleted {os.path.basename(md_file_path)} due to blacklist match")
                return  # Skip the rest of processing

        # Remove the original HTML file
        os.remove(file_path)

        logger.info(f"✅ Processed {filename}")

    except Exception as e:
        logger.error(f"❌ Failed to process {filename}: {e}")
        # Keep the original HTML file if processing fails
        if os.path.exists(file_path):
            logger.info(f"📁 Keeping original HTML file")


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
                    logger.info(f"🦊 Using Firefox: {firefox_path}")
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
                            logger.info(f"🦊 Using Firefox from PATH")
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
            logger.warning(f"⚠️  Driver attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                logger.info(f"⏳ Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error("❌ All driver attempts failed")
                raise WebDriverException(
                    f"Failed to create Firefox driver after {max_retries} attempts: {e}"
                )


def scrape_url(url: str, output_dir: str, tags_to_remove: List[str], blacklist: List[str] = None) -> bool:
    """Scrapes the content of a URL using Selenium.

    Args:
        url: URL to scrape
        output_dir: Directory to save the scraped content
        tags_to_remove: List of HTML tags to remove during processing
        blacklist: Optional list of blacklist terms to check against scraped content

    Returns:
        True if scraping was successful, False otherwise
    """
    # Skip media URLs that don't contain HTML content
    if is_media_url(url):
        logger.info(f"📷 Skipping media: {url}")
        return False
    driver = None
    try:
        logger.info(f"🌐 Scraping: {url}")
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

        post_process_html(file_path, tags_to_remove, blacklist)
        logger.info(f"✅ Scraped: {url}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to scrape: {url}")
        # Try fallback for timeout, DNS, or driver issues
        if any(
            error_type in str(e).lower()
            for error_type in ["timeout", "dns", "driver", "firefox", "navigation"]
        ):
            logger.info("🔄 Attempting fallback method")
            return fallback_scrape_url(url, output_dir, tags_to_remove)
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"⚠️  Error closing driver: {e}")


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
            logger.warning(f"⚠️  Error loading processed URLs: {e}")
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
        logger.error(f"❌ Error saving processed URLs: {e}")


def scrape_pasture(pasture, base_output_dir: str, processed_urls: Set[str], stats_tracker: StatsTracker = None) -> Set[str]:
    """Scrape a single pasture.

    Args:
        pasture: Pasture instance to scrape
        base_output_dir: Base output directory
        processed_urls: Set of already processed URLs
        stats_tracker: Optional StatsTracker instance for collecting statistics

    Returns:
        Updated set of processed URLs
    """
    try:
        # Add source to stats
        if stats_tracker:
            stats_tracker.add_source(pasture.name)

        posts = pasture.fetch_posts()

        # Pass stats tracker to filter_posts so it can track rejections
        if hasattr(pasture, 'set_stats_tracker'):
            pasture.set_stats_tracker(stats_tracker)

        filtered_posts = pasture.filter_posts(posts)

        output_dir = pasture.get_output_directory(base_output_dir)
        tags_to_remove = pasture.get_tags_to_remove()
        blacklist = pasture.get_blacklist()

        new_urls_scraped = 0
        for post in filtered_posts:
            external_url = pasture.get_url_from_post(post)

            # Skip media URLs early to avoid unnecessary processing
            if is_media_url(external_url):
                logger.info(f"📷 Skipping media: {external_url}")
                continue

            if pasture.should_scrape_url(external_url, processed_urls):
                if scrape_url(external_url, output_dir, tags_to_remove, blacklist):
                    pasture.mark_url_processed(external_url, processed_urls)
                    new_urls_scraped += 1
                    # Track successful scrape
                    if stats_tracker:
                        stats_tracker.increment_scraped(pasture.name)
                else:
                    logger.warning(f"❌ Failed: {external_url}")
                    # Try fallback method
                    if fallback_scrape_url(external_url, output_dir, tags_to_remove, blacklist):
                        pasture.mark_url_processed(external_url, processed_urls)
                        new_urls_scraped += 1
                        # Track successful scrape
                        if stats_tracker:
                            stats_tracker.increment_scraped(pasture.name)
            else:
                logger.info(f"⏭️  Skipping duplicate: {external_url}")
                # Track duplicate
                if stats_tracker:
                    stats_tracker.increment_duplicate()

        logger.info(f"📊 {pasture.name}: {new_urls_scraped} new URLs")
        return processed_urls

    except Exception as e:
        logger.error(f"❌ Error in {pasture.name}: {e}")
        if stats_tracker:
            stats_tracker.increment_error()
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


def fallback_scrape_url(url: str, output_dir: str, tags_to_remove: List[str], blacklist: List[str] = None) -> bool:
    """Fallback scraping method using requests + BeautifulSoup for simple sites.

    Args:
        url: URL to scrape
        output_dir: Directory to save the scraped content
        tags_to_remove: List of HTML tags to remove during processing
        blacklist: Optional list of blacklist terms to check against scraped content

    Returns:
        True if scraping was successful, False otherwise

    This is used when Selenium fails due to driver issues.
    """
    try:
        logger.info(f"🔄 Fallback scraping: {url}")

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
        post_process_html(file_path, tags_to_remove, blacklist)
        logger.info(f"✅ Fallback scraped: {url}")
        return True

    except Exception as e:
        logger.error(f"❌ Fallback failed: {url}")
        return False
