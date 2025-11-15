"""
Retry utilities for handling transient failures.

This module provides retry decorators and utilities for handling
failures that may be transient (e.g., network errors, model loading).
"""
import time
import logging
from typing import Callable, Type, Tuple, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
                  Signature: (exception, attempt_number) -> None
    
    Example:
        @retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
        def load_model():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt)
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator

