import configparser
import json
import os
import time
import schedule
from datetime import datetime
from typing import Dict, Any, Set

from pastures import PastureFactory
from core.scraper import (
    scrape_pasture,
    load_processed_urls,
    save_processed_urls,
)


def run_single_scrape(config: configparser.ConfigParser) -> None:
    """Run a single scrape of all configured pastures.

    Args:
        config: Configuration parser with pasture sections
    """
    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    processed_urls_file = os.path.join(output_base_dir, "processed_urls.json")
    processed_urls = load_processed_urls(processed_urls_file)

    print(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for section in config.sections():
        if section == "global":
            continue

        try:
            pasture_config = dict(config[section])
            pasture = PastureFactory.create_pasture(section, pasture_config)
            processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls)
        except Exception as e:
            print(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)
    print(f"Completed scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def scrape_scheduled_pasture(section: str, config: configparser.ConfigParser) -> None:
    """Scrape a single pasture when scheduled.

    Args:
        section: Name of the pasture section to scrape
        config: Configuration parser with pasture sections
    """
    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    processed_urls_file = os.path.join(output_base_dir, "processed_urls.json")
    processed_urls = load_processed_urls(processed_urls_file)

    print(
        f"Starting scheduled scrape of {section} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        pasture_config = dict(config[section])
        pasture = PastureFactory.create_pasture(section, pasture_config)
        processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls)
    except Exception as e:
        print(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)
    print(
        f"Completed scheduled scrape of {section} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


def setup_scheduler(config: configparser.ConfigParser) -> None:
    """Set up scheduled scraping based on config intervals.

    Args:
        config: Configuration parser with pasture sections
    """
    print("Setting up scheduled scraping...")

    for section in config.sections():
        if section == "global":
            continue

        interval = config[section].get("interval", "60").strip()
        try:
            interval_minutes = int(interval)
            schedule.every(interval_minutes).minutes.do(
                lambda section=section: scrape_scheduled_pasture(section, config)
            )
            print(f"Scheduled {section} to run every {interval_minutes} minutes")
        except ValueError:
            print(
                f"Invalid interval for {section}: {interval}. Using default 60 minutes."
            )
            schedule.every(60).minutes.do(
                lambda section=section: scrape_scheduled_pasture(section, config)
            )


def should_run_scheduled_mode(config: configparser.ConfigParser) -> bool:
    """Check if we should run in scheduled mode.

    Args:
        config: Configuration parser with pasture sections

    Returns:
        True if any pasture has an interval configured, False otherwise
    """
    return any(
        config[section].get("interval")
        for section in config.sections()
        if section != "global" and config[section].get("interval")
    )


def main() -> None:
    """Main function to run the pasture scraper."""
    config = configparser.ConfigParser()
    config.read("config.ini")

    if should_run_scheduled_mode(config):
        # Run initial scrape
        run_single_scrape(config)

        # Set up scheduler
        setup_scheduler(config)

        print("Scheduler started. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Scheduler stopped.")
    else:
        # Run single scrape
        run_single_scrape(config)


if __name__ == "__main__":
    main()
