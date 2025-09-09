import time
import logging
from functools import wraps
from typing import Callable, Any, Type, Tuple
from config.settings import settings


def retry_with_delay(exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    """재시도 데코레이터"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(settings.RETRY_COUNT + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    if attempt == settings.RETRY_COUNT:
                        logger.error(f"{func.__name__} 최종 실패 (시도: {attempt + 1}): {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} 실패 (시도: {attempt + 1}/{settings.RETRY_COUNT + 1}): {e}")
                    
                    if settings.RETRY_DELAY > 0:
                        logger.info(f"{settings.RETRY_DELAY}초 후 재시도...")
                        time.sleep(settings.RETRY_DELAY)
            
        return wrapper
    return decorator