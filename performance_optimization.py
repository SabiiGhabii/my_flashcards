#!/usr/bin/env python3
"""
Performance Optimization System

This module provides comprehensive performance optimization for:
- Caching and memoization
- Batch processing for large content
- Memory optimization
- Parallel processing
- Progress tracking and monitoring
"""

import os
import pickle
import hashlib
import time
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Iterator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import wraps, lru_cache
import logging
import psutil

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


class CacheManager:
    """Advanced caching system for content processing"""
    
    def __init__(self, cache_dir: str = "cache", max_cache_size_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_stats = {"hits": 0, "misses": 0}
        
        # Clean old cache files on startup
        self._cleanup_old_cache()
    
    def _get_cache_key(self, content: str, processing_params: Dict[str, Any]) -> str:
        """Generate cache key from content and parameters"""
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        params_str = str(sorted(processing_params.items()))
        params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()
        return f"{content_hash}_{params_hash}"
    
    def get(self, content: str, processing_params: Dict[str, Any]) -> Optional[Any]:
        """Get cached result"""
        cache_key = self._get_cache_key(content, processing_params)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    result = pickle.load(f)
                self.cache_stats["hits"] += 1
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            except Exception as e:
                logger.warning(f"Failed to load cache file {cache_file}: {e}")
                cache_file.unlink(missing_ok=True)
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, content: str, processing_params: Dict[str, Any], result: Any):
        """Cache result"""
        cache_key = self._get_cache_key(content, processing_params)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            logger.debug(f"Cached result for key: {cache_key}")
            
            # Check cache size and cleanup if necessary
            self._check_cache_size()
            
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    def _check_cache_size(self):
        """Check cache size and cleanup if necessary"""
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > self.max_cache_size_mb:
            logger.info(f"Cache size ({total_size_mb:.1f}MB) exceeds limit, cleaning up...")
            self._cleanup_old_cache(keep_recent=True)
    
    def _cleanup_old_cache(self, keep_recent: bool = False):
        """Clean up old cache files"""
        cache_files = list(self.cache_dir.glob("*.pkl"))
        
        if keep_recent and len(cache_files) > 100:
            # Sort by modification time and keep only recent files
            cache_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            files_to_remove = cache_files[100:]  # Keep 100 most recent
        else:
            files_to_remove = cache_files
        
        for cache_file in files_to_remove:
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove cache file {cache_file}: {e}")
        
        if files_to_remove:
            logger.info(f"Removed {len(files_to_remove)} cache files")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / total_requests if total_requests > 0 else 0
        
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "hit_rate": hit_rate,
            "total_files": len(cache_files),
            "total_size_mb": total_size / (1024 * 1024)
        }


def cached_processing(cache_manager: CacheManager):
    """Decorator for caching processing results"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(content: str, **kwargs):
            # Try to get from cache
            cached_result = cache_manager.get(content, kwargs)
            if cached_result is not None:
                return cached_result
            
            # Process and cache result
            result = func(content, **kwargs)
            cache_manager.set(content, kwargs, result)
            return result
        
        return wrapper
    return decorator


class BatchProcessor:
    """Batch processing system for large content"""
    
    def __init__(self, batch_size: int = 1000, max_workers: int = None):
        self.batch_size = batch_size
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.cache_manager = CacheManager()
    
    def process_large_content(self, content: str, processor_func: Callable,
                            chunk_overlap: int = 100) -> List[Dict[str, Any]]:
        """Process large content in chunks with overlap"""
        if len(content) <= self.batch_size:
            return processor_func(content)
        
        # Split content into overlapping chunks
        chunks = self._create_overlapping_chunks(content, chunk_overlap)
        
        # Process chunks in parallel
        all_results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._process_chunk, chunk, processor_func): i
                for i, chunk in enumerate(chunks)
            }
            
            for future in as_completed(future_to_chunk):
                chunk_idx = future_to_chunk[future]
                try:
                    result = future.result()
                    all_results.extend(result)
                    logger.debug(f"Processed chunk {chunk_idx + 1}/{len(chunks)}")
                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk_idx}: {e}")
        
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
    """Memory optimization utilities"""
    
    def __init__(self, memory_threshold_mb: int = 1000):
        self.memory_threshold_mb = memory_threshold_mb
        self.initial_memory = self._get_memory_usage()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    
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
                 max_workers: int = None, memory_threshold_mb: int = 1000):
        self.cache_manager = CacheManager(cache_dir)
        self.batch_processor = BatchProcessor(batch_size, max_workers)
        self.memory_optimizer = MemoryOptimizer(memory_threshold_mb)
    
    def process_content_optimized(self, content: str, processor_func: Callable,
                                processing_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process content with full optimization"""
        if processing_params is None:
            processing_params = {}
        
        # Check cache first
        cached_result = self.cache_manager.get(content, processing_params)
        if cached_result is not None:
            logger.info("Using cached result")
            return cached_result
        
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
            
            # Cache result
            result_data = {
                "cards": results,
                "processing_time": time.time() - progress.start_time,
                "memory_info": memory_info,
                "cache_stats": self.cache_manager.get_stats()
            }
            
            self.cache_manager.set(content, processing_params, result_data)
            
            # Finish progress tracking
            metrics = progress.finish()
            result_data["performance_metrics"] = metrics
            
            return result_data
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "cache_stats": self.cache_manager.get_stats(),
            "memory_info": self.memory_optimizer.check_memory_usage(),
            "batch_size": self.batch_processor.batch_size,
            "max_workers": self.batch_processor.max_workers
        }


# Factory function
def create_optimized_processor(**kwargs) -> PerformanceOptimizedProcessor:
    """Create a performance-optimized processor"""
    return PerformanceOptimizedProcessor(**kwargs)
