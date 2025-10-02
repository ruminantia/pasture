import hashlib
import json
import os
import time
from datetime import datetime
from typing import List, Set

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


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
    print(f"Post-processing {file_path}")
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

    print(f"Finished post-processing {file_path}")


def scrape_url(url: str, output_dir: str, tags_to_remove: List[str]) -> bool:
    """Scrapes the content of a URL using Selenium.

    Args:
        url: URL to scrape
        output_dir: Directory to save the scraped content
        tags_to_remove: List of HTML tags to remove during processing

    Returns:
        True if scraping was successful, False otherwise
    """
    try:
        options = Options()
        options.add_argument("--headless")
        # Use webdriver_manager to automatically manage GeckoDriver
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.get(url)
        time.sleep(5)  # Allow time for the page to load
        html = driver.execute_script(
            "return document.getElementsByTagName('html')[0].innerHTML"
        )
        file_path = os.path.join(output_dir, f"{hash_url(url)}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        driver.quit()
        post_process_html(file_path, tags_to_remove)
        return True
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return False


def load_processed_urls(processed_urls_file: str) -> Set[str]:
    """Load processed URLs from a JSON file.

    Args:
        processed_urls_file: Path to the JSON file containing processed URLs

    Returns:
        Set of processed URL hashes
    """
    if os.path.exists(processed_urls_file):
        with open(processed_urls_file, "r") as f:
            return set(json.load(f))
    else:
        return set()


def save_processed_urls(processed_urls_file: str, processed_urls: Set[str]) -> None:
    """Save processed URLs to a JSON file.

    Args:
        processed_urls_file: Path to the JSON file to save to
        processed_urls: Set of processed URL hashes to save
    """
    with open(processed_urls_file, "w") as f:
        json.dump(list(processed_urls), f)


def scrape_pasture(pasture, base_output_dir: str, processed_urls: Set[str]) -> Set[str]:
    """Scrape a single pasture.

    Args:
        pasture: Pasture instance to scrape
        base_output_dir: Base output directory
        processed_urls: Set of already processed URLs

    Returns:
        Updated set of processed URLs
    """
    posts = pasture.fetch_posts()
    filtered_posts = pasture.filter_posts(posts)

    output_dir = pasture.get_output_directory(base_output_dir)
    tags_to_remove = pasture.get_tags_to_remove()

    new_urls_scraped = 0
    for post in filtered_posts:
        external_url = pasture.get_url_from_post(post)

        if pasture.should_scrape_url(external_url, processed_urls):
            print(f"Scraping {external_url}")
            if scrape_url(external_url, output_dir, tags_to_remove):
                pasture.mark_url_processed(external_url, processed_urls)
                new_urls_scraped += 1
                print(f"Successfully scraped {external_url}")
            else:
                print(f"Failed to scrape {external_url}")
        else:
            print(f"Skipping duplicate URL: {external_url}")

    print(f"Scraped {new_urls_scraped} new URLs from {pasture.name}")
    return processed_urls
