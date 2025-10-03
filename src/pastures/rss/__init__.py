from typing import List, Dict, Any
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import urlparse

from ..base import Pasture


class RSSPasture(Pasture):
    """Pasture implementation for scraping RSS feeds."""

    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch items from an RSS feed."""
        url = self.config.get("url", "")
        if not url:
            raise ValueError("RSS pasture requires a 'url' configuration")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            }

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse the RSS feed
            root = ET.fromstring(response.content)

            # Handle different RSS versions and formats
            items = []

            # RSS 2.0 format
            if root.tag == "rss":
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")

            # Atom format (common alternative)
            elif root.tag.endswith("feed"):  # Atom feed
                items = root.findall(".//entry")

            # RDF format (RSS 1.0)
            elif root.tag.endswith("RDF"):
                items = root.findall("item")

            posts = []
            for item in items:
                post_data = self._parse_rss_item(item)
                if post_data:
                    posts.append(post_data)

            return posts

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching RSS feed: {e}")
            return []
        except ET.ParseError as e:
            print(f"❌ Error parsing RSS feed: {e}")
            return []

    def _parse_rss_item(self, item) -> Dict[str, Any]:
        """Parse an RSS item into a standardized format."""
        post_data = {}

        # RSS 2.0 fields
        title = item.find("title")
        if title is not None and title.text:
            post_data["title"] = title.text

        link = item.find("link")
        if link is not None:
            # Handle both text content and href attributes
            if link.text:
                post_data["url"] = link.text
            elif "href" in link.attrib:
                post_data["url"] = link.attrib["href"]

        # Atom format fields
        if not post_data.get("url"):
            link_elem = item.find(".//link[@rel='alternate']")
            if link_elem is not None and "href" in link_elem.attrib:
                post_data["url"] = link_elem.attrib["href"]

        # Description/summary
        description = item.find("description")
        if description is not None and description.text:
            post_data["description"] = description.text
        else:
            summary = item.find("summary")
            if summary is not None and summary.text:
                post_data["description"] = summary.text

        # Publication date
        pub_date = item.find("pubDate")
        if pub_date is not None and pub_date.text:
            post_data["pub_date"] = pub_date.text
        else:
            published = item.find("published")
            if published is not None and published.text:
                post_data["pub_date"] = published.text

        # GUID/ID
        guid = item.find("guid")
        if guid is not None and guid.text:
            post_data["id"] = guid.text
        else:
            item_id = item.find("id")
            if item_id is not None and item_id.text:
                post_data["id"] = item_id.text

        # Author
        author = item.find("author")
        if author is not None and author.text:
            post_data["author"] = author.text

        # Categories/tags
        categories = item.findall("category")
        if categories:
            post_data["categories"] = [cat.text for cat in categories if cat.text]

        # Only include items that have at least a title and URL
        if post_data.get("title") and post_data.get("url"):
            return post_data

        return None

    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter RSS items based on criteria."""
        blacklist = [
            term.strip()
            for term in self.config.get("blacklist", "").split(",")
            if term.strip()
        ]

        max_age_days = self.config.get("max_age_days")
        if max_age_days:
            try:
                max_age_days = int(max_age_days)
            except (ValueError, TypeError):
                max_age_days = None

        filtered_posts = []
        for post in posts:
            title = post.get("title", "").lower()
            description = post.get("description", "").lower()

            # Skip posts that contain blacklisted terms in title or description
            if any(
                term.lower() in title or term.lower() in description
                for term in blacklist
            ):
                continue

            # Filter by age if configured
            if max_age_days and not self._is_within_age_limit(post, max_age_days):
                continue

            filtered_posts.append(post)

        print(f"📄 Got {len(posts)} RSS items")
        if blacklist and len(posts) > len(filtered_posts):
            print(f"🎯 Filtered {len(posts) - len(filtered_posts)} items")
        if max_age_days and len(posts) > len(filtered_posts):
            print(f"📅 Age filtered {len(posts) - len(filtered_posts)} items")
        return filtered_posts

    def _is_within_age_limit(self, post: Dict[str, Any], max_age_days: int) -> bool:
        """Check if a post is within the age limit."""
        pub_date_str = post.get("pub_date")
        if not pub_date_str:
            return True  # If no date, assume it's recent

        try:
            # Try common RSS date formats
            date_formats = [
                "%a, %d %b %Y %H:%M:%S %Z",
                "%a, %d %b %Y %H:%M:%S %z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d %H:%M:%S",
            ]

            pub_date = None
            for fmt in date_formats:
                try:
                    pub_date = datetime.strptime(pub_date_str, fmt)
                    break
                except ValueError:
                    continue

            if pub_date:
                age = datetime.now() - pub_date
                return age.days <= max_age_days

        except Exception:
            pass

        return True  # If we can't parse the date, assume it's recent

    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from an RSS item."""
        return post["url"]
