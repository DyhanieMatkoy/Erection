"""
Example demonstrating enhanced API pagination, sorting, and filtering
Shows Task 5: API pagination and sorting endpoints functionality
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqlite3
from datetime import date, timedelta
from unittest.mock import Mock

from api.services.pagination_service import PaginationService, PaginationConfig
from api.services.sorting_service import SortingService
from api.services.date_filter_service import DateFilterService


def create_test_database():
    """Create test database with sample data"""
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Create estimates table
    cursor.execute("""
        CREATE TABLE estimates (
            id INTEGER PRIMARY KEY,
            number TEXT,
            date TEXT,
            customer_id INTEGER,
            object_id INTEGER,
            contractor_id INTEGER,
            responsible_id INTEGER,
            total_sum REAL,
            total_labor REAL,
            estimate_type TEXT,
            marked_for_deletion INTEGER DEFAULT 0,
            created_at TEXT,
            modified_at TEXT
        )
    """)
    
    # Create reference tables
    cursor.execute("""
        CREATE TABLE counterparties (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE objects (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE organizations (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE persons (
            id INTEGER PRIMARY KEY,
            full_name TEXT
        )
    """)
    
    # Insert reference data
    cursor.execute("INSERT INTO counterparties (id, name) VALUES (1, 'ООО Строитель')")
    cursor.execute("INSERT INTO counterparties (id, name) VALUES (2, 'ЗАО Монтаж')")
    cursor.execute("INSERT INTO objects (id, name) VALUES (1, 'Жилой комплекс Солнечный')")
    cursor.execute("INSERT INTO objects (id, name) VALUES (2, 'Торговый центр Европа')")
    cursor.execute("INSERT INTO organizations (id, name) VALUES (1, 'ООО Подрядчик')")
    cursor.execute("INSERT INTO persons (id, full_name) VALUES (1, 'Иванов И.И.')")
    cursor.execute("INSERT INTO persons (id, full_name) VALUES (2, 'Петров П.П.')")
    
    # Insert sample estimates with various dates
    base_date = date(2024, 1, 1)
    for i in range(1, 101):  # 100 estimates
        estimate_date = base_date + timedelta(days=i * 3)
        cursor.execute("""
            INSERT INTO estimates (
                id, number, date, customer_id, object_id, contractor_id, 
                responsible_id, total_sum, total_labor, estimate_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i, f'EST-{i:03d}', estimate_date.isoformat(),
            1 if i % 2 == 0 else 2,  # Alternate customers
            1 if i % 3 == 0 else 2,  # Alternate objects
            1, 1 if i % 2 == 0 else 2,  # Alternate responsible persons
            100000 + i * 1000, 40 + i * 2,
            'General' if i % 4 == 0 else 'Plan'
        ))
    
    db.commit()
    return db


def demonstrate_pagination():
    """Demonstrate pagination functionality"""
    print("=== PAGINATION DEMONSTRATION ===")
    
    # Create pagination service
    config = PaginationConfig(default_page_size=10, max_page_size=50)
    service = PaginationService(config)
    
    # Create test database
    db = create_test_database()
    
    # Test query
    base_query = """
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            p.full_name as responsible_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN persons p ON e.responsible_id = p.id
        WHERE e.marked_for_deletion = 0
        ORDER BY e.date DESC
    """
    
    # Test different pages
    for page in [1, 2, 5, 10]:
        print(f"\n--- Page {page} ---")
        result = service.paginate_query_result(db, base_query, [], page, 10)
        
        print(f"Items on page: {len(result.items)}")
        print(f"Total items: {result.total_items}")
        print(f"Total pages: {result.total_pages}")
        print(f"Has next: {result.has_next}")
        print(f"Has previous: {result.has_previous}")
        
        if result.items:
            print(f"First item: {result.items[0]['number']} - {result.items[0]['date']}")
            print(f"Last item: {result.items[-1]['number']} - {result.items[-1]['date']}")
    
    db.close()


def demonstrate_sorting():
    """Demonstrate sorting functionality"""
    print("\n=== SORTING DEMONSTRATION ===")
    
    # Create sorting service
    service = SortingService()
    
    # Create test database
    db = create_test_database()
    cursor = db.cursor()
    
    # Base query
    base_query = """
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            p.full_name as responsible_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN persons p ON e.responsible_id = p.id
        WHERE e.marked_for_deletion = 0
    """
    
    # Test different sorting options
    sort_tests = [
        ('date', 'desc', 'Most recent first'),
        ('number', 'asc', 'Number ascending'),
        ('total_sum', 'desc', 'Highest sum first'),
        ('customer_name', 'asc', 'Customer name A-Z')
    ]
    
    for sort_by, sort_order, description in sort_tests:
        print(f"\n--- {description} ---")
        
        sorted_query, error = service.apply_sorting_to_query(
            base_query, 'estimates', sort_by, sort_order
        )
        
        if error:
            print(f"Error: {error}")
            continue
        
        # Execute query and show first 5 results
        cursor.execute(f"{sorted_query} LIMIT 5")
        results = cursor.fetchall()
        
        for row in results:
            if sort_by == 'date':
                print(f"  {row['number']}: {row['date']}")
            elif sort_by == 'number':
                print(f"  {row['number']}: {row['date']}")
            elif sort_by == 'total_sum':
                print(f"  {row['number']}: {row['total_sum']:,.2f}")
            elif sort_by == 'customer_name':
                print(f"  {row['number']}: {row['customer_name']}")
    
    # Test invalid sorting
    print(f"\n--- Invalid sorting test ---")
    sorted_query, error = service.apply_sorting_to_query(
        base_query, 'estimates', 'invalid_column', 'asc'
    )
    print(f"Error (expected): {error}")
    
    db.close()


def demonstrate_date_filtering():
    """Demonstrate date filtering functionality"""
    print("\n=== DATE FILTERING DEMONSTRATION ===")
    
    # Create date filter service
    service = DateFilterService()
    
    # Create test database
    db = create_test_database()
    cursor = db.cursor()
    
    # Test default date range calculation
    print("--- Default date range ---")
    default_range = service.get_default_date_range(db, 'estimates')
    print(f"Start date: {default_range.start_date}")
    print(f"End date: {default_range.end_date}")
    print(f"Is default: {default_range.is_default}")
    print(f"Summary: {service.get_date_range_summary(default_range)}")
    
    # Test date filtering
    print("\n--- Date filtering test ---")
    base_query = """
        SELECT 
            e.*,
            c.name as customer_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
    """
    
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    # Apply date filter for Q1 2024
    start_date = date(2024, 1, 1)
    end_date = date(2024, 3, 31)
    
    query, where_clauses, params, error = service.apply_date_filter_to_query(
        base_query, 'estimates', start_date, end_date, where_clauses, params
    )
    
    if error:
        print(f"Error: {error}")
    else:
        # Build complete query
        where_sql = " AND ".join(where_clauses)
        complete_query = f"{query} WHERE {where_sql} ORDER BY e.date"
        
        cursor.execute(complete_query, params)
        results = cursor.fetchall()
        
        print(f"Found {len(results)} estimates in Q1 2024:")
        for row in results[:10]:  # Show first 10
            print(f"  {row['number']}: {row['date']}")
        
        if len(results) > 10:
            print(f"  ... and {len(results) - 10} more")
    
    # Test date range validation
    print("\n--- Date validation test ---")
    test_cases = [
        (date(2024, 1, 1), date(2024, 12, 31), "Valid range"),
        (date(2024, 12, 31), date(2024, 1, 1), "Invalid range (start > end)"),
        (date(1800, 1, 1), date(2024, 1, 1), "Date too far in past"),
        (date(2024, 1, 1), date(2200, 1, 1), "Date too far in future")
    ]
    
    for start, end, description in test_cases:
        is_valid, error = service.validate_date_range(start, end)
        print(f"  {description}: {'Valid' if is_valid else f'Invalid - {error}'}")
    
    db.close()


def demonstrate_integration():
    """Demonstrate integration of all services"""
    print("\n=== INTEGRATION DEMONSTRATION ===")
    
    # Create all services
    pagination_service = PaginationService(PaginationConfig(default_page_size=5))
    sorting_service = SortingService()
    date_filter_service = DateFilterService()
    
    # Create test database
    db = create_test_database()
    cursor = db.cursor()
    
    print("--- Complete API-style query ---")
    
    # Simulate API parameters
    page = 1
    page_size = 5
    sort_by = 'total_sum'
    sort_order = 'desc'
    date_from = date(2024, 6, 1)
    date_to = date(2024, 12, 31)
    search = 'EST'
    
    # Build base query
    base_query = """
        SELECT 
            e.*,
            c.name as customer_name,
            o.name as object_name,
            p.full_name as responsible_name
        FROM estimates e
        LEFT JOIN counterparties c ON e.customer_id = c.id
        LEFT JOIN objects o ON e.object_id = o.id
        LEFT JOIN persons p ON e.responsible_id = p.id
    """
    
    # Build WHERE clauses
    where_clauses = ["e.marked_for_deletion = 0"]
    params = []
    
    # Apply search
    if search:
        where_clauses.append("(e.number LIKE ? OR c.name LIKE ? OR o.name LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    # Apply date filter
    query, where_clauses, params, date_error = date_filter_service.apply_date_filter_to_query(
        base_query, 'estimates', date_from, date_to, where_clauses, params
    )
    
    if date_error:
        print(f"Date filter error: {date_error}")
        return
    
    # Build complete query
    where_sql = " AND ".join(where_clauses)
    complete_query = f"{query} WHERE {where_sql}"
    
    # Apply sorting
    sorted_query, sort_error = sorting_service.apply_sorting_to_query(
        complete_query, 'estimates', sort_by, sort_order
    )
    
    if sort_error:
        print(f"Sort error: {sort_error}")
        return
    
    # Apply pagination
    result = pagination_service.paginate_query_result(
        db, sorted_query, params, page, page_size
    )
    
    # Display results
    print(f"Query parameters:")
    print(f"  Page: {page}, Page size: {page_size}")
    print(f"  Sort: {sort_by} {sort_order}")
    print(f"  Date range: {date_from} to {date_to}")
    print(f"  Search: '{search}'")
    
    print(f"\nResults:")
    print(f"  Total items: {result.total_items}")
    print(f"  Total pages: {result.total_pages}")
    print(f"  Current page: {result.page}")
    print(f"  Items on page: {len(result.items)}")
    
    print(f"\nItems:")
    for item in result.items:
        print(f"  {item['number']}: {item['date']} - {item['total_sum']:,.2f} - {item['customer_name']}")
    
    # Create API-style response
    response = {
        "success": True,
        "data": result.items,
        "pagination": pagination_service.create_pagination_info_dict(result),
        "sorting": {
            "sort_by": sort_by,
            "sort_order": sort_order,
            "available_columns": sorting_service.get_sortable_columns('estimates')
        },
        "filtering": {
            "search": search,
            "date_range": {
                "start_date": date_from.isoformat(),
                "end_date": date_to.isoformat()
            }
        }
    }
    
    print(f"\nAPI Response structure:")
    print(f"  Success: {response['success']}")
    print(f"  Data items: {len(response['data'])}")
    print(f"  Pagination info: {response['pagination']}")
    print(f"  Sorting info: {response['sorting']['sort_by']} {response['sorting']['sort_order']}")
    print(f"  Available sort columns: {len(response['sorting']['available_columns'])}")
    
    db.close()


def main():
    """Run all demonstrations"""
    print("Enhanced API Pagination, Sorting, and Filtering Demonstration")
    print("=" * 60)
    
    demonstrate_pagination()
    demonstrate_sorting()
    demonstrate_date_filtering()
    demonstrate_integration()
    
    print("\n" + "=" * 60)
    print("Demonstration completed successfully!")
    print("\nKey features implemented:")
    print("✓ Configurable pagination with metadata")
    print("✓ Column sorting with validation")
    print("✓ Intelligent default date filtering")
    print("✓ Advanced search and filtering")
    print("✓ Integration of all services")
    print("✓ API-style response formatting")


if __name__ == "__main__":
    main()