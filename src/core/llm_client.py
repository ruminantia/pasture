"""LLM client for post-processing scraped articles."""

import logging
import requests
import json
from typing import Optional

logger = logging.getLogger(__name__)


class NonRetryableError(Exception):
    """Exception for errors that shouldn't be retried."""
    pass


DEFAULT_SYSTEM_PROMPT = "This is a scraped page (article). It contains some artifacts and loose ends. Please squeeze out its substance and rewrite it as a brief, well formatted, article. Avoid bullet points and / or section titles. The goal is one uniform flowing body which delivers the original story to the reader without altering it."


class LLMClient:
    """Client for interacting with Llama.cpp-compatible LLM APIs."""

    def __init__(
        self,
        base_url: str,
        model: str = "gemma",
        temperature: float = 1.0,
        timeout: int = 600,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        """Initialize the LLM client.

        Args:
            base_url: Base URL for the LLM API (e.g., http://192.168.68.81:8080/v1)
            model: Model name to use
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            system_prompt: System prompt to use
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.system_prompt = system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT
        self.chat_url = f"{self.base_url}/chat/completions"

    def process_content(self, content: str, retry: bool = True) -> Optional[str]:
        """Process content through the LLM.

        Args:
            content: The content to process
            retry: Whether to retry once on failure

        Returns:
            Processed content, or None if processing failed
        """
        if not content or not content.strip():
            logger.warning("Empty content provided to LLM")
            return None

        return self._process_with_retry(content, max_retries=1 if retry else 0)

    def _process_with_retry(self, content: str, max_retries: int = 1) -> Optional[str]:
        """Process content with retry logic.

        Args:
            content: The content to process
            max_retries: Maximum number of retry attempts

        Returns:
            Processed content, or None if all attempts failed
        """
        for attempt in range(max_retries + 1):
            try:
                result = self._make_request(content)
                if result:
                    return result
            except NonRetryableError as e:
                # Don't retry non-retryable errors (context length, 4xx, etc.)
                logger.warning(f"Non-retryable LLM error: {e}")
                return None
            except requests.exceptions.ConnectionError as e:
                # Connection refused/reset - server is down, don't retry
                if 'refused' in str(e).lower() or 'reset' in str(e).lower():
                    logger.warning(f"LLM server unavailable: {e}")
                    return None
                logger.warning(f"LLM connection failed: {e} (attempt {attempt + 1}/{max_retries + 1})")
            except requests.exceptions.Timeout:
                logger.warning(f"LLM request timed out (attempt {attempt + 1}/{max_retries + 1})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"LLM request failed: {e} (attempt {attempt + 1}/{max_retries + 1})")
            except Exception as e:
                logger.error(f"Unexpected error during LLM processing: {e}")
                # Don't retry on unexpected errors
                return None

        logger.error(f"LLM processing failed after {max_retries + 1} attempts")
        return None

    def _make_request(self, content: str) -> Optional[str]:
        """Make a single request to the LLM API.

        Args:
            content: The content to process

        Returns:
            Processed content, or None if request failed

        Raises:
            requests.exceptions.RequestException: On HTTP errors
            NonRetryableError: On errors that shouldn't be retried
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content}
            ],
            "temperature": self.temperature,
            "stream": False
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            self.chat_url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )

        # Check for non-retryable errors before raising
        if not response.ok:
            if self._is_context_length_error(response):
                error_msg = "Context length exceeded"
                try:
                    data = response.json()
                    error_msg = data.get('error', {}).get('message', error_msg)
                except Exception:
                    pass
                logger.error(f"🚫 {error_msg} - skipping article")
                raise NonRetryableError(error_msg)
            elif self._is_non_retryable_error(response):
                error_msg = f"HTTP {response.status_code}"
                try:
                    data = response.json()
                    error_msg = data.get('error', {}).get('message', error_msg)
                except Exception:
                    pass
                logger.error(f"🚫 Non-retryable LLM error: {error_msg}")
                raise NonRetryableError(error_msg)

        response.raise_for_status()
        data = response.json()

        # Extract the response content
        try:
            content = data['choices'][0]['message']['content']
            logger.debug(f"Received LLM response: {len(content)} characters")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected LLM response format: {e}")
            logger.debug(f"Response data: {data}")
            return None

    def _is_context_length_error(self, response: requests.Response) -> bool:
        """Check if the response indicates a context length error.

        Args:
            response: The HTTP response object

        Returns:
            True if this is a context length exceeded error
        """
        if response.status_code == 400:
            try:
                data = response.json()
                error_msg = data.get('error', {}).get('message', '').lower()
                error_type = data.get('error', {}).get('type', '').lower()
                # Common error messages for context length issues
                if any(keyword in error_msg or keyword in error_type for keyword in [
                    'context', 'length', 'too long', 'exceed', 'tokens', 'maximum'
                ]):
                    return True
            except Exception:
                pass
        return False

    def _is_non_retryable_error(self, response: requests.Response) -> bool:
        """Check if the response indicates a non-retryable error.

        Args:
            response: The HTTP response object

        Returns:
            True if this error should not be retried
        """
        # Context length errors - don't retry
        if self._is_context_length_error(response):
            return True
        # Client errors (4xx) except 429 (rate limit) are non-retryable
        if 400 <= response.status_code < 500 and response.status_code != 429:
            return True
        return False

    @classmethod
    def from_config(cls, config: dict) -> Optional['LLMClient']:
        """Create an LLMClient from configuration dict.

        Args:
            config: Configuration dictionary with LLM settings

        Returns:
            LLMClient instance, or None if LLM is disabled or config is invalid
        """
        if not config.get('enabled', False):
            return None

        base_url = config.get('base_url')
        if not base_url:
            logger.warning("LLM enabled but no base_url configured")
            return None

        return cls(
            base_url=base_url,
            model=config.get('model', 'gemma'),
            temperature=float(config.get('temperature', 0.2)),
            timeout=int(config.get('timeout', 600)),
            system_prompt=config.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
        )
