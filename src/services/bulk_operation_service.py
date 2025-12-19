from typing import List, Any, Callable, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
import logging
import traceback

logger = logging.getLogger(__name__)

class BulkOperationWorker(QRunnable):
    """
    Worker for executing bulk operations in a background thread.
    """
    def __init__(self, 
                 operation_name: str, 
                 items: List[Any], 
                 handler: Callable[[Any], Dict[str, Any]], 
                 progress_callback: Callable[[int, int], None],
                 result_callback: Callable[[Dict[str, Any]], None],
                 check_cancel_callback: Callable[[], bool]):
        super().__init__()
        self.operation_name = operation_name
        self.items = items
        self.handler = handler
        self.progress_callback = progress_callback
        self.result_callback = result_callback
        self.check_cancel_callback = check_cancel_callback
        self.is_cancelled = False

    def run(self):
        results = {
            'success_count': 0,
            'failure_count': 0,
            'errors': [],
            'details': []
        }
        
        total = len(self.items)
        
        try:
            for i, item in enumerate(self.items):
                # Check cancellation
                if self.check_cancel_callback():
                    self.is_cancelled = True
                    break
                
                # Report progress
                # We report progress BEFORE processing the item, or after?
                # Usually 0/total, then 1/total...
                if self.progress_callback:
                    self.progress_callback(i, total)
                
                # Execute handler
                try:
                    result = self.handler(item)
                    
                    if result.get('success', True):
                        results['success_count'] += 1
                        results['details'].append({'item': item, 'success': True, 'result': result})
                    else:
                        results['failure_count'] += 1
                        error_msg = result.get('error', 'Unknown error')
                        results['errors'].append(f"Item {item}: {error_msg}")
                        results['details'].append({'item': item, 'success': False, 'error': error_msg})
                        
                except Exception as e:
                    results['failure_count'] += 1
                    error_msg = str(e)
                    results['errors'].append(f"Item {item}: {error_msg}")
                    results['details'].append({'item': item, 'success': False, 'error': error_msg})
                    logger.error(f"Error processing item {item} in {self.operation_name}: {e}")
            
            # Final progress
            if self.progress_callback:
                self.progress_callback(total, total)
                
        except Exception as e:
            logger.error(f"Critical error in bulk operation {self.operation_name}: {e}")
            logger.error(traceback.format_exc())
            results['critical_error'] = str(e)
            
        finally:
            results['is_cancelled'] = self.is_cancelled
            if self.result_callback:
                self.result_callback(results)


class BulkOperationService(QObject):
    """
    Service for managing bulk operations.
    Supports queuing, execution, progress tracking, and cancellation.
    (Task 12.1)
    """
    
    # Signals
    operation_started = pyqtSignal(str, str, int) # operation_id, operation_name, total_items
    progress_updated = pyqtSignal(str, str, int, int) # operation_id, operation_name, current, total
    operation_completed = pyqtSignal(str, str, dict) # operation_id, operation_name, results
    operation_failed = pyqtSignal(str, str, str) # operation_id, operation_name, error_message
    
    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        self._cancel_flags = {} # operation_id -> bool
        self._active_operations = {} # operation_id -> info
        
    def execute_operation(self, 
                          operation_name: str, 
                          items: List[Any], 
                          handler: Callable[[Any], Dict[str, Any]],
                          operation_id: str = None) -> str:
        """
        Start a bulk operation.
        
        Args:
            operation_name: Display name of the operation
            items: List of items to process (usually IDs or objects)
            handler: Function that takes an item and returns dict with 'success' and optional 'error'
            operation_id: Optional unique ID, generated if not provided
            
        Returns:
            operation_id
        """
        if not operation_id:
            import uuid
            operation_id = str(uuid.uuid4())
            
        if not items:
            # Nothing to do
            self.operation_completed.emit(operation_id, operation_name, {'success_count': 0, 'failure_count': 0, 'errors': []})
            return operation_id
            
        self._cancel_flags[operation_id] = False
        self._active_operations[operation_id] = {
            'name': operation_name,
            'total': len(items)
        }
        
        # Define callbacks
        def progress_cb(current, total):
            # We emit signal from the worker thread. 
            # Signals are thread-safe in PyQt if connected correctly (AutoConnection).
            self.progress_updated.emit(operation_id, operation_name, current, total)
            
        def result_cb(results):
            # Cleanup
            if operation_id in self._cancel_flags:
                del self._cancel_flags[operation_id]
            if operation_id in self._active_operations:
                del self._active_operations[operation_id]
                
            self.operation_completed.emit(operation_id, operation_name, results)
            
        def check_cancel_cb():
            return self._cancel_flags.get(operation_id, False)
            
        # Create and start worker
        worker = BulkOperationWorker(
            operation_name,
            items,
            handler,
            progress_cb,
            result_cb,
            check_cancel_cb
        )
        
        self.operation_started.emit(operation_id, operation_name, len(items))
        self.thread_pool.start(worker)
        
        return operation_id
        
    def cancel_operation(self, operation_id: str):
        """Request cancellation of an operation"""
        if operation_id in self._cancel_flags:
            self._cancel_flags[operation_id] = True
            
    def is_busy(self) -> bool:
        """Check if any operations are running"""
        return self.thread_pool.activeThreadCount() > 0
