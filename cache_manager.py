"""
Thread-safe LRU cache manager with TTL support for Yahoo Finance MCP server.
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional, Tuple


class CacheManager:
    """Thread-safe LRU cache with TTL (Time To Live) support."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize cache manager.
        
        Args:
            max_size: Maximum number of entries in cache (LRU eviction)
        """
        self._cache: OrderedDict[str, Tuple[Any, float, float]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Tuple[Any, float]]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Args:
            key: Cache key
            
        Returns:
            Tuple of (value, age_seconds) if found and valid, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, timestamp, ttl = self._cache[key]
            age = time.time() - timestamp
            
            # Check if expired
            if age > ttl:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return (value, age)
    
    def set(self, key: str, value: Any, ttl_seconds: float):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._cache.popitem(last=False)
            
            self._cache[key] = (value, time.time(), ttl_seconds)
            self._cache.move_to_end(key)
    
    def get_or_set(
        self,
        key: str,
        factory_func: Callable[[], Any],
        ttl_seconds: float
    ) -> Tuple[Any, Optional[float]]:
        """
        Get from cache or compute and cache if missing/expired.
        
        Args:
            key: Cache key
            factory_func: Function to call if cache miss
            ttl_seconds: TTL for new cache entries
            
        Returns:
            Tuple of (value, age_seconds). age_seconds is None for cache miss.
        """
        # Try to get from cache
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - compute value
        try:
            value = factory_func()
            self.set(key, value, ttl_seconds)
            return (value, None)  # None age indicates fresh data
        except Exception as e:
            # Don't cache errors
            raise e
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, size, and hit rate
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_rate": f"{hit_rate:.1f}%"
            }


# Global cache instance
_global_cache: Optional[CacheManager] = None
_cache_lock = threading.Lock()


def get_cache() -> CacheManager:
    """
    Get the global cache instance (singleton pattern).
    
    Returns:
        Global CacheManager instance
    """
    global _global_cache
    
    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = CacheManager(max_size=100)
    
    return _global_cache
