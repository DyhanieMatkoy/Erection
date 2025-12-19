#!/usr/bin/env python3
"""Validate migration results

This script verifies that all works have proper unit_id assignments,
checks that no data was lost during migration, and confirms all API
endpoints work with the new structure.
"""

import sys
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work, Unit, WorkUnitMigration
from sqlalchemy import func, and_, or_


class MigrationResultValidator:
    """Validator for migration results and system integrity"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def validate_unit_assignments(self) -> Dict[str, Any]:
        """Verify all works have proper unit_id assignments"""
        print("Validating unit assignments...")
        
        with self.db_manager.get_session() as session:
            # Count total works
            total_works = session.query(Work).filter(
                Work.marked_for_deletion == False
            ).count()
            
            # Count works with unit_id
            works_with_unit_id = session.query(Work).filter(
                and_(
                    Work.unit_id.isnot(None),
                    Work.marked_for_deletion == False
                )
            ).count()
            
            # Count works without unit_id
            works_without_unit_id = session.query(Work).filter(
                and_(
                    Work.unit_id.is_(None),
                    Work.marked_for_deletion == False
                )
            ).count()
            
            # Check for invalid unit_id references
            invalid_unit_refs = session.query(Work).filter(
                and_(
                    Work.unit_id.isnot(None),
                    Work.marked_for_deletion == False
                )
            ).outerjoin(Unit, Work.unit_id == Unit.id).filter(
                Unit.id.is_(None)
            ).all()
            
            # Sample works without units for analysis
            sample_without_units = session.query(Work).filter(
                and_(
                    Work.unit_id.is_(None),
                    Work.marked_for_deletion == False
                )
            ).limit(10).all()
            
            # Check unit distribution
            unit_usage = session.query(
                Unit.id, Unit.name, func.count(Work.id).label('work_count')
            ).join(Work, Work.unit_id == Unit.id).filter(
                Work.marked_for_deletion == False
            ).group_by(Unit.id, Unit.name).order_by(
                func.count(Work.id).desc()
            ).limit(20).all()
            
            return {
                'total_works': total_works,
                'works_with_unit_id': works_with_unit_id,
                'works_without_unit_id': works_without_unit_id,
                'unit_assignment_percentage': round((works_with_unit_id / max(total_works, 1)) * 100, 2),
                'invalid_unit_references': len(invalid_unit_refs),
                'invalid_unit_details': [
                    {
                        'work_id': w.id,
                        'work_name': w.name,
                        'invalid_unit_id': w.unit_id
                    } for w in invalid_unit_refs
                ],
                'sample_works_without_units': [
                    {
                        'work_id': w.id,
                        'work_name': w.name,
                        'is_group': w.is_group
                    } for w in sample_without_units
                ],
                'top_unit_usage': [
                    {
                        'unit_id': u.id,
                        'unit_name': u.name,
                        'work_count': u.work_count
                    } for u in unit_usage
                ]
            }
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Check that no data was lost during migration"""
        print("Validating data integrity...")
        
        with self.db_manager.get_session() as session:
            # Check for works with legacy unit data still present
            works_with_legacy_unit = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    Work.marked_for_deletion == False
                )
            ).count()
            
            # Check migration tracking completeness
            migration_entries = session.query(WorkUnitMigration).count()
            
            # Check for orphaned migration entries
            orphaned_migrations = session.query(WorkUnitMigration).outerjoin(
                Work, WorkUnitMigration.work_id == Work.id
            ).filter(Work.id.is_(None)).count()
            
            # Check migration status distribution
            migration_status_counts = session.query(
                WorkUnitMigration.migration_status,
                func.count(WorkUnitMigration.work_id)
            ).group_by(WorkUnitMigration.migration_status).all()
            
            # Check for works that should have been migrated but weren't
            works_needing_migration = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    or_(Work.unit_id.is_(None), Work.unit_id == 0),
                    Work.marked_for_deletion == False
                )
            ).count()
            
            # Verify referential integrity
            unit_count = session.query(Unit).filter(
                Unit.marked_for_deletion == False
            ).count()
            
            works_referencing_units = session.query(Work).filter(
                Work.unit_id.isnot(None)
            ).count()
            
            return {
                'works_with_legacy_unit_data': works_with_legacy_unit,
                'migration_entries_count': migration_entries,
                'orphaned_migration_entries': orphaned_migrations,
                'migration_status_distribution': dict(migration_status_counts),
                'works_still_needing_migration': works_needing_migration,
                'total_units_available': unit_count,
                'works_referencing_units': works_referencing_units,
                'data_integrity_score': self._calculate_integrity_score(
                    works_with_legacy_unit, works_needing_migration, orphaned_migrations
                )
            }
    
    def _calculate_integrity_score(self, legacy_count: int, 
                                 needs_migration: int, orphaned: int) -> float:
        """Calculate data integrity score (0-100)"""
        issues = legacy_count + needs_migration + orphaned
        if issues == 0:
            return 100.0
        elif issues <= 5:
            return 95.0
        elif issues <= 20:
            return 80.0
        elif issues <= 50:
            return 60.0
        else:
            return max(0.0, 60.0 - (issues - 50) * 0.5)
    
    def test_api_endpoints(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Test API endpoints to confirm they work with new structure"""
        print("Testing API endpoints...")
        
        test_results = []
        
        # Test endpoints
        endpoints_to_test = [
            {
                'name': 'List Works',
                'method': 'GET',
                'url': f'{base_url}/api/references/works',
                'params': {'page': 1, 'page_size': 10}
            },
            {
                'name': 'List Works with Unit Info',
                'method': 'GET',
                'url': f'{base_url}/api/references/works',
                'params': {'page': 1, 'page_size': 10, 'include_unit_info': True}
            },
            {
                'name': 'List Units',
                'method': 'GET',
                'url': f'{base_url}/api/references/units',
                'params': {'page': 1, 'page_size': 10}
            },
            {
                'name': 'Migration Status',
                'method': 'GET',
                'url': f'{base_url}/api/references/works/migration-status'
            }
        ]
        
        for endpoint in endpoints_to_test:
            try:
                if endpoint['method'] == 'GET':
                    response = requests.get(
                        endpoint['url'],
                        params=endpoint.get('params', {}),
                        timeout=10
                    )
                
                test_results.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_size': len(response.content),
                    'has_data': len(response.json().get('items', [])) > 0 if response.status_code == 200 else False
                })
                
            except requests.exceptions.RequestException as e:
                test_results.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                })
            except Exception as e:
                test_results.append({
                    'endpoint': endpoint['name'],
                    'url': endpoint['url'],
                    'status_code': None,
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                })
        
        successful_tests = sum(1 for result in test_results if result['success'])
        
        return {
            'total_endpoints_tested': len(endpoints_to_test),
            'successful_tests': successful_tests,
            'failed_tests': len(endpoints_to_test) - successful_tests,
            'success_rate': round((successful_tests / len(endpoints_to_test)) * 100, 2),
            'test_results': test_results
        }
    
    def validate_work_hierarchy_integrity(self) -> Dict[str, Any]:
        """Validate that work hierarchy is intact after migration"""
        print("Validating work hierarchy integrity...")
        
        with self.db_manager.get_session() as session:
            # Check for circular references
            circular_refs = []
            
            # Get all works with parents
            works_with_parents = session.query(Work).filter(
                and_(
                    Work.parent_id.isnot(None),
                    Work.marked_for_deletion == False
                )
            ).all()
            
            for work in works_with_parents:
                visited = set()
                current = work
                
                while current and current.parent_id:
                    if current.id in visited:
                        circular_refs.append({
                            'work_id': work.id,
                            'work_name': work.name,
                            'circular_path': list(visited)
                        })
                        break
                    
                    visited.add(current.id)
                    current = session.query(Work).filter(Work.id == current.parent_id).first()
            
            # Check for orphaned parent references
            from sqlalchemy.orm import aliased
            ParentWork = aliased(Work)
            
            orphaned_parents = session.query(Work).filter(
                and_(
                    Work.parent_id.isnot(None),
                    Work.marked_for_deletion == False
                )
            ).outerjoin(
                ParentWork, Work.parent_id == ParentWork.id
            ).filter(
                ParentWork.id.is_(None)
            ).count()
            
            # Check hierarchy depth distribution
            max_depth = 0
            depth_distribution = {}
            
            root_works = session.query(Work).filter(
                and_(
                    Work.parent_id.is_(None),
                    Work.marked_for_deletion == False
                )
            ).all()
            
            def calculate_depth(work, depth=0):
                nonlocal max_depth
                max_depth = max(max_depth, depth)
                
                if depth not in depth_distribution:
                    depth_distribution[depth] = 0
                depth_distribution[depth] += 1
                
                children = session.query(Work).filter(
                    and_(
                        Work.parent_id == work.id,
                        Work.marked_for_deletion == False
                    )
                ).all()
                
                for child in children:
                    calculate_depth(child, depth + 1)
            
            for root_work in root_works[:100]:  # Limit to avoid performance issues
                calculate_depth(root_work)
            
            return {
                'circular_references': len(circular_refs),
                'circular_reference_details': circular_refs,
                'orphaned_parent_references': orphaned_parents,
                'max_hierarchy_depth': max_depth,
                'depth_distribution': depth_distribution,
                'total_root_works': len(root_works),
                'works_with_parents': len(works_with_parents)
            }
    
    def generate_validation_report(self, include_api_tests: bool = True,
                                 api_base_url: str = "http://localhost:8000") -> str:
        """Generate comprehensive validation report"""
        
        # Run all validations
        unit_validation = self.validate_unit_assignments()
        integrity_validation = self.validate_data_integrity()
        hierarchy_validation = self.validate_work_hierarchy_integrity()
        
        api_validation = None
        if include_api_tests:
            try:
                api_validation = self.test_api_endpoints(api_base_url)
            except Exception as e:
                api_validation = {
                    'error': f'API testing failed: {str(e)}',
                    'success_rate': 0
                }
        
        # Generate report
        report_lines = [
            "=" * 80,
            "MIGRATION RESULTS VALIDATION REPORT",
            f"Generated: {datetime.now().isoformat()}",
            "=" * 80,
            "",
            "UNIT ASSIGNMENT VALIDATION",
            "-" * 80,
            f"Total works: {unit_validation['total_works']}",
            f"Works with unit_id: {unit_validation['works_with_unit_id']}",
            f"Works without unit_id: {unit_validation['works_without_unit_id']}",
            f"Unit assignment percentage: {unit_validation['unit_assignment_percentage']}%",
            f"Invalid unit references: {unit_validation['invalid_unit_references']}",
            ""
        ]
        
        if unit_validation['invalid_unit_references'] > 0:
            report_lines.extend([
                "INVALID UNIT REFERENCES (need fixing):",
            ])
            for invalid in unit_validation['invalid_unit_details'][:10]:
                report_lines.append(
                    f"  Work #{invalid['work_id']}: {invalid['work_name']} "
                    f"(invalid unit_id: {invalid['invalid_unit_id']})"
                )
            report_lines.append("")
        
        # Data integrity section
        report_lines.extend([
            "DATA INTEGRITY VALIDATION",
            "-" * 80,
            f"Works with legacy unit data: {integrity_validation['works_with_legacy_unit_data']}",
            f"Migration entries: {integrity_validation['migration_entries_count']}",
            f"Orphaned migration entries: {integrity_validation['orphaned_migration_entries']}",
            f"Works still needing migration: {integrity_validation['works_still_needing_migration']}",
            f"Data integrity score: {integrity_validation['data_integrity_score']:.1f}/100",
            ""
        ])
        
        if integrity_validation['migration_status_distribution']:
            report_lines.extend([
                "Migration status distribution:",
            ])
            for status, count in integrity_validation['migration_status_distribution'].items():
                report_lines.append(f"  {status}: {count}")
            report_lines.append("")
        
        # Hierarchy validation section
        report_lines.extend([
            "HIERARCHY INTEGRITY VALIDATION",
            "-" * 80,
            f"Circular references: {hierarchy_validation['circular_references']}",
            f"Orphaned parent references: {hierarchy_validation['orphaned_parent_references']}",
            f"Maximum hierarchy depth: {hierarchy_validation['max_hierarchy_depth']}",
            f"Total root works: {hierarchy_validation['total_root_works']}",
            f"Works with parents: {hierarchy_validation['works_with_parents']}",
            ""
        ])
        
        # API validation section
        if api_validation:
            if 'error' in api_validation:
                report_lines.extend([
                    "API ENDPOINT VALIDATION",
                    "-" * 80,
                    f"API testing failed: {api_validation['error']}",
                    ""
                ])
            else:
                report_lines.extend([
                    "API ENDPOINT VALIDATION",
                    "-" * 80,
                    f"Endpoints tested: {api_validation['total_endpoints_tested']}",
                    f"Successful tests: {api_validation['successful_tests']}",
                    f"Failed tests: {api_validation['failed_tests']}",
                    f"Success rate: {api_validation['success_rate']}%",
                    ""
                ])
                
                if api_validation['failed_tests'] > 0:
                    report_lines.extend([
                        "Failed API tests:",
                    ])
                    for result in api_validation['test_results']:
                        if not result['success']:
                            error_msg = result.get('error', f"Status: {result.get('status_code', 'Unknown')}")
                            report_lines.append(f"  {result['endpoint']}: {error_msg}")
                    report_lines.append("")
        
        # Overall assessment
        overall_score = self._calculate_overall_score(
            unit_validation, integrity_validation, hierarchy_validation, api_validation
        )
        
        report_lines.extend([
            "OVERALL ASSESSMENT",
            "-" * 80,
            f"Overall migration success score: {overall_score:.1f}/100",
            ""
        ])
        
        # Recommendations
        recommendations = self._generate_recommendations(
            unit_validation, integrity_validation, hierarchy_validation, api_validation
        )
        
        if recommendations:
            report_lines.extend([
                "RECOMMENDATIONS",
                "-" * 80,
            ])
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            report_lines.append("")
        
        report_lines.extend([
            "=" * 80,
        ])
        
        return "\n".join(report_lines)
    
    def _calculate_overall_score(self, unit_val: Dict, integrity_val: Dict,
                               hierarchy_val: Dict, api_val: Optional[Dict]) -> float:
        """Calculate overall migration success score"""
        
        # Unit assignment score (40% weight)
        unit_score = min(100, unit_val['unit_assignment_percentage'])
        if unit_val['invalid_unit_references'] > 0:
            unit_score -= min(20, unit_val['invalid_unit_references'] * 2)
        
        # Data integrity score (30% weight)
        integrity_score = integrity_val['data_integrity_score']
        
        # Hierarchy integrity score (20% weight)
        hierarchy_score = 100
        if hierarchy_val['circular_references'] > 0:
            hierarchy_score -= min(50, hierarchy_val['circular_references'] * 10)
        if hierarchy_val['orphaned_parent_references'] > 0:
            hierarchy_score -= min(30, hierarchy_val['orphaned_parent_references'] * 2)
        
        # API score (10% weight)
        api_score = 100
        if api_val and 'success_rate' in api_val:
            api_score = api_val['success_rate']
        elif api_val and 'error' in api_val:
            api_score = 0
        
        # Weighted average
        overall = (unit_score * 0.4 + integrity_score * 0.3 + 
                  hierarchy_score * 0.2 + api_score * 0.1)
        
        return max(0, min(100, overall))
    
    def _generate_recommendations(self, unit_val: Dict, integrity_val: Dict,
                                hierarchy_val: Dict, api_val: Optional[Dict]) -> List[str]:
        """Generate recommendations based on validation results"""
        
        recommendations = []
        
        # Unit assignment recommendations
        if unit_val['invalid_unit_references'] > 0:
            recommendations.append(
                f"Fix {unit_val['invalid_unit_references']} invalid unit references"
            )
        
        if unit_val['unit_assignment_percentage'] < 90:
            recommendations.append(
                "Consider assigning units to more works for better data consistency"
            )
        
        # Data integrity recommendations
        if integrity_val['works_with_legacy_unit_data'] > 0:
            recommendations.append(
                f"Remove legacy unit data from {integrity_val['works_with_legacy_unit_data']} works"
            )
        
        if integrity_val['orphaned_migration_entries'] > 0:
            recommendations.append(
                f"Clean up {integrity_val['orphaned_migration_entries']} orphaned migration entries"
            )
        
        if integrity_val['works_still_needing_migration'] > 0:
            recommendations.append(
                f"Complete migration for {integrity_val['works_still_needing_migration']} remaining works"
            )
        
        # Hierarchy recommendations
        if hierarchy_val['circular_references'] > 0:
            recommendations.append(
                f"Fix {hierarchy_val['circular_references']} circular references in work hierarchy"
            )
        
        if hierarchy_val['orphaned_parent_references'] > 0:
            recommendations.append(
                f"Fix {hierarchy_val['orphaned_parent_references']} orphaned parent references"
            )
        
        # API recommendations
        if api_val and api_val.get('success_rate', 100) < 100:
            recommendations.append(
                "Fix failing API endpoints to ensure system functionality"
            )
        
        if not recommendations:
            recommendations.append("Migration validation passed successfully - no issues found!")
        
        return recommendations


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate migration results')
    parser.add_argument('--output', '-o',
                       help='Output file for validation report')
    parser.add_argument('--no-api-tests', action='store_true',
                       help='Skip API endpoint testing')
    parser.add_argument('--api-url', default='http://localhost:8000',
                       help='Base URL for API testing (default: http://localhost:8000)')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    try:
        # Initialize database manager
        print("Initializing database connection...")
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Create validator
        validator = MigrationResultValidator(db_manager)
        
        if args.json:
            # Output detailed JSON results
            results = {
                'unit_validation': validator.validate_unit_assignments(),
                'integrity_validation': validator.validate_data_integrity(),
                'hierarchy_validation': validator.validate_work_hierarchy_integrity(),
                'validation_timestamp': datetime.now().isoformat()
            }
            
            if not args.no_api_tests:
                results['api_validation'] = validator.test_api_endpoints(args.api_url)
            
            output = json.dumps(results, indent=2, ensure_ascii=False, default=str)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output)
                print(f"JSON results saved to: {args.output}")
            else:
                print(output)
        else:
            # Generate human-readable report
            report = validator.generate_validation_report(
                include_api_tests=not args.no_api_tests,
                api_base_url=args.api_url
            )
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Validation report saved to: {args.output}")
            else:
                print(report)
        
    except Exception as e:
        print(f"Error during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()