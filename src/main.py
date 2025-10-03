import configparser
import json
import os
import time
import schedule
import logging
from datetime import datetime
from typing import Dict, Any, Set

from pastures import PastureFactory
from core.scraper import (
    scrape_pasture,
    load_processed_urls,
    save_processed_urls,
)


# Set up logging - centralized configuration to avoid duplicates
def setup_logging():
    """Configure logging for the entire application."""

    # Custom formatter for cleaner, more readable logging
    class PastureFormatter(logging.Formatter):
        def format(self, record):
            # Color codes for different log levels
            colors = {
                "INFO": "\033[94m",  # Blue
                "WARNING": "\033[93m",  # Yellow
                "ERROR": "\033[91m",  # Red
                "DEBUG": "\033[90m",  # Gray
            }
            reset = "\033[0m"

            # Get the color for this log level
            color = colors.get(record.levelname, "")

            # Format the message
            timestamp = self.formatTime(record, "%H:%M:%S")
            level = f"{color}{record.levelname:8}{reset}"
            message = record.getMessage()

            # Clean up module names for better readability
            if record.name == "core.scraper":
                module = "SCRAPER"
            elif record.name == "__main__":
                module = "MAIN"
            elif "pastures" in record.name:
                module = record.name.split(".")[-1].upper()
            else:
                module = record.name

            return f"{timestamp} | {level} | {module:12} | {message}"

    # Clear all existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure root logger with our custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(PastureFormatter())
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.INFO)

    # Disable propagation to prevent duplicate messages
    root_logger.propagate = False

    # Return the main logger for this module
    return logging.getLogger(__name__)


# Initialize logging
logger = setup_logging()


def run_single_scrape(config: configparser.ConfigParser) -> None:
    """Run a single scrape of all configured pastures.

    Args:
        config: Configuration parser with pasture sections
    """
    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    processed_urls_file = os.path.join(output_base_dir, "processed_urls.json")
    processed_urls = load_processed_urls(processed_urls_file)

    logger.info(f"🚀 Starting scrape session")

    for section in config.sections():
        if section == "global":
            continue

        try:
            pasture_config = dict(config[section])
            pasture = PastureFactory.create_pasture(section, pasture_config)
            processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls)
        except Exception as e:
            logger.error(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)
    logger.info(f"✅ Scrape session completed")


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

    logger.info(f"⏰ Scheduled scrape: {section}")

    try:
        pasture_config = dict(config[section])
        pasture = PastureFactory.create_pasture(section, pasture_config)
        processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls)
    except Exception as e:
        logger.error(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)
    logger.info(f"✅ Scheduled scrape completed: {section}")


def setup_scheduler(config: configparser.ConfigParser) -> None:
    """Set up scheduled scraping based on config intervals.

    Args:
        config: Configuration parser with pasture sections
    """
    logger.info("🔄 Setting up scheduled scraping")

    for section in config.sections():
        if section == "global":
            continue

        interval = config[section].get("interval", "60").strip()
        try:
            interval_minutes = int(interval)
            schedule.every(interval_minutes).minutes.do(
                lambda section=section: scrape_scheduled_pasture(section, config)
            )
            logger.info(f"⏰ Scheduled {section} every {interval_minutes} minutes")
        except ValueError:
            logger.warning(
                f"⚠️  Invalid interval for {section}: {interval}, using 60 minutes"
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

        logger.info("🔄 Scheduler started - Press Ctrl+C to exit")
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped")
    else:
        # Run single scrape
        run_single_scrape(config)


if __name__ == "__main__":
    main()
