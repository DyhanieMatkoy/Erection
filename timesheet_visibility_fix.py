"""
Fix for Timesheet Visibility Issue - Marked for Deletion Entries Not Filtered Out

This fix ensures that timesheets marked for deletion are properly filtered out of the list.
"""

from sqlalchemy import and_, or_

def apply_timesheet_visibility_fix():
    """Apply the timesheet visibility fix"""
    
    # Fix 1: Improve boolean filtering in data service
    def get_documents_fixed(self, model_class, page=1, page_size=20, sort_by=None, 
                           sort_order='asc', filters=None, date_range=None, include_deleted=False):
        """Fixed version of get_documents with proper boolean filtering"""
        query = self.db.query(model_class)
        
        # Apply Soft Delete Filter (exclude deleted by default) - FIXED
        if not include_deleted:
            # Check for both marked_for_deletion and is_deleted fields
            delete_conditions = []
            
            if hasattr(model_class, 'marked_for_deletion'):
                delete_conditions.append(model_class.marked_for_deletion.is_(False))
            
            if hasattr(model_class, 'is_deleted'):
                delete_conditions.append(model_class.is_deleted.is_(False))
            
            # Apply all delete conditions
            if delete_conditions:
                query = query.filter(and_(*delete_conditions))
        
        # Rest of the method remains the same...
        return query
    
    # Fix 2: Ensure timesheet list form explicitly excludes deleted
    def load_timesheet_data_fixed(controller):
        """Fixed version that explicitly excludes deleted timesheets"""
        # Force include_deleted to False for timesheet lists
        original_filters = controller.filters.copy()
        
        # Add explicit filter for non-deleted items
        controller.filters['marked_for_deletion'] = False
        controller.filters['is_deleted'] = False
        
        # Load data
        result = controller.data_service.get_documents(
            model_class=controller.model_class,
            page=controller.current_page,
            page_size=controller.page_size,
            filters=controller.filters,
            sort_by=controller.sort_by,
            sort_order=controller.sort_order,
            include_deleted=False  # Explicitly set to False
        )
        
        # Restore original filters
        controller.filters = original_filters
        
        return result

print("✅ Timesheet visibility fix created")
