import sys
import unittest
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QCoreApplication
from src.services.bulk_operation_service import BulkOperationService

# Create QApplication instance if it doesn't exist
app = QApplication.instance() or QApplication(sys.argv)

class TestBulkOperationService(unittest.TestCase):
    def setUp(self):
        self.service = BulkOperationService()
        self.received_signals = []
        
        # Connect signals
        self.service.operation_started.connect(lambda op_id, name, total: self.received_signals.append(('started', name, total)))
        self.service.progress_updated.connect(lambda op_id, name, curr, total: self.received_signals.append(('progress', name, curr, total)))
        self.service.operation_completed.connect(lambda op_id, name, res: self.received_signals.append(('completed', name, res)))
        
    def tearDown(self):
        # Wait for threads to finish if any (to avoid segfaults)
        self.service.thread_pool.waitForDone(1000)

    def test_successful_operation(self):
        """Test a successful bulk operation"""
        items = [1, 2, 3]
        
        def handler(item):
            return {'success': True}
            
        self.service.execute_operation("TestOp", items, handler)
        
        # Wait for completion
        start_time = time.time()
        while not any(s[0] == 'completed' for s in self.received_signals):
            app.processEvents()
            time.sleep(0.01)
            if time.time() - start_time > 2:
                self.fail("Operation timed out")
                
        # Verify signals
        started = next(s for s in self.received_signals if s[0] == 'started')
        self.assertEqual(started[1], "TestOp")
        self.assertEqual(started[2], 3)
        
        completed = next(s for s in self.received_signals if s[0] == 'completed')
        results = completed[2]
        self.assertEqual(results['success_count'], 3)
        self.assertEqual(results['failure_count'], 0)
        self.assertEqual(len(results['details']), 3)

    def test_failed_operation(self):
        """Test an operation with failures"""
        items = [1, 2, 3]
        
        def handler(item):
            if item == 2:
                return {'success': False, 'error': 'Failed'}
            return {'success': True}
            
        self.service.execute_operation("FailOp", items, handler)
        
        # Wait for completion
        start_time = time.time()
        while not any(s[0] == 'completed' for s in self.received_signals):
            app.processEvents()
            time.sleep(0.01)
            if time.time() - start_time > 2:
                self.fail("Operation timed out")
                
        completed = next(s for s in self.received_signals if s[0] == 'completed')
        results = completed[2]
        self.assertEqual(results['success_count'], 2)
        self.assertEqual(results['failure_count'], 1)
        self.assertEqual(len(results['errors']), 1)

    def test_cancellation(self):
        """Test operation cancellation"""
        items = range(100)
        
        def handler(item):
            time.sleep(0.01) # Slow down
            return {'success': True}
            
        op_id = self.service.execute_operation("CancelOp", items, handler)
        
        # Let it start
        time.sleep(0.05)
        app.processEvents()
        
        # Cancel
        self.service.cancel_operation(op_id)
        
        # Wait for completion
        start_time = time.time()
        while not any(s[0] == 'completed' for s in self.received_signals):
            app.processEvents()
            time.sleep(0.01)
            if time.time() - start_time > 2:
                self.fail("Operation timed out")
                
        completed = next(s for s in self.received_signals if s[0] == 'completed')
        results = completed[2]
        
        self.assertTrue(results['is_cancelled'])
        self.assertLess(results['success_count'], 100)
        
if __name__ == '__main__':
    unittest.main()
