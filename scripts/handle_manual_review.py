#!/usr/bin/env python3
"""Handle manual review cases for unit migration

This script processes works requiring manual unit assignment,
validates migration results, and updates migration tracking.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.services.migration_workflow_service import MigrationWorkflowService
from src.services.work_unit_migration_service import WorkUnitMigrationService
from src.data.models.sqlalchemy_models import Work, Unit, WorkUnitMigration
from sqlalchemy import func


class ManualReviewHandler:
    """Handler for manual review cases in unit migration"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.workflow_service = MigrationWorkflowService(db_manager)
        self.migration_service = WorkUnitMigrationService(db_manager)
    
    def get_manual_review_summary(self) -> Dict[str, Any]:
        """Get summary of manual review cases"""
        print("Analyzing manual review cases...")
        
        # Get migration statistics
        stats = self.migration_service.get_migration_statistics()
        
        # Get manual review items
        manual_items = self.workflow_service.get_manual_review_items()
        
        # Group by reason
        reasons = {}
        for item in manual_items:
            reason = item.get('manual_review_reason', 'Unknown')
            if reason not in reasons:
                reasons[reason] = []
            reasons[reason].append(item)
        
        return {
            'total_manual_items': len(manual_items),
            'migration_statistics': stats,
            'items_by_reason': reasons,
            'sample_items': manual_items[:10]  # First 10 for display
        }
    
    def display_manual_review_items(self, limit: int = 20):
        """Display manual review items for user review"""
        items = self.workflow_service.get_manual_review_items(limit=limit)
        
        if not items:
            print("No manual review items found.")
            return
        
        print(f"\nManual Review Items (showing {len(items)} items):")
        print("=" * 80)
        
        for i, item in enumerate(items, 1):
            print(f"\n{i}. Work ID: {item['work_id']}")
            print(f"   Work Name: {item['work_name']}")
            print(f"   Legacy Unit: '{item['legacy_unit']}'")
            print(f"   Confidence: {item['confidence_score']:.2f}")
            print(f"   Reason: {item['manual_review_reason']}")
            
            if item['potential_matches']:
                print(f"   Potential Matches:")
                for j, match in enumerate(item['potential_matches'], 1):
                    print(f"     {j}. Unit #{match['unit_id']}: '{match['unit_name']}' "
                          f"(similarity: {match['similarity']:.2f})")
            else:
                print(f"   No potential matches found")
    
    def resolve_manual_item_interactive(self, work_id: int) -> bool:
        """Interactively resolve a manual review item"""
        
        # Get the manual review item
        items = self.workflow_service.get_manual_review_items()
        item = next((i for i in items if i['work_id'] == work_id), None)
        
        if not item:
            print(f"No manual review item found for work ID {work_id}")
            return False
        
        print(f"\nResolving Work ID: {work_id}")
        print(f"Work Name: {item['work_name']}")
        print(f"Legacy Unit: '{item['legacy_unit']}'")
        print(f"Reason: {item['manual_review_reason']}")
        
        if item['potential_matches']:
            print(f"\nPotential Matches:")
            for i, match in enumerate(item['potential_matches'], 1):
                print(f"  {i}. Unit #{match['unit_id']}: '{match['unit_name']}' "
                      f"(similarity: {match['similarity']:.2f})")
            
            print(f"  0. No unit assignment needed")
            print(f"  s. Skip this item")
            
            while True:
                choice = input("\nSelect option (number, 0, or s): ").strip().lower()
                
                if choice == 's':
                    return False
                elif choice == '0':
                    # No unit assignment needed
                    success = self.workflow_service.resolve_manual_review(work_id, None)
                    if success:
                        print("Marked as 'no unit assignment needed'")
                    return success
                else:
                    try:
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(item['potential_matches']):
                            selected_match = item['potential_matches'][choice_num - 1]
                            selected_unit_id = selected_match['unit_id']
                            
                            success = self.workflow_service.resolve_manual_review(
                                work_id, selected_unit_id
                            )
                            if success:
                                print(f"Assigned unit #{selected_unit_id}: '{selected_match['unit_name']}'")
                            return success
                        else:
                            print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number, 0, or 's'.")
        else:
            print(f"\nNo potential matches found.")
            print(f"Options:")
            print(f"  0. No unit assignment needed")
            print(f"  s. Skip this item")
            
            while True:
                choice = input("\nSelect option (0 or s): ").strip().lower()
                
                if choice == 's':
                    return False
                elif choice == '0':
                    success = self.workflow_service.resolve_manual_review(work_id, None)
                    if success:
                        print("Marked as 'no unit assignment needed'")
                    return success
                else:
                    print("Invalid choice. Please enter 0 or 's'.")
    
    def batch_resolve_by_pattern(self, pattern_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch resolve items based on pattern rules
        
        pattern_rules format:
        [
            {
                'legacy_unit_pattern': 'шт',
                'target_unit_id': 123,
                'description': 'Map all шт to pieces unit'
            }
        ]
        """
        
        items = self.workflow_service.get_manual_review_items()
        resolved_count = 0
        errors = []
        
        for rule in pattern_rules:
            pattern = rule['legacy_unit_pattern'].lower()
            target_unit_id = rule.get('target_unit_id')
            
            matching_items = [
                item for item in items 
                if pattern in item['legacy_unit'].lower()
            ]
            
            print(f"Applying rule: {rule['description']}")
            print(f"Found {len(matching_items)} matching items")
            
            for item in matching_items:
                try:
                    success = self.workflow_service.resolve_manual_review(
                        item['work_id'], target_unit_id
                    )
                    if success:
                        resolved_count += 1
                        print(f"  Resolved work {item['work_id']}: '{item['legacy_unit']}'")
                    else:
                        errors.append({
                            'work_id': item['work_id'],
                            'error': 'Failed to resolve'
                        })
                except Exception as e:
                    errors.append({
                        'work_id': item['work_id'],
                        'error': str(e)
                    })
        
        return {
            'resolved_count': resolved_count,
            'errors': errors,
            'rules_applied': len(pattern_rules)
        }
    
    def validate_migration_integrity(self) -> Dict[str, Any]:
        """Validate migration results for data integrity"""
        print("Validating migration integrity...")
        
        with self.db_manager.get_session() as session:
            # Check for orphaned unit_id references
            orphaned_works = session.query(Work).filter(
                Work.unit_id.isnot(None)
            ).outerjoin(Unit, Work.unit_id == Unit.id).filter(
                Unit.id.is_(None)
            ).all()
            
            # Check for works without units (should be acceptable)
            works_without_units = session.query(Work).filter(
                Work.unit_id.is_(None)
            ).count()
            
            # Check migration tracking consistency
            migration_entries = session.query(WorkUnitMigration).all()
            
            # Validate completed migrations
            completed_migrations = [m for m in migration_entries if m.migration_status == 'completed']
            invalid_completed = []
            
            for migration in completed_migrations:
                work = session.query(Work).filter(Work.id == migration.work_id).first()
                if not work:
                    invalid_completed.append({
                        'migration_id': migration.work_id,
                        'issue': 'Work not found'
                    })
                elif work.unit_id != migration.matched_unit_id:
                    invalid_completed.append({
                        'migration_id': migration.work_id,
                        'issue': f'Unit mismatch: work.unit_id={work.unit_id}, migration.matched_unit_id={migration.matched_unit_id}'
                    })
            
            # Check for duplicate migration entries
            duplicate_entries = session.query(WorkUnitMigration.work_id).group_by(
                WorkUnitMigration.work_id
            ).having(func.count(WorkUnitMigration.work_id) > 1).all()
            
            return {
                'orphaned_unit_references': len(orphaned_works),
                'orphaned_works': [{'id': w.id, 'name': w.name, 'unit_id': w.unit_id} for w in orphaned_works],
                'works_without_units': works_without_units,
                'total_migration_entries': len(migration_entries),
                'completed_migrations': len(completed_migrations),
                'invalid_completed_migrations': len(invalid_completed),
                'invalid_completed_details': invalid_completed,
                'duplicate_migration_entries': len(duplicate_entries),
                'validation_timestamp': datetime.now().isoformat()
            }
    
    def generate_manual_review_report(self) -> str:
        """Generate comprehensive manual review report"""
        
        summary = self.get_manual_review_summary()
        validation = self.validate_migration_integrity()
        
        report_lines = [
            "=" * 80,
            "MANUAL REVIEW HANDLING REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            "",
            "MANUAL REVIEW SUMMARY",
            "-" * 80,
            f"Total manual review items: {summary['total_manual_items']}",
            ""
        ]
        
        if summary['items_by_reason']:
            report_lines.extend([
                "Items by reason:",
            ])
            for reason, items in summary['items_by_reason'].items():
                report_lines.append(f"  {reason}: {len(items)} items")
            report_lines.append("")
        
        # Migration statistics
        stats = summary['migration_statistics']
        report_lines.extend([
            "MIGRATION STATISTICS",
            "-" * 80,
            f"Total migration entries: {stats.get('total_entries', 0)}",
            f"Average confidence: {stats.get('average_confidence', 0)}",
            f"Completion percentage: {stats.get('completion_percentage', 0)}%",
            ""
        ])
        
        if 'status_counts' in stats:
            report_lines.extend([
                "Status breakdown:",
            ])
            for status, count in stats['status_counts'].items():
                report_lines.append(f"  {status}: {count}")
            report_lines.append("")
        
        # Validation results
        report_lines.extend([
            "INTEGRITY VALIDATION",
            "-" * 80,
            f"Orphaned unit references: {validation['orphaned_unit_references']}",
            f"Works without units: {validation['works_without_units']}",
            f"Invalid completed migrations: {validation['invalid_completed_migrations']}",
            f"Duplicate migration entries: {validation['duplicate_migration_entries']}",
            ""
        ])
        
        if validation['orphaned_works']:
            report_lines.extend([
                "ORPHANED UNIT REFERENCES (need fixing):",
            ])
            for work in validation['orphaned_works'][:10]:
                report_lines.append(f"  Work #{work['id']}: {work['name']} (unit_id: {work['unit_id']})")
            if len(validation['orphaned_works']) > 10:
                report_lines.append(f"  ... and {len(validation['orphaned_works']) - 10} more")
            report_lines.append("")
        
        if validation['invalid_completed_details']:
            report_lines.extend([
                "INVALID COMPLETED MIGRATIONS (need fixing):",
            ])
            for invalid in validation['invalid_completed_details'][:10]:
                report_lines.append(f"  Migration {invalid['migration_id']}: {invalid['issue']}")
            if len(validation['invalid_completed_details']) > 10:
                report_lines.append(f"  ... and {len(validation['invalid_completed_details']) - 10} more")
            report_lines.append("")
        
        # Sample manual review items
        if summary['sample_items']:
            report_lines.extend([
                "SAMPLE MANUAL REVIEW ITEMS",
                "-" * 80,
            ])
            for item in summary['sample_items'][:5]:
                report_lines.append(
                    f"Work #{item['work_id']}: '{item['legacy_unit']}' "
                    f"(confidence: {item['confidence_score']:.2f}) - {item['manual_review_reason']}"
                )
            report_lines.append("")
        
        report_lines.extend([
            "RECOMMENDATIONS",
            "-" * 80,
            "1. Review and resolve remaining manual review items",
            "2. Fix any orphaned unit references found",
            "3. Clean up invalid completed migrations",
            "4. Consider batch resolution for common patterns",
            "",
            "=" * 80,
        ])
        
        return "\n".join(report_lines)
    
    def interactive_review_session(self):
        """Run interactive manual review session"""
        
        while True:
            summary = self.get_manual_review_summary()
            
            if summary['total_manual_items'] == 0:
                print("No manual review items remaining!")
                break
            
            print(f"\n{summary['total_manual_items']} manual review items remaining")
            print("\nOptions:")
            print("1. Display items")
            print("2. Resolve specific item")
            print("3. Generate report")
            print("4. Validate integrity")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.display_manual_review_items()
            elif choice == '2':
                try:
                    work_id = int(input("Enter work ID to resolve: ").strip())
                    self.resolve_manual_item_interactive(work_id)
                except ValueError:
                    print("Invalid work ID")
            elif choice == '3':
                report = self.generate_manual_review_report()
                print(report)
            elif choice == '4':
                validation = self.validate_migration_integrity()
                print(f"\nValidation Results:")
                print(f"  Orphaned references: {validation['orphaned_unit_references']}")
                print(f"  Invalid completed: {validation['invalid_completed_migrations']}")
                print(f"  Duplicate entries: {validation['duplicate_migration_entries']}")
            elif choice == '5':
                break
            else:
                print("Invalid choice")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Handle manual review cases')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run interactive review session')
    parser.add_argument('--report', '-r', action='store_true',
                       help='Generate and display report')
    parser.add_argument('--validate', '-v', action='store_true',
                       help='Validate migration integrity')
    parser.add_argument('--list', '-l', type=int, default=20,
                       help='List manual review items (default: 20)')
    parser.add_argument('--resolve', type=int,
                       help='Resolve specific work ID')
    parser.add_argument('--output', '-o',
                       help='Output file for report')
    
    args = parser.parse_args()
    
    try:
        # Initialize database manager
        print("Initializing database connection...")
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Create handler
        handler = ManualReviewHandler(db_manager)
        
        if args.interactive:
            handler.interactive_review_session()
        elif args.report:
            report = handler.generate_manual_review_report()
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Report saved to: {args.output}")
            else:
                print(report)
        elif args.validate:
            validation = handler.validate_migration_integrity()
            print(json.dumps(validation, indent=2, ensure_ascii=False, default=str))
        elif args.resolve:
            handler.resolve_manual_item_interactive(args.resolve)
        else:
            # Default: list items
            handler.display_manual_review_items(args.list)
        
    except Exception as e:
        print(f"Error during manual review handling: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()