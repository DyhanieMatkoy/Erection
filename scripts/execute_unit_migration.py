#!/usr/bin/env python3
"""Execute automated unit migration

This script runs the complete unit migration process on production data,
processing automatic matches and flagging manual review cases.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.services.migration_workflow_service import MigrationWorkflowService
from scripts.utils.migration_backup_utils import MigrationBackupManager


class UnitMigrationExecutor:
    """Executor for automated unit migration"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.workflow_service = MigrationWorkflowService(db_manager)
        self.backup_utils = MigrationBackupManager(db_manager)
    
    def create_pre_migration_backup(self) -> str:
        """Create backup before migration"""
        print("Creating pre-migration backup...")
        backup_info = self.backup_utils.create_pre_migration_backup()
        print(f"Backup created: {backup_info['timestamp']}")
        return backup_info['timestamp']
    
    def analyze_migration_scope(self) -> Dict[str, Any]:
        """Analyze and display migration scope"""
        print("Analyzing migration scope...")
        analysis = self.workflow_service.analyze_migration_scope()
        
        print(f"\nMigration Scope Analysis:")
        print(f"  Total works needing migration: {analysis['total_works_needing_migration']}")
        print(f"  Unique legacy unit strings: {analysis['unique_legacy_units']}")
        print(f"  Existing migration entries: {analysis['existing_migration_entries']}")
        
        if analysis['work_count_by_unit']:
            print(f"\nTop 10 most common legacy units:")
            sorted_units = sorted(analysis['work_count_by_unit'].items(), 
                                key=lambda x: x[1], reverse=True)
            for unit, count in sorted_units[:10]:
                print(f"    '{unit}': {count} works")
        
        return analysis
    
    def create_migration_plan(self, batch_size: int = 100) -> Dict[str, Any]:
        """Create and display migration plan"""
        print(f"\nCreating migration plan with batch size {batch_size}...")
        plan = self.workflow_service.create_migration_plan(batch_size)
        
        print(f"\nMigration Plan:")
        print(f"  Estimated batches: {plan['estimated_batches']}")
        print(f"  Estimated processing time: {plan['estimated_processing_time_minutes']} minutes")
        
        if 'match_statistics' in plan:
            stats = plan['match_statistics']
            print(f"\nPre-migration match statistics:")
            for match_type, count in stats.items():
                print(f"    {match_type}: {count}")
        
        return plan
    
    def execute_migration(self, batch_size: int = 100, 
                         auto_confirm: bool = False) -> Dict[str, Any]:
        """Execute the migration process"""
        
        # Get user confirmation unless auto_confirm is True
        if not auto_confirm:
            response = input("\nProceed with migration? (y/N): ").strip().lower()
            if response != 'y':
                print("Migration cancelled by user.")
                return {'status': 'cancelled'}
        
        print("\nStarting automated unit migration...")
        start_time = datetime.now()
        
        # Execute full migration
        result = self.workflow_service.execute_full_migration(batch_size)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        print(f"\nMigration completed in {total_time:.2f} seconds")
        print(f"Batches executed: {result['batches_executed']}")
        print(f"Total works processed: {result['total_works_processed']}")
        
        # Display final statistics
        if 'final_statistics' in result:
            stats = result['final_statistics']
            print(f"\nFinal Migration Statistics:")
            print(f"  Total entries: {stats['total_entries']}")
            print(f"  Average confidence: {stats['average_confidence']}")
            print(f"  Completion percentage: {stats['completion_percentage']}%")
            
            if 'status_counts' in stats:
                print(f"  Status breakdown:")
                for status, count in stats['status_counts'].items():
                    print(f"    {status}: {count}")
        
        return result
    
    def apply_high_confidence_matches(self, threshold: float = 0.9,
                                    auto_confirm: bool = False) -> Dict[str, Any]:
        """Apply high-confidence migration results"""
        
        if not auto_confirm:
            response = input(f"\nApply matches with confidence >= {threshold}? (y/N): ").strip().lower()
            if response != 'y':
                print("Auto-application cancelled by user.")
                return {'status': 'cancelled'}
        
        print(f"\nApplying high-confidence matches (threshold: {threshold})...")
        result = self.workflow_service.apply_migration_results(threshold)
        
        print(f"Applied {result['applied_count']} migrations")
        if result['errors']:
            print(f"Errors encountered: {len(result['errors'])}")
            for error in result['errors'][:5]:  # Show first 5 errors
                print(f"  Work {error['work_id']}: {error['error']}")
        
        return result
    
    def generate_migration_report(self, migration_result: Dict[str, Any],
                                application_result: Dict[str, Any] = None) -> str:
        """Generate detailed migration report"""
        
        report_lines = [
            "=" * 80,
            "AUTOMATED UNIT MIGRATION EXECUTION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            "",
            "MIGRATION EXECUTION SUMMARY",
            "-" * 80,
        ]
        
        if migration_result.get('status') == 'cancelled':
            report_lines.extend([
                "Migration was cancelled by user.",
                ""
            ])
        else:
            report_lines.extend([
                f"Batches executed: {migration_result.get('batches_executed', 0)}",
                f"Total works processed: {migration_result.get('total_works_processed', 0)}",
                f"Processing time: {migration_result.get('total_processing_time_seconds', 0):.2f} seconds",
                ""
            ])
            
            if 'final_statistics' in migration_result:
                stats = migration_result['final_statistics']
                report_lines.extend([
                    "FINAL STATISTICS",
                    "-" * 80,
                    f"Total migration entries: {stats.get('total_entries', 0)}",
                    f"Average confidence score: {stats.get('average_confidence', 0)}",
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
        
        if application_result and application_result.get('status') != 'cancelled':
            report_lines.extend([
                "AUTO-APPLICATION RESULTS",
                "-" * 80,
                f"Migrations applied: {application_result.get('applied_count', 0)}",
                f"Threshold used: {application_result.get('auto_apply_threshold', 0)}",
                f"Errors: {len(application_result.get('errors', []))}",
                ""
            ])
        
        # Get current progress
        progress = self.workflow_service.get_migration_progress()
        if 'statistics' in progress:
            stats = progress['statistics']
            report_lines.extend([
                "CURRENT SYSTEM STATE",
                "-" * 80,
                f"Works with legacy units: {stats.get('total_legacy_works', 0)}",
                f"Migration entries: {stats.get('total_entries', 0)}",
                f"Overall completion: {stats.get('completion_percentage', 0)}%",
                ""
            ])
        
        # Get manual review items
        manual_items = self.workflow_service.get_manual_review_items(limit=10)
        if manual_items:
            report_lines.extend([
                "MANUAL REVIEW REQUIRED (Sample - first 10)",
                "-" * 80,
            ])
            for item in manual_items:
                report_lines.append(
                    f"  Work #{item['work_id']}: '{item['legacy_unit']}' "
                    f"(confidence: {item['confidence_score']:.2f}) - {item['manual_review_reason']}"
                )
            report_lines.append("")
        
        report_lines.extend([
            "NEXT STEPS",
            "-" * 80,
            "1. Review manual review items and resolve them",
            "2. Validate migration results using validation script",
            "3. Update all systems to use new unit structure",
            "4. Remove legacy unit column after validation",
            "",
            "=" * 80,
        ])
        
        return "\n".join(report_lines)
    
    def save_migration_results(self, migration_result: Dict[str, Any],
                             application_result: Dict[str, Any] = None,
                             output_dir: str = "migration_results") -> str:
        """Save migration results to files"""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        results_file = os.path.join(output_dir, f"migration_results_{timestamp}.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'migration_result': migration_result,
                'application_result': application_result,
                'timestamp': timestamp
            }, f, indent=2, ensure_ascii=False, default=str)
        
        # Save human-readable report
        report = self.generate_migration_report(migration_result, application_result)
        report_file = os.path.join(output_dir, f"migration_report_{timestamp}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\nResults saved:")
        print(f"  Detailed results: {results_file}")
        print(f"  Human-readable report: {report_file}")
        
        return report_file


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Execute automated unit migration')
    parser.add_argument('--batch-size', '-b', type=int, default=100,
                       help='Batch size for processing (default: 100)')
    parser.add_argument('--auto-apply-threshold', '-t', type=float, default=0.9,
                       help='Threshold for auto-applying matches (default: 0.9)')
    parser.add_argument('--auto-confirm', '-y', action='store_true',
                       help='Auto-confirm all prompts (use with caution)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip pre-migration backup (not recommended)')
    parser.add_argument('--no-apply', action='store_true',
                       help='Skip auto-application of high-confidence matches')
    parser.add_argument('--output-dir', '-o', default='migration_results',
                       help='Output directory for results (default: migration_results)')
    
    args = parser.parse_args()
    
    try:
        # Initialize database manager
        print("Initializing database connection...")
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Create executor
        executor = UnitMigrationExecutor(db_manager)
        
        # Create backup unless skipped
        if not args.no_backup:
            backup_file = executor.create_pre_migration_backup()
        
        # Analyze scope
        analysis = executor.analyze_migration_scope()
        
        # Create plan
        plan = executor.create_migration_plan(args.batch_size)
        
        # Execute migration
        migration_result = executor.execute_migration(
            batch_size=args.batch_size,
            auto_confirm=args.auto_confirm
        )
        
        application_result = None
        
        # Apply high-confidence matches unless skipped
        if not args.no_apply and migration_result.get('status') != 'cancelled':
            application_result = executor.apply_high_confidence_matches(
                threshold=args.auto_apply_threshold,
                auto_confirm=args.auto_confirm
            )
        
        # Save results
        report_file = executor.save_migration_results(
            migration_result, application_result, args.output_dir
        )
        
        print(f"\nMigration execution completed successfully!")
        print(f"Report saved to: {report_file}")
        
    except Exception as e:
        print(f"Error during migration execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()