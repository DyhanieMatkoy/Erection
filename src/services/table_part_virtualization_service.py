"""
Table Part Virtualization Service

Provides virtual scrolling and lazy loading for large datasets in table parts.
Optimizes memory usage and rendering performance for tables with 1000+ rows.
"""

from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QTableWidget, QAbstractItemView
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class VirtualizationOptions:
    """Configuration for table virtualization"""
    row_height: int = 30
    buffer_size: int = 10
    page_size: int = 100
    preload_pages: int = 2
    cache_size: int = 10
    enable_prefetch: bool = True
    enable_column_virtualization: bool = False


@dataclass
class PerformanceMetrics:
    """Performance metrics for virtualization"""
    render_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    rendered_rows: int = 0
    total_rows: int = 0
    cache_hit_rate: float = 0.0
    average_load_time_ms: float = 0.0


@dataclass
class DataPage:
    """Represents a page of data"""
    page_number: int
    data: List[Dict[str, Any]]
    is_loading: bool = False
    is_loaded: bool = False
    error: Optional[str] = None
    timestamp: float = 0.0


class TablePartVirtualizationService(QObject):
    """
    Service for virtualizing table part data to handle large datasets efficiently.
    
    Features:
    - Virtual scrolling: Only renders visible rows
    - Lazy loading: Loads data in pages as needed
    - Memory management: Caches limited number of pages
    - Prefetching: Preloads adjacent pages for smooth scrolling
    """
    
    # Signals
    dataLoaded = pyqtSignal(int, list)  # page_number, data
    loadingStateChanged = pyqtSignal(bool)  # is_loading
    errorOccurred = pyqtSignal(str)  # error_message
    metricsUpdated = pyqtSignal(object)  # PerformanceMetrics
    
    def __init__(
        self,
        table_widget: QTableWidget,
        load_data_fn: Callable[[int, int], Tuple[List[Dict[str, Any]], int]],
        options: Optional[VirtualizationOptions] = None
    ):
        super().__init__()
        
        self.table = table_widget
        self.load_data_fn = load_data_fn
        self.options = options or VirtualizationOptions()
        
        # Data storage
        self.pages: Dict[int, DataPage] = {}
        self.total_count: Optional[int] = None
        self.current_page = 0
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.total_load_time = 0.0
        self.total_requests = 0
        self.cache_hits = 0
        
        # Timers for debouncing
        self.prefetch_timer = QTimer()
        self.prefetch_timer.setSingleShot(True)
        self.prefetch_timer.timeout.connect(self._do_prefetch)
        self.pending_prefetch_page: Optional[int] = None
        
        # Setup table
        self._setup_table()
    
    def _setup_table(self):
        """Configure table widget for virtualization"""
        # Enable smooth scrolling
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        
        # Set uniform row heights for better performance
        self.table.verticalHeader().setDefaultSectionSize(self.options.row_height)
        self.table.verticalHeader().setSectionResizeMode(
            self.table.verticalHeader().ResizeMode.Fixed
        )
        
        # Connect scroll events
        self.table.verticalScrollBar().valueChanged.connect(self._on_scroll)
    
    def _on_scroll(self, value: int):
        """Handle scroll events to load visible data"""
        visible_range = self._get_visible_range()
        self._load_visible_range(visible_range[0], visible_range[1])
    
    def _get_visible_range(self) -> Tuple[int, int]:
        """Calculate the range of visible rows"""
        scroll_value = self.table.verticalScrollBar().value()
        viewport_height = self.table.viewport().height()
        
        start_row = max(0, scroll_value // self.options.row_height - self.options.buffer_size)
        visible_rows = (viewport_height // self.options.row_height) + 1
        end_row = start_row + visible_rows + (2 * self.options.buffer_size)
        
        if self.total_count is not None:
            end_row = min(end_row, self.total_count)
        
        return start_row, end_row
    
    def _load_visible_range(self, start_row: int, end_row: int):
        """Load data for visible range"""
        start_page = start_row // self.options.page_size
        end_page = end_row // self.options.page_size
        
        # Load current visible pages
        for page_num in range(start_page, end_page + 1):
            if not self._is_page_loaded(page_num):
                self._load_page(page_num)
        
        # Prefetch adjacent pages if enabled
        if self.options.enable_prefetch:
            preload_start = max(0, start_page - self.options.preload_pages)
            preload_end = end_page + self.options.preload_pages
            
            for page_num in range(preload_start, preload_end + 1):
                if page_num < start_page or page_num > end_page:
                    self._schedule_prefetch(page_num)
    
    def _is_page_loaded(self, page_number: int) -> bool:
        """Check if a page is already loaded"""
        page = self.pages.get(page_number)
        return page is not None and page.is_loaded
    
    def _load_page(self, page_number: int):
        """Load a specific page of data"""
        # Check if already loading or loaded
        existing_page = self.pages.get(page_number)
        if existing_page:
            if existing_page.is_loaded:
                self.cache_hits += 1
                self._update_metrics()
                return
            if existing_page.is_loading:
                return
        
        # Create loading page entry
        loading_page = DataPage(
            page_number=page_number,
            data=[],
            is_loading=True,
            timestamp=time.time()
        )
        self.pages[page_number] = loading_page
        
        self.loadingStateChanged.emit(True)
        self.total_requests += 1
        
        try:
            start_time = time.time()
            
            # Load data using provided function
            data, total_count = self.load_data_fn(page_number, self.options.page_size)
            
            load_time = (time.time() - start_time) * 1000  # Convert to ms
            self.total_load_time += load_time
            
            # Update page with loaded data
            loaded_page = DataPage(
                page_number=page_number,
                data=data,
                is_loading=False,
                is_loaded=True,
                timestamp=time.time()
            )
            self.pages[page_number] = loaded_page
            
            # Update total count
            if total_count is not None:
                self.total_count = total_count
            
            # Emit signals
            self.dataLoaded.emit(page_number, data)
            
            # Update table display
            self._update_table_display()
            
            # Cleanup old pages if cache is full
            self._cleanup_cache()
            
            # Update metrics
            self._update_metrics()
            
            logger.debug(f"Loaded page {page_number} with {len(data)} rows in {load_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to load page {page_number}: {e}")
            
            error_page = DataPage(
                page_number=page_number,
                data=[],
                is_loading=False,
                is_loaded=False,
                error=str(e),
                timestamp=time.time()
            )
            self.pages[page_number] = error_page
            
            self.errorOccurred.emit(str(e))
        
        finally:
            self.loadingStateChanged.emit(False)
    
    def _schedule_prefetch(self, page_number: int):
        """Schedule a page prefetch with debouncing"""
        if not self._is_page_loaded(page_number):
            self.pending_prefetch_page = page_number
            self.prefetch_timer.start(100)  # 100ms delay
    
    def _do_prefetch(self):
        """Execute pending prefetch"""
        if self.pending_prefetch_page is not None:
            self._load_page(self.pending_prefetch_page)
            self.pending_prefetch_page = None
    
    def _update_table_display(self):
        """Update table widget with loaded data"""
        start_time = time.time()
        
        # Get visible range
        start_row, end_row = self._get_visible_range()
        
        # Get data for visible range
        visible_data = self._get_data_range(start_row, end_row)
        
        # Update table rows
        # This should be implemented by subclasses based on their specific table structure
        # For now, we just track the render time
        
        render_time = (time.time() - start_time) * 1000
        self.metrics.render_time_ms = render_time
        self.metrics.rendered_rows = len(visible_data)
        
        if render_time > 16:  # More than one frame at 60fps
            logger.warning(f"Slow render detected: {render_time:.2f}ms")
    
    def _get_data_range(self, start_row: int, end_row: int) -> List[Dict[str, Any]]:
        """Get data for a specific range of rows"""
        result = []
        start_page = start_row // self.options.page_size
        end_page = end_row // self.options.page_size
        
        for page_num in range(start_page, end_page + 1):
            page = self.pages.get(page_num)
            if page and page.is_loaded:
                page_start_row = page_num * self.options.page_size
                page_end_row = page_start_row + len(page.data)
                
                # Calculate intersection with requested range
                range_start = max(start_row, page_start_row)
                range_end = min(end_row, page_end_row)
                
                if range_start < range_end:
                    local_start = range_start - page_start_row
                    local_end = range_end - page_start_row
                    result.extend(page.data[local_start:local_end])
        
        return result
    
    def _cleanup_cache(self):
        """Remove old pages to manage memory"""
        if len(self.pages) <= self.options.cache_size:
            return
        
        # Sort pages by timestamp (oldest first)
        sorted_pages = sorted(self.pages.items(), key=lambda x: x[1].timestamp)
        
        # Remove oldest pages
        pages_to_remove = len(self.pages) - self.options.cache_size
        for i in range(pages_to_remove):
            page_num, _ = sorted_pages[i]
            del self.pages[page_num]
            logger.debug(f"Removed page {page_num} from cache")
    
    def _update_metrics(self):
        """Update performance metrics"""
        self.metrics.total_rows = self.total_count or 0
        
        if self.total_requests > 0:
            self.metrics.average_load_time_ms = self.total_load_time / self.total_requests
            self.metrics.cache_hit_rate = self.cache_hits / self.total_requests
        
        # Estimate memory usage
        total_items = sum(len(page.data) for page in self.pages.values() if page.is_loaded)
        self.metrics.memory_usage_mb = (total_items * 1) / 1024  # Rough estimate: 1KB per item
        
        self.metricsUpdated.emit(self.metrics)
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """Get all loaded data"""
        result = []
        sorted_pages = sorted(self.pages.items(), key=lambda x: x[0])
        
        for _, page in sorted_pages:
            if page.is_loaded:
                result.extend(page.data)
        
        return result
    
    def is_range_loaded(self, start_row: int, end_row: int) -> bool:
        """Check if a range of rows is loaded"""
        start_page = start_row // self.options.page_size
        end_page = end_row // self.options.page_size
        
        for page_num in range(start_page, end_page + 1):
            if not self._is_page_loaded(page_num):
                return False
        
        return True
    
    def reset(self):
        """Reset all data and state"""
        self.pages.clear()
        self.total_count = None
        self.current_page = 0
        
        # Reset metrics
        self.metrics = PerformanceMetrics()
        self.total_load_time = 0.0
        self.total_requests = 0
        self.cache_hits = 0
        
        logger.info("Virtualization service reset")
    
    def refresh_page(self, page_number: int):
        """Refresh a specific page"""
        if page_number in self.pages:
            del self.pages[page_number]
        self._load_page(page_number)
    
    def refresh_all(self):
        """Refresh all loaded pages"""
        loaded_pages = [num for num, page in self.pages.items() if page.is_loaded]
        self.pages.clear()
        
        for page_num in loaded_pages:
            self._load_page(page_num)
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        return self.metrics
    
    def scroll_to_row(self, row_index: int):
        """Scroll to a specific row"""
        if self.total_count and row_index >= self.total_count:
            return
        
        scroll_value = row_index * self.options.row_height
        self.table.verticalScrollBar().setValue(scroll_value)
    
    def cleanup(self):
        """Cleanup resources"""
        self.prefetch_timer.stop()
        self.pages.clear()
        logger.info("Virtualization service cleaned up")


def create_virtualization_service(
    table_widget: QTableWidget,
    load_data_fn: Callable[[int, int], Tuple[List[Dict[str, Any]], int]],
    options: Optional[VirtualizationOptions] = None
) -> TablePartVirtualizationService:
    """Factory function to create a virtualization service"""
    return TablePartVirtualizationService(table_widget, load_data_fn, options)
