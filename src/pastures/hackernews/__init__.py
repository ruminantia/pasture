import requests
from typing import List, Dict, Any
from ..base import Pasture


class HackerNewsPasture(Pasture):
    """Pasture implementation for scraping Hacker News."""

    def fetch_posts(self) -> List[Dict[str, Any]]:
        """Fetch top stories from Hacker News API."""
        try:
            # Get top story IDs from the correct API endpoint
            # Use configured URL if provided, otherwise use default HackerNews API
            top_stories_url = self.config.get(
                "url", "https://hacker-news.firebaseio.com/v0/topstories.json"
            )
            response = requests.get(top_stories_url)
            response.raise_for_status()
            story_ids = response.json()[:50]  # Get top 50 stories

            # Fetch story details for each ID
            posts = []
            for story_id in story_ids:
                story_url = (
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                )
                story_response = requests.get(story_url)
                if story_response.status_code == 200:
                    story_data = story_response.json()
                    # Only include stories with URLs (not Ask HN posts or job posts)
                    if story_data.get("type") == "story" and story_data.get("url"):
                        posts.append(story_data)

            print(f"📄 Got {len(posts)} stories with URLs")
            return posts
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching Hacker News: {e}")
            return []

    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter Hacker News stories based on criteria."""
        blacklist = self.get_blacklist()

        filtered_posts = []
        for post in posts:
            title = post.get("title", "").lower()
            url = post.get("url", "").lower()

            # Check for blacklist matches in both title and URL
            blacklist_matches = [
                term for term in blacklist
                if term.lower() in title or term.lower() in url
            ]

            # Track blacklist rejection
            if blacklist_matches and self.stats_tracker:
                for term in blacklist_matches:
                    self.stats_tracker.increment_blacklisted(term)

            # Skip posts that contain blacklisted terms in title or URL
            if not any(term.lower() in title or term.lower() in url for term in blacklist):
                filtered_posts.append(post)

        if blacklist and len(posts) > len(filtered_posts):
            print(f"🎯 Filtered {len(posts) - len(filtered_posts)} posts")
        return filtered_posts

    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from a Hacker News story."""
        return post["url"]
