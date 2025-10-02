import configparser
import hashlib
import json
import os
import time
import schedule
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options


def get_subreddit_posts(url):
    """Fetches posts from a subreddit's JSON feed."""
    try:
        response = requests.get(url, headers={"User-agent": "your bot 0.1"})
        response.raise_for_status()
        return response.json()["data"]["children"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []


def filter_posts(posts, blacklist):
    """Filters posts based on specified criteria."""
    filtered_posts = []
    for post in posts:
        if (
            not post["data"]["stickied"]
            and not post["data"]["is_self"]
            and not any(
                term.lower() in post["data"]["title"].lower() for term in blacklist
            )
        ):
            filtered_posts.append(post)
    return filtered_posts


def hash_url(url):
    """Hashes a URL using SHA256."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def post_process_html(file_path, tags_to_remove):
    """Cleans up an HTML file using BeautifulSoup and converts it to Markdown."""
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


def scrape_url(url, output_dir, tags_to_remove):
    """Scrapes the content of a URL using Selenium."""
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


def scrape_subreddit(config, section, output_base_dir, processed_urls):
    """Scrape a single subreddit section."""
    if section == "global":
        return processed_urls

    subreddit_url = config[section]["url"]
    blacklist = [
        term.strip() for term in config[section]["blacklist"].split(",") if term.strip()
    ]

    # Get section-specific tags to remove and handle overrides
    section_tags_to_remove = []
    tags_to_keep = []
    if "remove_tags" in config[section]:
        for tag in config[section]["remove_tags"].split(","):
            tag = tag.strip()
            if tag:
                if tag.startswith("-"):
                    # Tag to keep (remove from global list)
                    tags_to_keep.append(tag[1:])
                else:
                    # Tag to remove (add to section list)
                    section_tags_to_remove.append(tag)

    # Get global tags to remove
    global_tags_to_remove = []
    if "global" in config and "remove_tags" in config["global"]:
        global_tags_to_remove = [
            tag.strip()
            for tag in config["global"]["remove_tags"].split(",")
            if tag.strip()
        ]

    # Start with global tags, remove any that are marked to keep
    effective_global_tags = [
        tag for tag in global_tags_to_remove if tag not in tags_to_keep
    ]

    # Combine effective global tags and section tags, removing duplicates
    all_tags_to_remove = list(set(effective_global_tags + section_tags_to_remove))

    posts = get_subreddit_posts(subreddit_url)
    filtered_posts = filter_posts(posts, blacklist)

    run_dir = os.path.join(output_base_dir, datetime.now().strftime("%Y-%m-%d"))
    subreddit_output_dir = os.path.join(run_dir, section)
    os.makedirs(subreddit_output_dir, exist_ok=True)

    new_urls_scraped = 0
    for post in filtered_posts:
        external_url = post["data"]["url"]
        url_hash = hash_url(external_url)

        if url_hash not in processed_urls:
            print(f"Scraping {external_url}")
            if scrape_url(external_url, subreddit_output_dir, all_tags_to_remove):
                processed_urls.add(url_hash)
                new_urls_scraped += 1
                print(f"Successfully scraped {external_url}")
            else:
                print(f"Failed to scrape {external_url}")
        else:
            print(f"Skipping duplicate URL: {external_url}")

    print(f"Scraped {new_urls_scraped} new URLs from {section}")
    return processed_urls


def run_single_scrape():
    """Run a single scrape of all configured subreddits."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    processed_urls_file = os.path.join(output_base_dir, "processed_urls.json")
    if os.path.exists(processed_urls_file):
        with open(processed_urls_file, "r") as f:
            processed_urls = set(json.load(f))
    else:
        processed_urls = set()

    print(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for section in config.sections():
        processed_urls = scrape_subreddit(
            config, section, output_base_dir, processed_urls
        )

    with open(processed_urls_file, "w") as f:
        json.dump(list(processed_urls), f)

    print(f"Completed scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def setup_scheduler():
    """Set up scheduled scraping based on config intervals."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    print("Setting up scheduled scraping...")

    for section in config.sections():
        if section == "global":
            continue

        interval = (
            config[section].get("interval", "60").strip()
        )  # Default to 60 minutes
        try:
            interval_minutes = int(interval)
            schedule.every(interval_minutes).minutes.do(
                lambda section=section: scrape_scheduled_section(section)
            )
            print(f"Scheduled {section} to run every {interval_minutes} minutes")
        except ValueError:
            print(
                f"Invalid interval for {section}: {interval}. Using default 60 minutes."
            )
            schedule.every(60).minutes.do(
                lambda section=section: scrape_scheduled_section(section)
            )


def scrape_scheduled_section(section):
    """Scrape a single section when scheduled."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    processed_urls_file = os.path.join(output_base_dir, "processed_urls.json")
    if os.path.exists(processed_urls_file):
        with open(processed_urls_file, "r") as f:
            processed_urls = set(json.load(f))
    else:
        processed_urls = set()

    print(
        f"Starting scheduled scrape of {section} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    processed_urls = scrape_subreddit(config, section, output_base_dir, processed_urls)

    with open(processed_urls_file, "w") as f:
        json.dump(list(processed_urls), f)

    print(
        f"Completed scheduled scrape of {section} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def main():
    """Main function to run the subreddit scraper."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    # Check if we should run in scheduled mode
    scheduled_mode = any(
        config[section].get("interval")
        for section in config.sections()
        if section != "global" and config[section].get("interval")
    )

    if scheduled_mode:
        # Run initial scrape
        run_single_scrape()

        # Set up scheduler
        setup_scheduler()

        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
    else:
        # Run single scrape (original behavior)
        run_single_scrape()


if __name__ == "__main__":
    main()
