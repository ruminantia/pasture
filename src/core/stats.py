"""Statistics tracking for Pasture scraper."""

import os
import json
import logging
from typing import Dict, Any, List, Set
from collections import defaultdict
from core.datetime_utils import now, format_datetime, get_date_string

logger = logging.getLogger(__name__)


class StatsTracker:
    """Track scraping statistics."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.stats_file = os.path.join(output_dir, 'stats.json')
        self.rejections_file = os.path.join(output_dir, 'rejections.json')
        self.session_stats = {
            'start_time': format_datetime(now()),
            'articles_scraped': 0,
            'articles_skipped_duplicate': 0,
            'articles_rejected_blacklist': 0,
            'blacklist_hits_by_term': defaultdict(int),
            'blacklist_hits_by_source': defaultdict(int),  # Track rejections per source
            'blacklist_hits_by_source_and_term': defaultdict(lambda: defaultdict(int)),  # Track term hits per source
            'articles_by_source': defaultdict(int),
            'errors': 0,
            'sources_processed': []
        }
        # Track detailed rejections for this session
        self.session_rejections: List[Dict[str, Any]] = []
        # Track URLs we've already recorded as rejected to avoid duplicates
        self._recorded_rejections: Set[str] = set()

    def increment_scraped(self, source: str):
        """Increment articles scraped counter."""
        self.session_stats['articles_scraped'] += 1
        self.session_stats['articles_by_source'][source] += 1

    def increment_duplicate(self):
        """Increment duplicate articles counter."""
        self.session_stats['articles_skipped_duplicate'] += 1

    def increment_blacklisted(self, term: str, source: str = None):
        """Increment blacklisted articles counter."""
        self.session_stats['articles_rejected_blacklist'] += 1
        self.session_stats['blacklist_hits_by_term'][term] += 1
        if source:
            self.session_stats['blacklist_hits_by_source'][source] += 1
            self.session_stats['blacklist_hits_by_source_and_term'][source][term] += 1

    def record_rejection(self, url: str, title: str, matching_terms: List[str], source: str):
        """Record a detailed rejection entry.

        Args:
            url: The URL that was rejected
            title: The title of the post/article
            matching_terms: List of blacklist terms that matched
            source: The pasture/source name
        """
        # Create a unique key for this URL to avoid duplicate records
        url_key = f"{source}:{url}"

        # Skip if we've already recorded this URL
        if url_key in self._recorded_rejections:
            return

        self._recorded_rejections.add(url_key)

        rejection_entry = {
            'url': url,
            'title': title,
            'matching_terms': matching_terms,
            'source': source,
            'rejected_at': format_datetime(now())
        }

        self.session_rejections.append(rejection_entry)

    def increment_error(self):
        """Increment error counter."""
        self.session_stats['errors'] += 1

    def add_source(self, source: str):
        """Add a processed source."""
        if source not in self.session_stats['sources_processed']:
            self.session_stats['sources_processed'].append(source)

    def save_session_stats(self):
        """Save session statistics to file."""
        try:
            # Load existing stats
            all_stats = self._load_stats()

            # Add current session
            dt_now = now()
            session_date = get_date_string()
            session_time = dt_now.strftime('%H:%M:%S')

            if 'sessions' not in all_stats:
                all_stats['sessions'] = []

            if 'daily' not in all_stats:
                all_stats['daily'] = {}

            # Convert defaultdicts to regular dicts for JSON serialization
            # Convert nested defaultdict for blacklist_hits_by_source_and_term
            blacklist_by_source_term = {}
            for source, terms in self.session_stats['blacklist_hits_by_source_and_term'].items():
                blacklist_by_source_term[source] = dict(terms)

            session_data = {
                'date': session_date,
                'time': session_time,
                'start_time': self.session_stats['start_time'],
                'end_time': format_datetime(dt_now),
                'articles_scraped': self.session_stats['articles_scraped'],
                'articles_skipped_duplicate': self.session_stats['articles_skipped_duplicate'],
                'articles_rejected_blacklist': self.session_stats['articles_rejected_blacklist'],
                'blacklist_hits_by_term': dict(self.session_stats['blacklist_hits_by_term']),
                'blacklist_hits_by_source': dict(self.session_stats['blacklist_hits_by_source']),
                'blacklist_hits_by_source_and_term': blacklist_by_source_term,
                'articles_by_source': dict(self.session_stats['articles_by_source']),
                'errors': self.session_stats['errors'],
                'sources_processed': self.session_stats['sources_processed']
            }

            # Add to sessions list
            all_stats['sessions'].append(session_data)

            # Keep only last 100 sessions
            if len(all_stats['sessions']) > 100:
                all_stats['sessions'] = all_stats['sessions'][-100:]

            # Aggregate daily stats
            if session_date not in all_stats['daily']:
                all_stats['daily'][session_date] = {
                    'articles_scraped': 0,
                    'articles_rejected_blacklist': 0,
                    'articles_skipped_duplicate': 0,
                    'blacklist_hits_by_term': {},
                    'blacklist_hits_by_source': {},
                    'blacklist_hits_by_source_and_term': {},
                    'articles_by_source': {},
                    'sessions_count': 0
                }

            daily = all_stats['daily'][session_date]
            daily['articles_scraped'] += session_data['articles_scraped']
            daily['articles_rejected_blacklist'] += session_data['articles_rejected_blacklist']
            daily['articles_skipped_duplicate'] += session_data['articles_skipped_duplicate']
            daily['sessions_count'] += 1

            # Merge blacklist hits by term
            for term, count in session_data['blacklist_hits_by_term'].items():
                daily['blacklist_hits_by_term'][term] = daily['blacklist_hits_by_term'].get(term, 0) + count

            # Merge blacklist hits by source
            for source, count in session_data['blacklist_hits_by_source'].items():
                daily['blacklist_hits_by_source'][source] = daily['blacklist_hits_by_source'].get(source, 0) + count

            # Merge blacklist hits by source and term
            for source, terms in session_data['blacklist_hits_by_source_and_term'].items():
                if source not in daily['blacklist_hits_by_source_and_term']:
                    daily['blacklist_hits_by_source_and_term'][source] = {}
                for term, count in terms.items():
                    daily['blacklist_hits_by_source_and_term'][source][term] = \
                        daily['blacklist_hits_by_source_and_term'][source].get(term, 0) + count

            # Merge source counts
            for source, count in session_data['articles_by_source'].items():
                daily['articles_by_source'][source] = daily['articles_by_source'].get(source, 0) + count

            # Keep only last 90 days
            dates_to_keep = sorted(all_stats['daily'].keys(), reverse=True)[:90]
            all_stats['daily'] = {k: v for k, v in all_stats['daily'].items() if k in dates_to_keep}

            # Save to file
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, indent=2)

            # Save rejections
            self._save_rejections()

            logger.info(f"📊 Session stats saved: {session_data['articles_scraped']} scraped, "
                       f"{session_data['articles_rejected_blacklist']} rejected, "
                       f"{session_data['articles_skipped_duplicate']} duplicates")

        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def _save_rejections(self):
        """Save rejection details to file."""
        try:
            # Load existing rejections
            existing_rejections = self._load_rejections()

            # Add new rejections from this session
            existing_rejections.extend(self.session_rejections)

            # Sort by rejected_at descending (newest first)
            existing_rejections.sort(key=lambda r: r.get('rejected_at', ''), reverse=True)

            # Keep only last 1000 rejections to prevent file from growing too large
            if len(existing_rejections) > 1000:
                existing_rejections = existing_rejections[:1000]

            # Save to file
            with open(self.rejections_file, 'w', encoding='utf-8') as f:
                json.dump(existing_rejections, f, indent=2)

            logger.info(f"🚫 Saved {len(self.session_rejections)} new rejections")

        except Exception as e:
            logger.error(f"Failed to save rejections: {e}")

    def _load_rejections(self) -> List[Dict[str, Any]]:
        """Load existing rejections from file."""
        if os.path.exists(self.rejections_file):
            try:
                with open(self.rejections_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rejections file: {e}")
                return []
        return []

    @staticmethod
    def get_rejections(output_dir: str, source: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get rejections, optionally filtered by source.

        Args:
            output_dir: Base output directory
            source: Optional source name to filter by
            limit: Maximum number of rejections to return

        Returns:
            List of rejection entries
        """
        rejections_file = os.path.join(output_dir, 'rejections.json')
        if os.path.exists(rejections_file):
            try:
                with open(rejections_file, 'r', encoding='utf-8') as f:
                    all_rejections = json.load(f)

                if source:
                    all_rejections = [r for r in all_rejections if r.get('source') == source]

                return all_rejections[:limit]
            except Exception as e:
                logger.error(f"Failed to load rejections: {e}")
                return []
        return []

    def _load_stats(self) -> Dict[str, Any]:
        """Load existing statistics from file."""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load stats file: {e}")
                return {}
        return {}

    @staticmethod
    def get_stats(output_dir: str) -> Dict[str, Any]:
        """Get statistics for a specific date."""
        stats_file = os.path.join(output_dir, 'stats.json')
        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load stats: {e}")
                return {}
        return {}
