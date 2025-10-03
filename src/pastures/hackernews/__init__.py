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

            return posts
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Hacker News stories: {e}")
            return []

    def filter_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter Hacker News stories based on criteria."""
        blacklist = [
            term.strip()
            for term in self.config.get("blacklist", "").split(",")
            if term.strip()
        ]

        filtered_posts = []
        for post in posts:
            title = post.get("title", "").lower()
            # Skip posts that contain blacklisted terms in title
            if not any(term.lower() in title for term in blacklist):
                filtered_posts.append(post)

        return filtered_posts

    def get_url_from_post(self, post: Dict[str, Any]) -> str:
        """Extract the external URL from a Hacker News story."""
        return post["url"]
