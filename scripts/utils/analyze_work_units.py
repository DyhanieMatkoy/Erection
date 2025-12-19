"""Work unit usage analysis tool

This script analyzes the current state of unit usage in the works table,
identifying migration opportunities, conflicts, and works requiring manual review.
"""

import sys
import os
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from difflib import SequenceMatcher

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Work, Unit
from sqlalchemy import and_, or_, func


class WorkUnitAnalyzer:
    """Analyzer for work unit migration"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def analyze_legacy_units(self) -> Dict[str, Any]:
        """Analyze legacy unit column usage"""
        with self.db_manager.get_session() as session:
            # Get all works with legacy units
            works_with_legacy = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != ''
                )
            ).all()
            
            # Get all available units
            all_units = session.query(Unit).filter(
                Unit.marked_for_deletion == False
            ).all()
            
            # Statistics
            total_works = session.query(Work).count()
            works_with_legacy_count = len(works_with_legacy)
            works_with_unit_id = session.query(Work).filter(
                Work.unit_id.isnot(None)
            ).count()
            works_with_both = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    Work.unit_id.isnot(None)
                )
            ).count()
            
            # Analyze legacy unit values
            legacy_unit_counts = defaultdict(int)
            for work in works_with_legacy:
                legacy_unit_counts[work.unit] += 1
            
            return {
                'total_works': total_works,
                'works_with_legacy_unit': works_with_legacy_count,
                'works_with_unit_id': works_with_unit_id,
                'works_with_both': works_with_both,
                'works_needing_migration': works_with_legacy_count - works_with_both,
                'unique_legacy_units': len(legacy_unit_counts),
                'legacy_unit_distribution': dict(legacy_unit_counts),
                'available_units': [{'id': u.id, 'name': u.name} for u in all_units]
            }
    
    def find_unit_matches(self, threshold: float = 0.8) -> Dict[str, List[Dict[str, Any]]]:
        """Find potential matches between legacy units and unit records"""
        with self.db_manager.get_session() as session:
            # Get all works with legacy units but no unit_id
            works_needing_migration = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    or_(Work.unit_id.is_(None), Work.unit_id == 0)
                )
            ).all()
            
            # Get all available units
            all_units = session.query(Unit).filter(
                Unit.marked_for_deletion == False
            ).all()
            
            # Find matches
            exact_matches = []
            fuzzy_matches = []
            no_matches = []
            
            for work in works_needing_migration:
                legacy_unit = work.unit.strip().lower()
                best_match = None
                best_score = 0.0
                
                for unit in all_units:
                    unit_name = unit.name.strip().lower()
                    
                    # Check for exact match
                    if legacy_unit == unit_name:
                        exact_matches.append({
                            'work_id': work.id,
                            'work_name': work.name,
                            'legacy_unit': work.unit,
                            'matched_unit_id': unit.id,
                            'matched_unit_name': unit.name,
                            'confidence': 1.0,
                            'match_type': 'exact'
                        })
                        best_match = None
                        break
                    
                    # Calculate similarity
                    similarity = SequenceMatcher(None, legacy_unit, unit_name).ratio()
                    if similarity > best_score:
                        best_score = similarity
                        best_match = unit
                
                # If no exact match found, check fuzzy match
                if best_match and best_score >= threshold:
                    fuzzy_matches.append({
                        'work_id': work.id,
                        'work_name': work.name,
                        'legacy_unit': work.unit,
                        'matched_unit_id': best_match.id,
                        'matched_unit_name': best_match.name,
                        'confidence': round(best_score, 2),
                        'match_type': 'fuzzy'
                    })
                elif not best_match or best_score < threshold:
                    no_matches.append({
                        'work_id': work.id,
                        'work_name': work.name,
                        'legacy_unit': work.unit,
                        'best_match_unit': best_match.name if best_match else None,
                        'best_match_score': round(best_score, 2) if best_match else 0.0,
                        'reason': 'No suitable match found' if not best_match else f'Low confidence ({best_score:.2f})'
                    })
            
            return {
                'exact_matches': exact_matches,
                'fuzzy_matches': fuzzy_matches,
                'no_matches': no_matches,
                'summary': {
                    'total_works_analyzed': len(works_needing_migration),
                    'exact_match_count': len(exact_matches),
                    'fuzzy_match_count': len(fuzzy_matches),
                    'no_match_count': len(no_matches),
                    'auto_migration_ready': len(exact_matches) + len(fuzzy_matches),
                    'manual_review_required': len(no_matches)
                }
            }
    
    def identify_conflicts(self) -> List[Dict[str, Any]]:
        """Identify works with conflicting unit information"""
        with self.db_manager.get_session() as session:
            # Find works where unit and unit_id don't match
            conflicts = []
            
            works_with_both = session.query(Work).filter(
                and_(
                    Work.unit.isnot(None),
                    Work.unit != '',
                    Work.unit_id.isnot(None)
                )
            ).all()
            
            for work in works_with_both:
                unit = session.query(Unit).filter(Unit.id == work.unit_id).first()
                if unit:
                    legacy_unit = work.unit.strip().lower()
                    unit_name = unit.name.strip().lower()
                    
                    if legacy_unit != unit_name:
                        conflicts.append({
                            'work_id': work.id,
                            'work_name': work.name,
                            'legacy_unit': work.unit,
                            'unit_id': work.unit_id,
                            'unit_name': unit.name,
                            'conflict_type': 'mismatch',
                            'recommendation': 'Review and choose correct unit'
                        })
            
            return conflicts
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive migration analysis report"""
        analysis = self.analyze_legacy_units()
        matches = self.find_unit_matches()
        conflicts = self.identify_conflicts()
        
        report_lines = [
            "=" * 80,
            "WORK UNIT MIGRATION ANALYSIS REPORT",
            "=" * 80,
            "",
            "OVERVIEW",
            "-" * 80,
            f"Total works in database: {analysis['total_works']}",
            f"Works with legacy unit column: {analysis['works_with_legacy_unit']}",
            f"Works with unit_id: {analysis['works_with_unit_id']}",
            f"Works with both: {analysis['works_with_both']}",
            f"Works needing migration: {analysis['works_needing_migration']}",
            f"Unique legacy unit values: {analysis['unique_legacy_units']}",
            "",
            "LEGACY UNIT DISTRIBUTION",
            "-" * 80,
        ]
        
        for unit, count in sorted(analysis['legacy_unit_distribution'].items(), 
                                 key=lambda x: x[1], reverse=True):
            report_lines.append(f"  {unit}: {count} works")
        
        report_lines.extend([
            "",
            "MATCHING ANALYSIS",
            "-" * 80,
            f"Total works analyzed: {matches['summary']['total_works_analyzed']}",
            f"Exact matches: {matches['summary']['exact_match_count']}",
            f"Fuzzy matches: {matches['summary']['fuzzy_match_count']}",
            f"No matches: {matches['summary']['no_match_count']}",
            f"Ready for auto-migration: {matches['summary']['auto_migration_ready']}",
            f"Requiring manual review: {matches['summary']['manual_review_required']}",
            "",
        ])
        
        if matches['exact_matches']:
            report_lines.extend([
                "EXACT MATCHES (Sample - first 10)",
                "-" * 80,
            ])
            for match in matches['exact_matches'][:10]:
                report_lines.append(
                    f"  Work #{match['work_id']}: '{match['legacy_unit']}' -> "
                    f"Unit #{match['matched_unit_id']} '{match['matched_unit_name']}'"
                )
            if len(matches['exact_matches']) > 10:
                report_lines.append(f"  ... and {len(matches['exact_matches']) - 10} more")
            report_lines.append("")
        
        if matches['fuzzy_matches']:
            report_lines.extend([
                "FUZZY MATCHES (Sample - first 10)",
                "-" * 80,
            ])
            for match in matches['fuzzy_matches'][:10]:
                report_lines.append(
                    f"  Work #{match['work_id']}: '{match['legacy_unit']}' -> "
                    f"Unit #{match['matched_unit_id']} '{match['matched_unit_name']}' "
                    f"(confidence: {match['confidence']})"
                )
            if len(matches['fuzzy_matches']) > 10:
                report_lines.append(f"  ... and {len(matches['fuzzy_matches']) - 10} more")
            report_lines.append("")
        
        if matches['no_matches']:
            report_lines.extend([
                "NO MATCHES - MANUAL REVIEW REQUIRED",
                "-" * 80,
            ])
            for no_match in matches['no_matches'][:20]:
                report_lines.append(
                    f"  Work #{no_match['work_id']}: '{no_match['legacy_unit']}' - "
                    f"{no_match['reason']}"
                )
            if len(matches['no_matches']) > 20:
                report_lines.append(f"  ... and {len(matches['no_matches']) - 20} more")
            report_lines.append("")
        
        if conflicts:
            report_lines.extend([
                "CONFLICTS DETECTED",
                "-" * 80,
            ])
            for conflict in conflicts[:10]:
                report_lines.append(
                    f"  Work #{conflict['work_id']}: Legacy='{conflict['legacy_unit']}' vs "
                    f"Unit_ID={conflict['unit_id']} ('{conflict['unit_name']}')"
                )
            if len(conflicts) > 10:
                report_lines.append(f"  ... and {len(conflicts) - 10} more")
            report_lines.append("")
        
        report_lines.extend([
            "RECOMMENDATIONS",
            "-" * 80,
            f"1. Auto-migrate {matches['summary']['auto_migration_ready']} works with high-confidence matches",
            f"2. Manually review {matches['summary']['manual_review_required']} works with no matches",
            f"3. Resolve {len(conflicts)} conflicts before proceeding",
            "",
            "=" * 80,
        ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")
        
        return report


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze work unit migration')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--threshold', '-t', type=float, default=0.8,
                       help='Fuzzy matching threshold (0.0-1.0, default: 0.8)')
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = DatabaseManager()
    db_manager.initialize()
    
    # Create analyzer
    analyzer = WorkUnitAnalyzer(db_manager)
    
    # Generate and display report
    report = analyzer.generate_report(args.output)
    print(report)


if __name__ == '__main__':
    main()