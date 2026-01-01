"""Statistics tracking for Pasture scraper."""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class StatsTracker:
    """Track scraping statistics."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.stats_file = os.path.join(output_dir, 'stats.json')
        self.session_stats = {
            'start_time': datetime.now().isoformat(),
            'articles_scraped': 0,
            'articles_skipped_duplicate': 0,
            'articles_rejected_blacklist': 0,
            'blacklist_hits_by_term': defaultdict(int),
            'articles_by_source': defaultdict(int),
            'errors': 0,
            'sources_processed': []
        }

    def increment_scraped(self, source: str):
        """Increment articles scraped counter."""
        self.session_stats['articles_scraped'] += 1
        self.session_stats['articles_by_source'][source] += 1

    def increment_duplicate(self):
        """Increment duplicate articles counter."""
        self.session_stats['articles_skipped_duplicate'] += 1

    def increment_blacklisted(self, term: str):
        """Increment blacklisted articles counter."""
        self.session_stats['articles_rejected_blacklist'] += 1
        self.session_stats['blacklist_hits_by_term'][term] += 1

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
            session_date = datetime.now().strftime('%Y-%m-%d')
            session_time = datetime.now().strftime('%H:%M:%S')

            if 'sessions' not in all_stats:
                all_stats['sessions'] = []

            if 'daily' not in all_stats:
                all_stats['daily'] = {}

            # Convert defaultdicts to regular dicts for JSON serialization
            session_data = {
                'date': session_date,
                'time': session_time,
                'start_time': self.session_stats['start_time'],
                'end_time': datetime.now().isoformat(),
                'articles_scraped': self.session_stats['articles_scraped'],
                'articles_skipped_duplicate': self.session_stats['articles_skipped_duplicate'],
                'articles_rejected_blacklist': self.session_stats['articles_rejected_blacklist'],
                'blacklist_hits_by_term': dict(self.session_stats['blacklist_hits_by_term']),
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
                    'articles_by_source': {},
                    'sessions_count': 0
                }

            daily = all_stats['daily'][session_date]
            daily['articles_scraped'] += session_data['articles_scraped']
            daily['articles_rejected_blacklist'] += session_data['articles_rejected_blacklist']
            daily['articles_skipped_duplicate'] += session_data['articles_skipped_duplicate']
            daily['sessions_count'] += 1

            # Merge blacklist hits
            for term, count in session_data['blacklist_hits_by_term'].items():
                daily['blacklist_hits_by_term'][term] = daily['blacklist_hits_by_term'].get(term, 0) + count

            # Merge source counts
            for source, count in session_data['articles_by_source'].items():
                daily['articles_by_source'][source] = daily['articles_by_source'].get(source, 0) + count

            # Keep only last 90 days
            dates_to_keep = sorted(all_stats['daily'].keys(), reverse=True)[:90]
            all_stats['daily'] = {k: v for k, v in all_stats['daily'].items() if k in dates_to_keep}

            # Save to file
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(all_stats, f, indent=2)

            logger.info(f"📊 Session stats saved: {session_data['articles_scraped']} scraped, "
                       f"{session_data['articles_rejected_blacklist']} rejected, "
                       f"{session_data['articles_skipped_duplicate']} duplicates")

        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

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
