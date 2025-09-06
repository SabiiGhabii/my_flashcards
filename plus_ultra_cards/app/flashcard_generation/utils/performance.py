"""
Performance Optimization System

This module provides basic performance optimization for:
- Caching and memoization
- Batch processing for large content
- Memory optimization
- Progress tracking and monitoring
"""

import os
import time
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from functools import wraps, lru_cache
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    start_time: float
    end_time: float
    memory_usage_mb: float
    cards_generated: int
    processing_rate: float  # cards per second
    cache_hits: int = 0
    cache_misses: int = 0


class SimpleCache:
    """Simple caching system for content processing"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        if key in self.cache:
            self.stats["hits"] += 1
            return self.cache[key]
        else:
            self.stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any):
        """Cache result"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "cache_size": len(self.cache)
        }


def cached_processing(cache: SimpleCache):
    """Decorator for caching processing results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Process and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


class BatchProcessor:
    """Batch processing system for large content"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.cache = SimpleCache()
    
    def process_large_content(self, content: str, processor_func: Callable,
                            chunk_overlap: int = 100) -> List[Dict[str, Any]]:
        """Process large content in chunks with overlap"""
        if len(content) <= self.batch_size:
            return processor_func(content)
        
        # Split content into overlapping chunks
        chunks = self._create_overlapping_chunks(content, chunk_overlap)
        
        # Process chunks
        all_results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i + 1}/{len(chunks)}")
            result = self._process_chunk(chunk, processor_func)
            all_results.extend(result)
        
        # Deduplicate results
        return self._deduplicate_results(all_results)
    
    def _create_overlapping_chunks(self, content: str, overlap: int) -> List[str]:
        """Create overlapping chunks from content"""
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + self.batch_size, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            
            if end >= len(content):
                break
            
            # Move start position with overlap
            start = end - overlap
        
        return chunks
    
    @cached_processing
    def _process_chunk(self, chunk: str, processor_func: Callable) -> List[Dict[str, Any]]:
        """Process a single chunk with caching"""
        return processor_func(chunk)
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on content similarity"""
        unique_results = []
        seen_content = set()
        
        for result in results:
            # Create a key based on result content
            content_key = (
                result.get("type", ""),
                (result.get("front", "") + result.get("content", "")).strip().lower()
            )
            
            if content_key not in seen_content and len(content_key[1]) >= 8:
                seen_content.add(content_key)
                unique_results.append(result)
        
        return unique_results


class MemoryOptimizer:
    """Basic memory optimization utilities"""
    
    def __init__(self, memory_threshold_mb: int = 1000):
        self.memory_threshold_mb = memory_threshold_mb
        self.initial_memory = self._get_memory_usage()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB (simplified)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # Fallback if psutil not available
            return 0.0
    
    def check_memory_usage(self) -> Dict[str, float]:
        """Check current memory usage"""
        current_memory = self._get_memory_usage()
        memory_increase = current_memory - self.initial_memory
        
        return {
            "current_mb": current_memory,
            "initial_mb": self.initial_memory,
            "increase_mb": memory_increase,
            "threshold_mb": self.memory_threshold_mb,
            "over_threshold": current_memory > self.memory_threshold_mb
        }
    
    def optimize_memory(self):
        """Perform memory optimization"""
        memory_info = self.check_memory_usage()
        
        if memory_info["over_threshold"]:
            logger.warning(f"Memory usage ({memory_info['current_mb']:.1f}MB) exceeds threshold")
            
            # Force garbage collection
            gc.collect()
            
            # Check memory again
            new_memory = self._get_memory_usage()
            freed_mb = memory_info["current_mb"] - new_memory
            
            if freed_mb > 0:
                logger.info(f"Freed {freed_mb:.1f}MB of memory")
            
            return {"freed_mb": freed_mb, "new_memory_mb": new_memory}
        
        return {"freed_mb": 0, "new_memory_mb": memory_info["current_mb"]}


class ProgressTracker:
    """Progress tracking and monitoring"""
    
    def __init__(self, total_items: int, description: str = "Processing"):
        self.total_items = total_items
        self.description = description
        self.processed_items = 0
        self.start_time = time.time()
        self.last_update = self.start_time
    
    def update(self, increment: int = 1):
        """Update progress"""
        self.processed_items += increment
        current_time = time.time()
        
        # Update every 5 seconds or when complete
        if current_time - self.last_update >= 5 or self.processed_items >= self.total_items:
            self._log_progress()
            self.last_update = current_time
    
    def _log_progress(self):
        """Log current progress"""
        elapsed_time = time.time() - self.start_time
        progress_pct = (self.processed_items / self.total_items) * 100
        
        if self.processed_items > 0:
            rate = self.processed_items / elapsed_time
            eta = (self.total_items - self.processed_items) / rate if rate > 0 else 0
            
            logger.info(
                f"{self.description}: {self.processed_items}/{self.total_items} "
                f"({progress_pct:.1f}%) - {rate:.1f} items/sec - ETA: {eta:.0f}s"
            )
    
    def finish(self) -> PerformanceMetrics:
        """Finish tracking and return metrics"""
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        rate = self.processed_items / elapsed_time if elapsed_time > 0 else 0
        
        memory_optimizer = MemoryOptimizer()
        memory_info = memory_optimizer.check_memory_usage()
        
        metrics = PerformanceMetrics(
            start_time=self.start_time,
            end_time=end_time,
            memory_usage_mb=memory_info["current_mb"],
            cards_generated=self.processed_items,
            processing_rate=rate
        )
        
        logger.info(
            f"{self.description} completed: {self.processed_items} items in "
            f"{elapsed_time:.1f}s ({rate:.1f} items/sec)"
        )
        
        return metrics


class PerformanceOptimizedProcessor:
    """Main performance-optimized processing system"""
    
    def __init__(self, cache_dir: str = "cache", batch_size: int = 1000,
                 memory_threshold_mb: int = 1000):
        self.batch_processor = BatchProcessor(batch_size)
        self.memory_optimizer = MemoryOptimizer(memory_threshold_mb)
        self.cache = SimpleCache()
    
    def process_content_optimized(self, content: str, processor_func: Callable) -> Dict[str, Any]:
        """Process content with optimization"""
        # Initialize progress tracking
        estimated_cards = min(len(content) // 100, 1000)  # Rough estimate
        progress = ProgressTracker(estimated_cards, "Content Processing")
        
        try:
            # Process with batch processing for large content
            if len(content) > self.batch_processor.batch_size:
                logger.info("Using batch processing for large content")
                results = self.batch_processor.process_large_content(content, processor_func)
            else:
                results = processor_func(content)
            
            # Update progress
            progress.update(len(results))
            
            # Optimize memory
            memory_info = self.memory_optimizer.optimize_memory()
            
            # Finish progress tracking
            metrics = progress.finish()
            
            result_data = {
                "cards": results,
                "processing_time": time.time() - progress.start_time,
                "memory_info": memory_info,
                "cache_stats": self.cache.get_stats(),
                "performance_metrics": metrics
            }
            
            return result_data
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "memory_info": self.memory_optimizer.check_memory_usage(),
            "batch_size": self.batch_processor.batch_size
        }


# Factory function
def create_optimized_processor(**kwargs) -> PerformanceOptimizedProcessor:
    """Create a performance-optimized processor"""
    return PerformanceOptimizedProcessor(**kwargs)
