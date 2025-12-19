"""
Table Part Memory Optimizer

Manages memory usage for large table datasets in PyQt6 applications.
Provides caching, compression, and cleanup strategies to handle large datasets efficiently.
"""

import json
import gzip
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import logging

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out


@dataclass
class MemoryOptimizationOptions:
    """Configuration for memory optimization"""
    max_memory_mb: float = 100.0
    cleanup_threshold: float = 0.8
    compression_enabled: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    monitoring_interval_ms: int = 5000
    compression_threshold_bytes: int = 10240  # 10KB


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    used_memory_mb: float = 0.0
    max_memory_mb: float = 0.0
    cache_size: int = 0
    compression_ratio: float = 0.0
    cleanup_count: int = 0
    last_cleanup: Optional[float] = None


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    data: Any = None
    compressed_data: Optional[bytes] = None
    size_bytes: int = 0
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created: float = field(default_factory=time.time)
    is_compressed: bool = False


class TablePartMemoryOptimizer(QObject):
    """
    Memory optimizer for table part data.
    
    Features:
    - Intelligent caching with configurable eviction strategies
    - Data compression for large entries
    - Automatic cleanup when memory thresholds are exceeded
    - Performance monitoring and statistics
    """
    
    # Signals
    memoryStatsUpdated = pyqtSignal(object)  # MemoryStats
    cleanupPerformed = pyqtSignal(int, float)  # removed_count, freed_mb
    compressionCompleted = pyqtSignal(str, float)  # key, compression_ratio
    memoryThresholdExceeded = pyqtSignal(float)  # current_usage_mb
    
    def __init__(self, options: Optional[MemoryOptimizationOptions] = None):
        super().__init__()
        
        self.options = options or MemoryOptimizationOptions()
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = MemoryStats(max_memory_mb=self.options.max_memory_mb)
        
        # Monitoring timer
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self._update_stats)
        self.monitoring_timer.start(self.options.monitoring_interval_ms)
        
        # Compression lock for thread safety
        self._compression_lock = threading.Lock()
        
        logger.info(f"Memory optimizer initialized with {self.options.max_memory_mb}MB limit")
    
    def store(self, key: str, data: Any) -> bool:
        """
        Store data in optimized cache.
        
        Args:
            key: Unique identifier for the data
            data: Data to store
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Estimate size
            size_bytes = self._estimate_size(data)
            
            # Check if cleanup is needed
            if self._should_cleanup(size_bytes):
                self.cleanup()
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=data,
                size_bytes=size_bytes,
                access_count=1
            )
            
            # Compress if enabled and data is large enough
            if (self.options.compression_enabled and 
                size_bytes > self.options.compression_threshold_bytes):
                
                compressed_data = self._compress_data(data)
                if compressed_data and len(compressed_data) < size_bytes:
                    entry.compressed_data = compressed_data
                    entry.size_bytes = len(compressed_data)
                    entry.is_compressed = True
                    entry.data = None  # Clear original data to save memory
                    
                    compression_ratio = len(compressed_data) / size_bytes
                    self.compressionCompleted.emit(key, compression_ratio)
                    
                    logger.debug(f"Compressed {key}: {size_bytes} -> {len(compressed_data)} bytes "
                               f"({compression_ratio:.2%})")
            
            # Store in cache
            self.cache[key] = entry
            self._update_stats()
            
            logger.debug(f"Stored {key} ({entry.size_bytes} bytes, compressed: {entry.is_compressed})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.
        
        Args:
            key: Unique identifier for the data
            
        Returns:
            Cached data or None if not found
        """
        entry = self.cache.get(key)
        if not entry:
            return None
        
        try:
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # Decompress if needed
            if entry.is_compressed and entry.compressed_data:
                if entry.data is None:
                    entry.data = self._decompress_data(entry.compressed_data)
                return entry.data
            
            return entry.data
            
        except Exception as e:
            logger.error(f"Failed to retrieve {key}: {e}")
            # Remove corrupted entry
            self.delete(key)
            return None
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        return key in self.cache
    
    def delete(self, key: str) -> bool:
        """Remove entry from cache"""
        if key in self.cache:
            del self.cache[key]
            self._update_stats()
            logger.debug(f"Deleted {key} from cache")
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self._update_stats()
        logger.info("Cache cleared")
    
    def cleanup(self) -> Tuple[int, float]:
        """
        Perform cache cleanup to free memory.
        
        Returns:
            Tuple of (removed_count, freed_mb)
        """
        target_size_mb = self.options.max_memory_mb * self.options.cleanup_threshold
        current_size_mb = self.stats.used_memory_mb
        
        if current_size_mb <= target_size_mb:
            return 0, 0.0
        
        # Get entries sorted by eviction strategy
        entries = list(self.cache.items())
        sorted_entries = self._sort_entries_for_cleanup(entries)
        
        removed_count = 0
        freed_bytes = 0
        
        # Remove entries until we're under the target size
        for key, entry in sorted_entries:
            if current_size_mb - (freed_bytes / (1024 * 1024)) <= target_size_mb:
                break
            
            freed_bytes += entry.size_bytes
            removed_count += 1
            del self.cache[key]
        
        freed_mb = freed_bytes / (1024 * 1024)
        
        # Update statistics
        self.stats.cleanup_count += 1
        self.stats.last_cleanup = time.time()
        self._update_stats()
        
        # Emit signals
        self.cleanupPerformed.emit(removed_count, freed_mb)
        
        logger.info(f"Cleanup completed: removed {removed_count} entries, freed {freed_mb:.2f}MB")
        return removed_count, freed_mb
    
    def optimize_memory(self) -> Tuple[int, float]:
        """
        Optimize memory usage by compressing uncompressed entries.
        
        Returns:
            Tuple of (optimized_count, saved_mb)
        """
        if not self.options.compression_enabled:
            return 0, 0.0
        
        optimized_count = 0
        saved_bytes = 0
        
        for entry in list(self.cache.values()):
            if (not entry.is_compressed and 
                entry.data is not None and 
                entry.size_bytes > self.options.compression_threshold_bytes):
                
                try:
                    compressed_data = self._compress_data(entry.data)
                    if compressed_data and len(compressed_data) < entry.size_bytes:
                        original_size = entry.size_bytes
                        
                        entry.compressed_data = compressed_data
                        entry.size_bytes = len(compressed_data)
                        entry.is_compressed = True
                        entry.data = None  # Clear original data
                        
                        saved_bytes += (original_size - entry.size_bytes)
                        optimized_count += 1
                        
                        compression_ratio = len(compressed_data) / original_size
                        self.compressionCompleted.emit(entry.key, compression_ratio)
                        
                except Exception as e:
                    logger.warning(f"Failed to compress {entry.key}: {e}")
        
        saved_mb = saved_bytes / (1024 * 1024)
        
        if optimized_count > 0:
            self._update_stats()
            logger.info(f"Memory optimization: compressed {optimized_count} entries, "
                       f"saved {saved_mb:.2f}MB")
        
        return optimized_count, saved_mb
    
    def preload_data(
        self, 
        keys: List[str], 
        load_fn: callable, 
        batch_size: int = 10
    ):
        """
        Preload data with memory-aware batching.
        
        Args:
            keys: List of keys to preload
            load_fn: Function to load data for a key
            batch_size: Number of items to load per batch
        """
        batches = [keys[i:i + batch_size] for i in range(0, len(keys), batch_size)]
        
        for batch in batches:
            # Check memory before each batch
            if self._should_cleanup():
                self.cleanup()
            
            # Load batch
            for key in batch:
                if not self.has(key):
                    try:
                        data = load_fn(key)
                        self.store(key, data)
                    except Exception as e:
                        logger.error(f"Failed to preload {key}: {e}")
            
            # Small delay between batches
            time.sleep(0.01)
    
    def get_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        return self.stats
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        total_size = sum(entry.size_bytes for entry in self.cache.values())
        compressed_count = sum(1 for entry in self.cache.values() if entry.is_compressed)
        
        return {
            'total_entries': len(self.cache),
            'compressed_entries': compressed_count,
            'total_size_mb': total_size / (1024 * 1024),
            'compression_ratio': compressed_count / len(self.cache) if self.cache else 0,
            'cache_strategy': self.options.cache_strategy.value,
            'max_memory_mb': self.options.max_memory_mb
        }
    
    def cleanup_resources(self):
        """Cleanup resources and stop monitoring"""
        self.monitoring_timer.stop()
        self.clear()
        logger.info("Memory optimizer resources cleaned up")
    
    # Private methods
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate size of data in bytes"""
        try:
            # Convert to JSON string and estimate size
            json_str = json.dumps(data, default=str)
            return len(json_str.encode('utf-8'))
        except Exception:
            # Fallback estimation
            return len(str(data).encode('utf-8'))
    
    def _compress_data(self, data: Any) -> Optional[bytes]:
        """Compress data using gzip"""
        try:
            with self._compression_lock:
                json_str = json.dumps(data, default=str)
                return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return None
    
    def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data using gzip"""
        with self._compression_lock:
            json_str = gzip.decompress(compressed_data).decode('utf-8')
            return json.loads(json_str)
    
    def _should_cleanup(self, additional_size_bytes: int = 0) -> bool:
        """Check if cleanup is needed"""
        projected_size_mb = (
            self.stats.used_memory_mb + 
            (additional_size_bytes / (1024 * 1024))
        )
        threshold_mb = self.options.max_memory_mb * self.options.cleanup_threshold
        return projected_size_mb > threshold_mb
    
    def _sort_entries_for_cleanup(
        self, 
        entries: List[Tuple[str, CacheEntry]]
    ) -> List[Tuple[str, CacheEntry]]:
        """Sort entries based on cache strategy"""
        if self.options.cache_strategy == CacheStrategy.LRU:
            return sorted(entries, key=lambda x: x[1].last_accessed)
        elif self.options.cache_strategy == CacheStrategy.LFU:
            return sorted(entries, key=lambda x: x[1].access_count)
        elif self.options.cache_strategy == CacheStrategy.FIFO:
            return sorted(entries, key=lambda x: x[1].created)
        else:
            return entries
    
    def _update_stats(self):
        """Update memory statistics"""
        total_size_bytes = sum(entry.size_bytes for entry in self.cache.values())
        compressed_size_bytes = sum(
            entry.size_bytes for entry in self.cache.values() 
            if entry.is_compressed
        )
        
        self.stats.used_memory_mb = total_size_bytes / (1024 * 1024)
        self.stats.cache_size = len(self.cache)
        
        if total_size_bytes > 0:
            self.stats.compression_ratio = compressed_size_bytes / total_size_bytes
        else:
            self.stats.compression_ratio = 0.0
        
        # Check for threshold exceeded
        if self.stats.used_memory_mb > self.options.max_memory_mb:
            self.memoryThresholdExceeded.emit(self.stats.used_memory_mb)
        
        # Emit updated stats
        self.memoryStatsUpdated.emit(self.stats)


def create_memory_optimizer(
    options: Optional[MemoryOptimizationOptions] = None
) -> TablePartMemoryOptimizer:
    """Factory function to create a memory optimizer"""
    return TablePartMemoryOptimizer(options)