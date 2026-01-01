"""Config reload trigger for inter-thread communication.

This module provides a mechanism for the web UI to trigger config reloads
in the main scheduler thread.
"""

import threading
import logging

logger = logging.getLogger(__name__)


# Global event for triggering config reload
_config_reload_event = threading.Event()


def trigger_config_reload():
    """Trigger a config reload from external modules (e.g., web_viewer)."""
    _config_reload_event.set()
    logger.debug("Config reload event triggered")


def wait_for_reload(timeout: float = None) -> bool:
    """Wait for config reload event.

    Args:
        timeout: Optional timeout in seconds

    Returns:
        True if event was set, False if timeout occurred
    """
    return _config_reload_event.wait(timeout=timeout)


def is_reload_pending() -> bool:
    """Check if a config reload is pending.

    Returns:
        True if reload event is set
    """
    return _config_reload_event.is_set()


def clear_reload():
    """Clear the config reload event."""
    _config_reload_event.clear()
    logger.debug("Config reload event cleared")
