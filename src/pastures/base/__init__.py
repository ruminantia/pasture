from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Optional
import os
from datetime import datetime
from core.datetime_utils import now


class Pasture(ABC):
    """Abstract base class for all pasture implementations."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.processed_urls: Set[str] = set()
        self.stats_tracker: Optional[Any] = None  # Optional StatsTracker instance

    def set_stats_tracker(self, stats_tracker: Optional[Any]) -> None:
        """Set the stats tracker for this pasture.

        Args:
            stats_tracker: StatsTracker instance to use for tracking statistics
        """
        self.stats_tracker = stats_tracker

    @abstractmethod
    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch posts/items from the pasture source.

        Returns:
            List of dictionaries containing post/item data
        """
        pass

    @abstractmethod
    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter posts based on pasture-specific criteria.

        Args:
            posts: List of posts to filter

        Returns:
            Filtered list of posts
        """
        pass

    def get_output_directory(self, base_output_dir: str) -> str:
        """Get the output directory for this pasture.

        Args:
            base_output_dir: Base output directory

        Returns:
            Full path to pasture-specific output directory
        """
        pasture_dir = os.path.join(base_output_dir, self.name)
        dt = now()
        run_dir = os.path.join(
            pasture_dir,
            dt.strftime("%Y"),
            dt.strftime("%m"),
            dt.strftime("%d"),
        )
        os.makedirs(run_dir, exist_ok=True)
        return run_dir

    def should_scrape_url(self, url: str, processed_urls: Set[str]) -> bool:
        """Check if a URL should be scraped.

        Args:
            url: URL to check
            processed_urls: Set of already processed URLs

        Returns:
            True if URL should be scraped, False otherwise
        """
        url_hash = self.hash_url(url)
        return url_hash not in processed_urls

    def mark_url_processed(self, url: str, processed_urls: Set[str]) -> None:
        """Mark a URL as processed.

        Args:
            url: URL to mark as processed
            processed_urls: Set to add the URL hash to
        """
        url_hash = self.hash_url(url)
        processed_urls.add(url_hash)

    @staticmethod
    def hash_url(url: str) -> str:
        """Hash a URL using SHA256.

        Args:
            url: URL to hash

        Returns:
            SHA256 hash of the URL
        """
        import hashlib

        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def get_tags_to_remove(self) -> List[str]:
        """Get the list of HTML tags to remove during processing.

        Returns:
            List of tag names to remove
        """
        tags_to_remove = []
        tags_to_keep = []

        # Get pasture-specific tags to remove and handle overrides
        if "remove_tags" in self.config:
            for tag in self.config["remove_tags"].split(","):
                tag = tag.strip()
                if tag:
                    if tag.startswith("-"):
                        # Tag to keep (remove from global list)
                        tags_to_keep.append(tag[1:])
                    else:
                        # Tag to remove (add to pasture list)
                        tags_to_remove.append(tag)

        # Get global tags to remove if available
        global_tags_to_remove = []
        if "global" in self.config and "remove_tags" in self.config["global"]:
            global_tags_to_remove = [
                tag.strip()
                for tag in self.config["global"]["remove_tags"].split(",")
                if tag.strip()
            ]

        # Start with global tags, remove any that are marked to keep
        effective_global_tags = [
            tag for tag in global_tags_to_remove if tag not in tags_to_keep
        ]

        # Combine effective global tags and pasture tags, removing duplicates
        all_tags_to_remove = list(set(effective_global_tags + tags_to_remove))

        return all_tags_to_remove

    @abstractmethod
    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from a post/item.

        Args:
            post: Post/item dictionary

        Returns:
            External URL to scrape
        """
        pass
