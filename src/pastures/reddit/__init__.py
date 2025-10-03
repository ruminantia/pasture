import requests
from typing import List, Dict, Any
from ..base import Pasture


class RedditPasture(Pasture):
    """Pasture implementation for scraping Reddit subreddits."""

    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch posts from a subreddit's JSON feed."""
        url = self.config["url"]
        try:
            response = requests.get(url, headers={"User-agent": "your bot 0.1"})
            response.raise_for_status()
            posts = response.json()["data"]["children"]
            print(f"📥 Fetched {len(posts)} posts")
            return posts
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching: {e}")
            return []

    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter posts based on Reddit-specific criteria."""
        blacklist = [
            term.strip()
            for term in self.config.get("blacklist", "").split(",")
            if term.strip()
        ]

        filtered_posts = []
        for post in posts:
            post_data = post["data"]
            if (
                not post_data["stickied"]
                and not post_data["is_self"]
                and not any(
                    term.lower() in post_data["title"].lower() for term in blacklist
                )
            ):
                filtered_posts.append(post)

        if blacklist and len(posts) > len(filtered_posts):
            print(f"🎯 Filtered {len(posts) - len(filtered_posts)} posts")
        return filtered_posts

    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from a Reddit post."""
        return post["data"]["url"]
