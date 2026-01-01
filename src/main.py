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
from core.stats import StatsTracker
from core.config_reload import trigger_config_reload, wait_for_reload, clear_reload


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

    # Also log to file for web viewer - use daily rotating logs
    try:
        from logging.handlers import TimedRotatingFileHandler
        os.makedirs('output/logs', exist_ok=True)

        # Daily rotating log files in logs/ directory
        # Current log: output/logs/scraper.log
        # Rotated logs: output/logs/scraper.log.YYYY-MM-DD
        file_handler = TimedRotatingFileHandler(
            'output/logs/scraper.log',
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        file_handler.suffix = '%Y-%m-%d'
        file_handler.setFormatter(PastureFormatter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")

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

    # Create stats tracker for this session
    stats_tracker = StatsTracker(output_base_dir)

    logger.info(f"🚀 Starting scrape session")

    for section in config.sections():
        if section == "global":
            continue

        try:
            # Merge global configuration with pasture-specific configuration
            pasture_config = dict(config[section])
            if "global" in config:
                global_config = dict(config["global"])
                # Merge global config into pasture config (pasture-specific takes precedence)
                for key, value in global_config.items():
                    if key not in pasture_config:
                        pasture_config[key] = value
                    elif key == "blacklist":
                        # For blacklist, combine global and pasture-specific lists
                        global_blacklist = value.strip()
                        pasture_blacklist = pasture_config[key].strip()
                        if global_blacklist and pasture_blacklist:
                            pasture_config[key] = (
                                f"{global_blacklist},{pasture_blacklist}"
                            )
                        elif global_blacklist:
                            pasture_config[key] = global_blacklist
                        # If only pasture_blacklist exists, it's already set

            pasture = PastureFactory.create_pasture(section, pasture_config)
            processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls, stats_tracker)
        except Exception as e:
            logger.error(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)

    # Save session statistics
    stats_tracker.save_session_stats()

    logger.info(f"✅ Scrape session completed")

    # Generate web viewer
    try:
        from core.web_viewer import generate_static_site
        generate_static_site(output_base_dir)
    except Exception as e:
        logger.error(f"❌ Failed to generate web viewer: {e}")


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

    # Create stats tracker for this session
    stats_tracker = StatsTracker(output_base_dir)

    logger.info(f"⏰ Scheduled scrape: {section}")

    try:
        # Merge global configuration with pasture-specific configuration
        pasture_config = dict(config[section])
        if "global" in config:
            global_config = dict(config["global"])
            # Merge global config into pasture config (pasture-specific takes precedence)
            for key, value in global_config.items():
                if key not in pasture_config:
                    pasture_config[key] = value
                elif key == "blacklist":
                    # For blacklist, combine global and pasture-specific lists
                    global_blacklist = value.strip()
                    pasture_blacklist = pasture_config[key].strip()
                    if global_blacklist and pasture_blacklist:
                        pasture_config[key] = f"{global_blacklist},{pasture_blacklist}"
                    elif global_blacklist:
                        pasture_config[key] = global_blacklist
                    # If only pasture_blacklist exists, it's already set

        pasture = PastureFactory.create_pasture(section, pasture_config)
        processed_urls = scrape_pasture(pasture, output_base_dir, processed_urls, stats_tracker)
    except Exception as e:
        logger.error(f"Error processing pasture '{section}': {e}")

    save_processed_urls(processed_urls_file, processed_urls)

    # Save session statistics
    stats_tracker.save_session_stats()

    logger.info(f"✅ Scheduled scrape completed: {section}")

    # Generate web viewer
    try:
        from core.web_viewer import generate_static_site
        generate_static_site(output_base_dir)
    except Exception as e:
        logger.error(f"❌ Failed to generate web viewer: {e}")


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


def clear_scheduler() -> None:
    """Clear all scheduled jobs."""
    schedule.clear()
    logger.info("🧹 Cleared all scheduled jobs")


def reload_config_and_reschedule(old_config: configparser.ConfigParser = None) -> configparser.ConfigParser:
    """Reload configuration and reschedule all pastures.

    Args:
        old_config: Previous configuration (optional, for detecting new/modified pastures)

    Returns:
        Updated configuration parser
    """
    logger.info("🔄 Reloading configuration...")

    # Store old pasture configs for comparison
    old_pastures = {}
    if old_config:
        for section in old_config.sections():
            if section != "global":
                old_pastures[section] = dict(old_config[section])

    # Reload config file
    config = configparser.ConfigParser()
    config.read("config.ini")

    # Clear existing schedule
    clear_scheduler()

    # Setup new schedule
    setup_scheduler(config)

    # List all active scheduled jobs
    jobs = schedule.get_jobs()
    logger.info(f"📅 Active scheduled jobs: {len(jobs)}")
    for job in jobs:
        if hasattr(job, 'tags') and job.tags:
            logger.info(f"   - {job.tags}")

    # Determine which pastures are new or modified
    new_or_modified = []
    for section in config.sections():
        if section == "global":
            continue

        if section not in old_pastures:
            # New pasture
            new_or_modified.append((section, "new"))
            logger.info(f"➕ New pasture detected: {section}")
        else:
            # Check if modified
            old_cfg = old_pastures[section]
            new_cfg = dict(config[section])

            # Compare configs (ignore interval for modification detection since
            # interval changes don't require immediate scrape)
            is_modified = False
            for key, new_value in new_cfg.items():
                if key == "interval":
                    continue
                old_value = old_cfg.get(key)
                if old_value != new_value:
                    is_modified = True
                    break

            if is_modified:
                new_or_modified.append((section, "modified"))
                logger.info(f"✏️  Modified pasture detected: {section}")

    # Trigger immediate scrape for new or modified pastures
    if new_or_modified:
        logger.info(f"🚀 Immediately scraping {len(new_or_modified)} new/modified pasture(s)...")
        for section, reason in new_or_modified:
            logger.info(f"   - Scraping {section} ({reason})")
            try:
                scrape_scheduled_pasture(section, config)
            except Exception as e:
                logger.error(f"❌ Failed to scrape {section}: {e}")
    else:
        logger.info("ℹ️  No new or modified pastures - skipping immediate scrape")

    return config


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

    # Start HTTP server for web viewer
    try:
        from core.web_viewer import start_http_server
        output_base_dir = "output"
        start_http_server(output_base_dir, port=8000)
    except Exception as e:
        logger.error(f"❌ Failed to start web viewer HTTP server: {e}")

    if should_run_scheduled_mode(config):
        # Run initial scrape
        run_single_scrape(config)

        # Set up scheduler
        setup_scheduler(config)

        logger.info("🔄 Scheduler started - Press Ctrl+C to exit")
        try:
            while True:
                # Check for config reload event
                if wait_for_reload(timeout=0.1):  # Non-blocking check
                    logger.info("🔄 Config reload requested, rescheduling...")
                    clear_reload()
                    # Pass old config for comparison
                    config = reload_config_and_reschedule(old_config=config)

                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped")
    else:
        # Run single scrape
        run_single_scrape(config)


if __name__ == "__main__":
    main()
