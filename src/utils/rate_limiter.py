"""Rate limiting and retry logic for API calls."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from anthropic import RateLimitError, APIError
from src.utils.logger import logger


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, tokens_per_minute: int = 60, burst_size: int = 10):
        """Initialize rate limiter.
        
        Args:
            tokens_per_minute: Maximum tokens per minute
            burst_size: Maximum burst size
        """
        self.tokens_per_minute = tokens_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
        """
        async with self.lock:
            # Refill tokens
            now = time.time()
            elapsed = now - self.last_refill
            refill = (elapsed / 60) * self.tokens_per_minute
            self.tokens = min(self.burst_size, self.tokens + refill)
            self.last_refill = now
            
            # Wait if not enough tokens
            while self.tokens < tokens:
                wait_time = (tokens - self.tokens) * 60 / self.tokens_per_minute
                logger.debug(f"Rate limited, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                
                # Refill again
                now = time.time()
                elapsed = now - self.last_refill
                refill = (elapsed / 60) * self.tokens_per_minute
                self.tokens = min(self.burst_size, self.tokens + refill)
                self.last_refill = now
            
            # Consume tokens
            self.tokens -= tokens


class APIRetry:
    """Retry decorator for API calls."""
    
    @staticmethod
    def with_retry(
        max_attempts: int = 3,
        wait_multiplier: int = 2,
        max_wait: int = 60
    ):
        """Create retry decorator.
        
        Args:
            max_attempts: Maximum retry attempts
            wait_multiplier: Exponential backoff multiplier
            max_wait: Maximum wait time between retries
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @retry(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=wait_multiplier, max=max_wait),
                retry=retry_if_exception_type((RateLimitError, APIError, ConnectionError)),
                before_sleep=before_sleep_log(logger, "WARNING")
            )
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except RateLimitError as e:
                    logger.warning(f"Rate limit hit: {e}")
                    raise
                except APIError as e:
                    logger.error(f"API error: {e}")
                    raise
                except ConnectionError as e:
                    logger.error(f"Connection error: {e}")
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    raise
            
            return wrapper
        return decorator


class GlobalRateLimiter:
    """Global rate limiter for all API calls."""
    
    _instances: Dict[str, RateLimiter] = {}
    
    @classmethod
    def get_limiter(cls, name: str = "default", **kwargs) -> RateLimiter:
        """Get or create a rate limiter.
        
        Args:
            name: Limiter name
            **kwargs: RateLimiter constructor arguments
            
        Returns:
            RateLimiter instance
        """
        if name not in cls._instances:
            cls._instances[name] = RateLimiter(**kwargs)
        return cls._instances[name]


# Preset rate limiters for different services
class RateLimiters:
    """Preset rate limiters."""
    
    # Anthropic API limits (adjust based on your tier)
    anthropic_llm = GlobalRateLimiter.get_limiter(
        "anthropic_llm",
        tokens_per_minute=100,  # Adjust based on your API tier
        burst_size=20
    )
    
    # Web search limits
    web_search = GlobalRateLimiter.get_limiter(
        "web_search",
        tokens_per_minute=60,
        burst_size=10
    )
    
    # Web fetch limits
    web_fetch = GlobalRateLimiter.get_limiter(
        "web_fetch",
        tokens_per_minute=30,
        burst_size=5
    )


def rate_limited(limiter: RateLimiter, tokens: int = 1):
    """Rate limiting decorator.
    
    Args:
        limiter: RateLimiter instance
        tokens: Tokens to consume per call
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire(tokens)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage decorators
def anthropic_rate_limited(tokens: int = 1):
    """Rate limit Anthropic API calls."""
    return rate_limited(RateLimiters.anthropic_llm, tokens)


def search_rate_limited(tokens: int = 1):
    """Rate limit search API calls."""
    return rate_limited(RateLimiters.web_search, tokens)


def fetch_rate_limited(tokens: int = 1):
    """Rate limit web fetch calls."""
    return rate_limited(RateLimiters.web_fetch, tokens)