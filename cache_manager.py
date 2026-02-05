"""Cache manager for Yahoo Finance MCP server with TTL support."""

import time
from collections import OrderedDict
from typing import Any, Optional
from threading import Lock


class CacheManager:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 100):
        """Initialize cache manager.
        
        Args:
            max_size: Maximum number of cache entries
        """
        self._cache: OrderedDict[str, tuple[Any, float, float]] = OrderedDict()
        self._max_size = max_size
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def _generate_key(self, func_name: str, **kwargs) -> str:
        """Generate cache key from function name and arguments.
        
        Args:
            func_name: Name of the function
            **kwargs: Function arguments
            
        Returns:
            Cache key string
        """
        # Sort kwargs for consistent key generation
        sorted_args = sorted(kwargs.items())
        args_str = "_".join(f"{k}={v}" for k, v in sorted_args)
        return f"{func_name}:{args_str}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, timestamp, ttl = self._cache[key]
            
            # Check if expired
            if time.time() - timestamp > ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        with self._lock:
            # Remove oldest entry if at max size
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._cache.popitem(last=False)

            self._cache[key] = (value, time.time(), ttl_seconds)
            self._cache.move_to_end(key)

    def get_or_set(self, key: str, factory_func, ttl_seconds: float) -> tuple[Any, bool]:
        """Get from cache or compute and cache the result.
        
        Args:
            key: Cache key
            factory_func: Function to call if cache miss
            ttl_seconds: Time to live in seconds
            
        Returns:
            Tuple of (value, was_cached)
        """
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value, True

        # Compute value
        value = factory_func()
        self.set(key, value, ttl_seconds)
        return value, False

    def get_age(self, key: str) -> Optional[float]:
        """Get age of cached item in seconds.
        
        Args:
            key: Cache key
            
        Returns:
            Age in seconds or None if not found
        """
        with self._lock:
            if key not in self._cache:
                return None
            _, timestamp, _ = self._cache[key]
            return time.time() - timestamp

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2%}",
            }


# Global cache instance
_global_cache = CacheManager(max_size=100)


def get_cache() -> CacheManager:
    """Get global cache instance."""
    return _global_cache
