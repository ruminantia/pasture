from typing import Dict, Any, Type
from .base import Pasture
from .reddit import RedditPasture
from .hackernews import HackerNewsPasture


class PastureFactory:
    """Factory class for creating pasture instances based on configuration."""

    _pasture_types = {
        "reddit": RedditPasture,
        "hackernews": HackerNewsPasture,
    }

    @classmethod
    def create_pasture(cls, name: str, config: Dict[str, Any]) -> Pasture:
        """Create a pasture instance based on configuration.

        Args:
            name: Name of the pasture section
            config: Configuration dictionary for the pasture

        Returns:
            Pasture instance

        Raises:
            ValueError: If pasture type cannot be determined from configuration
        """
        # Determine pasture type from configuration
        pasture_type = cls._determine_pasture_type(config)

        if pasture_type not in cls._pasture_types:
            raise ValueError(f"Unknown pasture type: {pasture_type}")

        pasture_class = cls._pasture_types[pasture_type]
        return pasture_class(name, config)

    @classmethod
    def _determine_pasture_type(cls, config: Dict[str, Any]) -> str:
        """Determine the pasture type from configuration.

        Args:
            config: Configuration dictionary

        Returns:
            String representing the pasture type
        """
        # Check for explicit type configuration
        if "type" in config:
            return config["type"]

        # Auto-detect based on URL patterns
        url = config.get("url", "")

        if "reddit.com" in url:
            return "reddit"
        elif (
            "hackernews" in url
            or "news.ycombinator.com" in url
            or "hacker-news.firebaseio.com" in url
        ):
            return "hackernews"
        # Add more auto-detection patterns as needed

        # Default to reddit for backward compatibility
        return "reddit"

    @classmethod
    def register_pasture_type(
        cls, pasture_type: str, pasture_class: Type[Pasture]
    ) -> None:
        """Register a new pasture type.

        Args:
            pasture_type: String identifier for the pasture type
            pasture_class: Class implementing the Pasture interface
        """
        cls._pasture_types[pasture_type] = pasture_class
