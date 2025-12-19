"""
Hierarchical Query Service

This service provides optimized queries for hierarchical work datasets,
implementing efficient recursive queries and pagination for large datasets.
Implements requirement 2.5 for hierarchical query optimization.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func, case
import logging

from ..data.models.sqlalchemy_models import Work, Unit
from ..data.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class HierarchicalQueryService:
    """Service for optimized hierarchical work queries"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def get_work_hierarchy_tree(
        self, 
        root_id: Optional[int] = None,
        max_depth: int = 10,
        include_unit_info: bool = True,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Get hierarchical work tree with optimized recursive query
        
        Args:
            root_id: Root work ID (None for all root works)
            max_depth: Maximum depth to traverse
            include_unit_info: Whether to include unit information
            include_deleted: Whether to include deleted works
            page: Page number for pagination
            page_size: Number of records per page
            
        Returns:
            Dict with hierarchical work data and pagination info
            
        Validates: Requirement 2.5 - Efficient hierarchical queries
        """
        try:
            with self.db_manager.get_session() as session:
                # Use database-specific recursive CTE for optimal performance
                if self.db_manager.get_database_type() == 'postgresql':
                    return self._get_hierarchy_postgresql(
                        session, root_id, max_depth, include_unit_info, 
                        include_deleted, page, page_size
                    )
                elif self.db_manager.get_database_type() == 'mssql':
                    return self._get_hierarchy_mssql(
                        session, root_id, max_depth, include_unit_info, 
                        include_deleted, page, page_size
                    )
                else:
                    # SQLite fallback - use iterative approach
                    return self._get_hierarchy_sqlite(
                        session, root_id, max_depth, include_unit_info, 
                        include_deleted, page, page_size
                    )
                    
        except Exception as e:
            logger.error(f"Failed to get work hierarchy: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_items': 0,
                    'total_pages': 0
                }
            }
    
    def _get_hierarchy_postgresql(
        self, 
        session: Session, 
        root_id: Optional[int], 
        max_depth: int,
        include_unit_info: bool, 
        include_deleted: bool, 
        page: int, 
        page_size: int
    ) -> Dict[str, Any]:
        """PostgreSQL-optimized recursive CTE query"""
        
        # Build the recursive CTE query
        deleted_condition = "" if include_deleted else "AND w.marked_for_deletion = false"
        unit_join = "LEFT JOIN units u ON w.unit_id = u.id" if include_unit_info else ""
        unit_fields = ", u.name as unit_name, u.description as unit_description" if include_unit_info else ""
        
        root_condition = f"w.parent_id = {root_id}" if root_id else "w.parent_id IS NULL"
        
        query = f"""
        WITH RECURSIVE work_hierarchy AS (
            -- Base case: root works
            SELECT 
                w.id, w.name, w.code, w.unit_id, w.price, w.labor_rate,
                w.is_group, w.parent_id, w.marked_for_deletion, w.uuid,
                COALESCE(u.name, w.unit) as unit_display
                {unit_fields},
                0 as level,
                ARRAY[w.id] as path,
                w.name as hierarchy_path
            FROM works w
            {unit_join}
            WHERE {root_condition} {deleted_condition}
            
            UNION ALL
            
            -- Recursive case: children
            SELECT 
                w.id, w.name, w.code, w.unit_id, w.price, w.labor_rate,
                w.is_group, w.parent_id, w.marked_for_deletion, w.uuid,
                COALESCE(u.name, w.unit) as unit_display
                {unit_fields},
                wh.level + 1,
                wh.path || w.id,
                wh.hierarchy_path || ' > ' || w.name
            FROM works w
            {unit_join}
            JOIN work_hierarchy wh ON w.parent_id = wh.id
            WHERE wh.level < {max_depth} {deleted_condition}
        )
        SELECT * FROM work_hierarchy
        ORDER BY path
        LIMIT {page_size} OFFSET {(page - 1) * page_size}
        """
        
        # Execute query
        result = session.execute(text(query))
        works = [dict(row._mapping) for row in result]
        
        # Get total count for pagination
        count_query = f"""
        WITH RECURSIVE work_hierarchy AS (
            SELECT w.id, w.parent_id, 0 as level, ARRAY[w.id] as path
            FROM works w
            WHERE {root_condition} {deleted_condition}
            
            UNION ALL
            
            SELECT w.id, w.parent_id, wh.level + 1, wh.path || w.id
            FROM works w
            JOIN work_hierarchy wh ON w.parent_id = wh.id
            WHERE wh.level < {max_depth} {deleted_condition}
        )
        SELECT COUNT(*) as total FROM work_hierarchy
        """
        
        total_result = session.execute(text(count_query))
        total_items = total_result.fetchone()[0]
        
        return {
            'success': True,
            'data': works,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': (total_items + page_size - 1) // page_size
            }
        }
    
    def _get_hierarchy_mssql(
        self, 
        session: Session, 
        root_id: Optional[int], 
        max_depth: int,
        include_unit_info: bool, 
        include_deleted: bool, 
        page: int, 
        page_size: int
    ) -> Dict[str, Any]:
        """SQL Server-optimized recursive CTE query"""
        
        deleted_condition = "" if include_deleted else "AND w.marked_for_deletion = 0"
        unit_join = "LEFT JOIN units u ON w.unit_id = u.id" if include_unit_info else ""
        unit_fields = ", u.name as unit_name, u.description as unit_description" if include_unit_info else ""
        
        root_condition = f"w.parent_id = {root_id}" if root_id else "w.parent_id IS NULL"
        
        query = f"""
        WITH work_hierarchy AS (
            -- Base case: root works
            SELECT 
                w.id, w.name, w.code, w.unit_id, w.price, w.labor_rate,
                w.is_group, w.parent_id, w.marked_for_deletion, w.uuid,
                COALESCE(u.name, w.unit) as unit_display
                {unit_fields},
                0 as level,
                CAST(w.id AS VARCHAR(MAX)) as path,
                w.name as hierarchy_path
            FROM works w
            {unit_join}
            WHERE {root_condition} {deleted_condition}
            
            UNION ALL
            
            -- Recursive case: children
            SELECT 
                w.id, w.name, w.code, w.unit_id, w.price, w.labor_rate,
                w.is_group, w.parent_id, w.marked_for_deletion, w.uuid,
                COALESCE(u.name, w.unit) as unit_display
                {unit_fields},
                wh.level + 1,
                wh.path + ',' + CAST(w.id AS VARCHAR(MAX)),
                wh.hierarchy_path + ' > ' + w.name
            FROM works w
            {unit_join}
            JOIN work_hierarchy wh ON w.parent_id = wh.id
            WHERE wh.level < {max_depth} {deleted_condition}
        )
        SELECT * FROM work_hierarchy
        ORDER BY path
        OFFSET {(page - 1) * page_size} ROWS
        FETCH NEXT {page_size} ROWS ONLY
        """
        
        # Execute query
        result = session.execute(text(query))
        works = [dict(row._mapping) for row in result]
        
        # Get total count
        count_query = f"""
        WITH work_hierarchy AS (
            SELECT w.id, w.parent_id, 0 as level
            FROM works w
            WHERE {root_condition} {deleted_condition}
            
            UNION ALL
            
            SELECT w.id, w.parent_id, wh.level + 1
            FROM works w
            JOIN work_hierarchy wh ON w.parent_id = wh.id
            WHERE wh.level < {max_depth} {deleted_condition}
        )
        SELECT COUNT(*) as total FROM work_hierarchy
        """
        
        total_result = session.execute(text(count_query))
        total_items = total_result.fetchone()[0]
        
        return {
            'success': True,
            'data': works,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': (total_items + page_size - 1) // page_size
            }
        }
    
    def _get_hierarchy_sqlite(
        self, 
        session: Session, 
        root_id: Optional[int], 
        max_depth: int,
        include_unit_info: bool, 
        include_deleted: bool, 
        page: int, 
        page_size: int
    ) -> Dict[str, Any]:
        """SQLite fallback using iterative approach"""
        
        works = []
        processed_ids = set()
        
        # Start with root works
        if root_id:
            root_works = session.query(Work).filter(
                and_(
                    Work.parent_id == root_id,
                    Work.marked_for_deletion == (False if not include_deleted else or_(True, False))
                )
            ).all()
        else:
            root_works = session.query(Work).filter(
                and_(
                    Work.parent_id.is_(None),
                    Work.marked_for_deletion == (False if not include_deleted else or_(True, False))
                )
            ).all()
        
        # Process hierarchy level by level
        current_level = root_works
        level = 0
        
        while current_level and level < max_depth:
            for work in current_level:
                if work.id not in processed_ids:
                    work_data = self._work_to_dict(work, level, include_unit_info)
                    works.append(work_data)
                    processed_ids.add(work.id)
            
            # Get next level
            if level < max_depth - 1:
                parent_ids = [work.id for work in current_level]
                current_level = session.query(Work).filter(
                    and_(
                        Work.parent_id.in_(parent_ids),
                        Work.marked_for_deletion == (False if not include_deleted else or_(True, False))
                    )
                ).all()
            else:
                current_level = []
            
            level += 1
        
        # Apply pagination
        total_items = len(works)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_works = works[start_idx:end_idx]
        
        return {
            'success': True,
            'data': paginated_works,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': (total_items + page_size - 1) // page_size
            }
        }
    
    def _work_to_dict(self, work: Work, level: int, include_unit_info: bool) -> Dict[str, Any]:
        """Convert Work object to dictionary with hierarchy info"""
        work_dict = {
            'id': work.id,
            'name': work.name,
            'code': work.code,
            'unit_id': work.unit_id,
            'price': work.price,
            'labor_rate': work.labor_rate,
            'is_group': work.is_group,
            'parent_id': work.parent_id,
            'marked_for_deletion': work.marked_for_deletion,
            'uuid': work.uuid,
            'level': level,
            'unit_display': work.effective_unit_name
        }
        
        if include_unit_info and work.unit_ref:
            work_dict.update({
                'unit_name': work.unit_ref.name,
                'unit_description': work.unit_ref.description
            })
        
        return work_dict
    
    def get_work_ancestors(self, work_id: int, include_self: bool = True) -> List[Dict[str, Any]]:
        """
        Get all ancestors of a work in hierarchical order
        
        Args:
            work_id: Work ID to get ancestors for
            include_self: Whether to include the work itself
            
        Returns:
            List of ancestor works from root to work (or parent)
        """
        ancestors = []
        
        try:
            with self.db_manager.get_session() as session:
                current_id = work_id
                visited = set()
                
                while current_id and current_id not in visited:
                    visited.add(current_id)
                    
                    work = session.query(Work).filter(Work.id == current_id).first()
                    if not work:
                        break
                    
                    if current_id == work_id and not include_self:
                        current_id = work.parent_id
                        continue
                    
                    work_data = self._work_to_dict(work, 0, True)
                    ancestors.insert(0, work_data)  # Insert at beginning for correct order
                    
                    current_id = work.parent_id
                
        except Exception as e:
            logger.error(f"Failed to get work ancestors for {work_id}: {str(e)}")
        
        return ancestors
    
    def get_work_descendants(
        self, 
        work_id: int, 
        max_depth: int = 10,
        include_deleted: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all descendants of a work
        
        Args:
            work_id: Work ID to get descendants for
            max_depth: Maximum depth to traverse
            include_deleted: Whether to include deleted works
            
        Returns:
            List of descendant works
        """
        descendants = []
        
        try:
            with self.db_manager.get_session() as session:
                # Use recursive approach for all database types
                to_process = [(work_id, 0)]
                processed = set()
                
                while to_process:
                    current_id, level = to_process.pop(0)
                    
                    if current_id in processed or level >= max_depth:
                        continue
                    
                    processed.add(current_id)
                    
                    # Get children
                    children_query = session.query(Work).filter(Work.parent_id == current_id)
                    if not include_deleted:
                        children_query = children_query.filter(Work.marked_for_deletion == False)
                    
                    children = children_query.all()
                    
                    for child in children:
                        child_data = self._work_to_dict(child, level + 1, True)
                        descendants.append(child_data)
                        
                        # Add to processing queue for next level
                        to_process.append((child.id, level + 1))
                
        except Exception as e:
            logger.error(f"Failed to get work descendants for {work_id}: {str(e)}")
        
        return descendants
    
    def get_hierarchy_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the work hierarchy
        
        Returns:
            Dict with hierarchy statistics
        """
        stats = {
            'total_works': 0,
            'root_works': 0,
            'max_depth': 0,
            'avg_children_per_parent': 0.0,
            'works_by_level': {},
            'orphaned_works': 0
        }
        
        try:
            with self.db_manager.get_session() as session:
                # Total works
                stats['total_works'] = session.query(Work).filter(
                    Work.marked_for_deletion == False
                ).count()
                
                # Root works (no parent)
                stats['root_works'] = session.query(Work).filter(
                    and_(Work.parent_id.is_(None), Work.marked_for_deletion == False)
                ).count()
                
                # Works with invalid parent references (orphaned)
                orphaned_query = session.execute(text("""
                    SELECT COUNT(*) as count
                    FROM works w
                    LEFT JOIN works p ON w.parent_id = p.id
                    WHERE w.parent_id IS NOT NULL 
                    AND (p.id IS NULL OR p.marked_for_deletion = 1)
                    AND w.marked_for_deletion = 0
                """))
                stats['orphaned_works'] = orphaned_query.fetchone()[0]
                
                # Average children per parent
                children_query = session.execute(text("""
                    SELECT AVG(child_count) as avg_children
                    FROM (
                        SELECT COUNT(*) as child_count
                        FROM works
                        WHERE parent_id IS NOT NULL AND marked_for_deletion = 0
                        GROUP BY parent_id
                    ) subq
                """))
                result = children_query.fetchone()
                stats['avg_children_per_parent'] = float(result[0]) if result[0] else 0.0
                
                # Calculate max depth and works by level (simplified for performance)
                # This is an approximation - for exact calculation, we'd need recursive queries
                max_depth_query = session.execute(text("""
                    SELECT MAX(level_count) as max_depth
                    FROM (
                        SELECT COUNT(*) as level_count
                        FROM works w1
                        JOIN works w2 ON w1.parent_id = w2.id
                        JOIN works w3 ON w2.parent_id = w3.id
                        WHERE w1.marked_for_deletion = 0
                        GROUP BY w1.id
                        LIMIT 1000
                    ) subq
                """))
                result = max_depth_query.fetchone()
                stats['max_depth'] = result[0] if result and result[0] else 0
                
        except Exception as e:
            logger.error(f"Failed to get hierarchy statistics: {str(e)}")
            stats['error'] = str(e)
        
        return stats
    
    def optimize_hierarchy_performance(self) -> Dict[str, Any]:
        """
        Analyze and suggest optimizations for hierarchy performance
        
        Returns:
            Dict with optimization suggestions
        """
        suggestions = {
            'index_recommendations': [],
            'query_optimizations': [],
            'data_issues': [],
            'performance_metrics': {}
        }
        
        try:
            with self.db_manager.get_session() as session:
                # Check for missing indexes
                db_type = self.db_manager.get_database_type()
                
                if db_type in ['postgresql', 'mssql']:
                    # Check if indexes exist
                    if db_type == 'postgresql':
                        index_check = session.execute(text("""
                            SELECT indexname FROM pg_indexes 
                            WHERE tablename = 'works' 
                            AND indexname IN ('idx_works_parent_id', 'idx_works_unit_id')
                        """))
                    else:  # mssql
                        index_check = session.execute(text("""
                            SELECT name FROM sys.indexes 
                            WHERE object_id = OBJECT_ID('works')
                            AND name IN ('idx_works_parent_id', 'idx_works_unit_id')
                        """))
                    
                    existing_indexes = [row[0] for row in index_check]
                    
                    if 'idx_works_parent_id' not in existing_indexes:
                        suggestions['index_recommendations'].append(
                            "Create index on parent_id for faster hierarchy traversal"
                        )
                    
                    if 'idx_works_unit_id' not in existing_indexes:
                        suggestions['index_recommendations'].append(
                            "Create index on unit_id for faster unit lookups"
                        )
                
                # Check for data issues
                stats = self.get_hierarchy_statistics()
                
                if stats.get('orphaned_works', 0) > 0:
                    suggestions['data_issues'].append(
                        f"Found {stats['orphaned_works']} orphaned works with invalid parent references"
                    )
                
                if stats.get('max_depth', 0) > 10:
                    suggestions['query_optimizations'].append(
                        "Consider limiting hierarchy depth in queries for better performance"
                    )
                
                # Performance metrics
                suggestions['performance_metrics'] = {
                    'total_works': stats.get('total_works', 0),
                    'hierarchy_depth': stats.get('max_depth', 0),
                    'avg_children': stats.get('avg_children_per_parent', 0),
                    'orphaned_works': stats.get('orphaned_works', 0)
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze hierarchy performance: {str(e)}")
            suggestions['error'] = str(e)
        
        return suggestions