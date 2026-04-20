"""Background LLM processing queue for post-processing scraped articles."""

import os
import logging
import threading
import queue
import time
from typing import Optional, Dict, Any
from pathlib import Path

from core.llm_client import LLMClient, NonRetryableError
from core.llm_status import get_global_tracker

logger = logging.getLogger(__name__)


class LLMTask:
    """A task for LLM processing."""

    def __init__(self, md_file_path: str, pasture_config: dict, llm_config: dict):
        """Initialize an LLM task.

        Args:
            md_file_path: Path to the raw markdown file
            pasture_config: Configuration for this pasture (for per-pasture overrides)
            llm_config: Global LLM configuration
        """
        self.md_file_path = md_file_path
        self.pasture_config = pasture_config
        self.llm_config = llm_config
        self.created_at = time.time()

    def get_llm_client(self) -> Optional[LLMClient]:
        """Get an LLM client for this task.

        Returns:
            LLMClient instance or None if disabled/invalid
        """
        # Check per-pasture override
        pasture_llm_enabled = self.pasture_config.get('llm_enabled', None)
        if pasture_llm_enabled is not None:
            if not pasture_llm_enabled:
                return None
            # Use pasture-specific config
            config = {
                'enabled': True,
                'base_url': self.pasture_config.get('llm_base_url', self.llm_config.get('base_url')),
                'model': self.pasture_config.get('llm_model', self.llm_config.get('model', 'gemma')),
                'temperature': self.pasture_config.get('llm_temperature', self.llm_config.get('temperature', 1.0)),
                'timeout': self.pasture_config.get('llm_timeout', self.llm_config.get('timeout', 600)),
                'system_prompt': self.pasture_config.get('llm_system_prompt', self.llm_config.get('system_prompt')),
            }
        else:
            # Use global config
            config = self.llm_config

        return LLMClient.from_config(config)

    def process(self) -> bool:
        """Process this task.

        Returns:
            True if processing succeeded, False otherwise
        """
        tracker = get_global_tracker()
        basename = os.path.basename(self.md_file_path)

        client = self.get_llm_client()
        if not client:
            logger.debug(f"LLM disabled for {basename}, skipping")
            return False

        if not os.path.exists(self.md_file_path):
            logger.warning(f"Source file not found: {self.md_file_path}")
            if tracker:
                tracker.set_failed(basename)
            return False

        # Check if already processed
        llm_file_path = self.get_output_path()
        if os.path.exists(llm_file_path):
            logger.debug(f"LLM file already exists: {llm_file_path}")
            if tracker:
                tracker.set_completed(basename)
            return True

        # Mark as processing
        if tracker:
            tracker.set_processing(basename)

        try:
            # Read the content
            with open(self.md_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                logger.warning(f"Empty content in {basename}")
                if tracker:
                    tracker.set_failed(basename)
                return False

            # Process with LLM
            logger.info(f"🤖 Processing {basename} with LLM...")
            processed_content = client.process_content(content, retry=True)

            if processed_content:
                # Write the processed content
                with open(llm_file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                logger.info(f"✅ LLM processed: {basename}")
                if tracker:
                    tracker.set_completed(basename)
                return True
            else:
                logger.warning(f"❌ LLM processing failed for {basename}")
                if tracker:
                    tracker.set_failed(basename)
                return False

        except NonRetryableError as e:
            # Non-retryable errors (context length, etc.) - log and continue
            logger.warning(f"⚠️ Skipped LLM processing for {basename}: {e}")
            if tracker:
                tracker.set_failed(basename)
            return False
        except Exception as e:
            logger.error(f"❌ Error processing {self.md_file_path}: {e}")
            if tracker:
                tracker.set_failed(basename)
            return False

    def get_output_path(self) -> str:
        """Get the output file path for the processed content."""
        path = Path(self.md_file_path)
        # article.md -> article.llm.md
        return str(path.with_suffix('.llm.md'))


class LLMProcessor:
    """Background processor for LLM tasks."""

    def __init__(self, llm_config: dict, num_workers: int = 1):
        """Initialize the LLM processor.

        Args:
            llm_config: Global LLM configuration
            num_workers: Number of worker threads (usually 1 for local LLM)
        """
        self.llm_config = llm_config
        self.num_workers = num_workers
        self.task_queue: queue.Queue[LLMTask] = queue.Queue()
        self.workers: list[threading.Thread] = []
        self.running = False
        self.stats = {
            'queued': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0
        }

    def start(self):
        """Start the background workers."""
        if self.running:
            logger.warning("LLM processor already running")
            return

        if not self.llm_config.get('enabled', False):
            logger.info("LLM processing disabled, not starting processor")
            return

        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"LLMWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        logger.info(f"🤖 LLM processor started with {self.num_workers} worker(s)")

    def stop(self):
        """Stop the background workers."""
        if not self.running:
            return

        self.running = False
        # Add None sentinels to unblock workers
        for _ in range(self.num_workers):
            self.task_queue.put(None)

        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)

        self.workers.clear()
        logger.info("🤖 LLM processor stopped")

    def enqueue(self, md_file_path: str, pasture_config: dict) -> bool:
        """Enqueue a file for LLM processing.

        Args:
            md_file_path: Path to the raw markdown file
            pasture_config: Configuration for this pasture

        Returns:
            True if enqueued, False if LLM is disabled
        """
        if not self.running:
            return False

        # Mark as pending in status tracker
        tracker = get_global_tracker()
        if tracker:
            tracker.set_pending(os.path.basename(md_file_path))

        task = LLMTask(md_file_path, pasture_config, self.llm_config)
        self.task_queue.put(task)
        self.stats['queued'] += 1
        return True

    def _worker_loop(self):
        """Worker loop that processes tasks from the queue."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                if task is None:  # Sentinel to stop
                    break

                # Check if LLM is enabled for this task
                client = task.get_llm_client()
                if client is None:
                    self.stats['skipped'] += 1
                    self.task_queue.task_done()
                    continue

                # Process the task
                success = task.process()
                if success:
                    self.stats['processed'] += 1
                else:
                    self.stats['failed'] += 1

                self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in LLM worker: {e}")
                self.stats['failed'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics.

        Returns:
            Dictionary with stats
        """
        return {
            **self.stats,
            'queue_size': self.task_queue.qsize(),
            'running': self.running
        }

    def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for all queued tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds
        """
        self.task_queue.join()


# Global singleton instance
_global_processor: Optional[LLMProcessor] = None


def get_global_processor() -> Optional[LLMProcessor]:
    """Get the global LLM processor instance.

    Returns:
        LLMProcessor instance or None
    """
    return _global_processor


def init_global_processor(llm_config: dict, num_workers: int = 1) -> LLMProcessor:
    """Initialize the global LLM processor.

    Args:
        llm_config: Global LLM configuration
        num_workers: Number of worker threads

    Returns:
        LLMProcessor instance
    """
    global _global_processor

    if _global_processor is not None:
        _global_processor.stop()

    _global_processor = LLMProcessor(llm_config, num_workers)
    _global_processor.start()
    return _global_processor


def shutdown_global_processor():
    """Shutdown the global LLM processor."""
    global _global_processor

    if _global_processor is not None:
        _global_processor.stop()
        _global_processor = None
