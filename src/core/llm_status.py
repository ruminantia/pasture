"""Track LLM processing status for articles."""

import json
import os
import threading
from typing import Dict, Optional
from datetime import datetime


class LLMStatusTracker:
    """Track LLM processing status for articles."""

    def __init__(self, output_dir: str):
        """Initialize the status tracker.

        Args:
            output_dir: Base output directory
        """
        self.output_dir = output_dir
        self.status_file = os.path.join(output_dir, "llm_status.json")
        self.lock = threading.Lock()
        self._status: Dict[str, str] = {}
        self._load()

    def _load(self):
        """Load status from disk."""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r') as f:
                    self._status = json.load(f)
            except Exception:
                self._status = {}

    def _save(self):
        """Save status to disk."""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self._status, f)
        except Exception:
            pass

    def set_pending(self, md_file: str):
        """Mark an article as pending LLM processing."""
        with self.lock:
            self._status[md_file] = 'pending'
            self._save()

    def set_processing(self, md_file: str):
        """Mark an article as currently being processed."""
        with self.lock:
            self._status[md_file] = 'processing'
            self._save()

    def set_completed(self, md_file: str):
        """Mark an article as successfully processed."""
        with self.lock:
            self._status[md_file] = 'completed'
            self._save()

    def set_failed(self, md_file: str):
        """Mark an article as failed to process."""
        with self.lock:
            self._status[md_file] = 'failed'
            self._save()

    def get_status(self, md_file: str) -> str:
        """Get the status of an article.

        Returns:
            'pending', 'processing', 'completed', 'failed', or 'unknown'
        """
        with self.lock:
            return self._status.get(md_file, 'unknown')

    def get_all_status(self) -> Dict[str, str]:
        """Get all statuses."""
        with self.lock:
            return dict(self._status)

    def cleanup_old_entries(self, existing_files: set):
        """Remove entries for files that no longer exist.

        Args:
            existing_files: Set of existing markdown files
        """
        with self.lock:
            to_remove = [f for f in self._status if f not in existing_files]
            for f in to_remove:
                del self._status[f]
            if to_remove:
                self._save()


# Global singleton
_global_tracker: Optional[LLMStatusTracker] = None


def get_global_tracker() -> Optional[LLMStatusTracker]:
    """Get the global LLM status tracker."""
    return _global_tracker


def init_global_tracker(output_dir: str) -> LLMStatusTracker:
    """Initialize the global LLM status tracker."""
    global _global_tracker
    _global_tracker = LLMStatusTracker(output_dir)
    return _global_tracker
