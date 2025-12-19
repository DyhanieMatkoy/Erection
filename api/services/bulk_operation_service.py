from typing import Dict, List, Type, Any, Optional
import logging
from api.models.bulk_operations import BulkOperationResult, BulkOperationRequest

logger = logging.getLogger(__name__)

class BulkOperationHandler:
    """Base class for bulk operation handlers"""
    
    async def execute(self, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        raise NotImplementedError("Subclasses must implement execute method")

class BulkOperationService:
    """Service for managing and executing bulk operations"""
    
    def __init__(self):
        self._handlers: Dict[str, BulkOperationHandler] = {}
        
    def register_handler(self, operation_type: str, handler: BulkOperationHandler):
        """Register a handler for a specific operation type"""
        self._handlers[operation_type] = handler
        logger.info(f"Registered handler for bulk operation: {operation_type}")
        
    def get_handler(self, operation_type: str) -> Optional[BulkOperationHandler]:
        """Get handler by operation type"""
        return self._handlers.get(operation_type)
        
    async def execute_operation(self, operation_type: str, ids: List[int], context: Dict[str, Any] = None) -> BulkOperationResult:
        """Execute a bulk operation"""
        handler = self.get_handler(operation_type)
        if not handler:
            return BulkOperationResult(
                success=False,
                message=f"No handler found for operation: {operation_type}",
                processed=0,
                errors=[f"Unknown operation type: {operation_type}"]
            )
            
        try:
            return await handler.execute(ids, context or {})
        except Exception as e:
            logger.error(f"Error executing bulk operation {operation_type}: {str(e)}", exc_info=True)
            return BulkOperationResult(
                success=False,
                message=f"Error executing operation: {str(e)}",
                processed=0,
                errors=[str(e)]
            )

# Global instance
bulk_operation_service = BulkOperationService()
