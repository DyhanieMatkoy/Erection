#!/usr/bin/env python3
"""
UUID Impact Assessment Tools

This module provides tools to analyze the impact of migrating works table
from integer IDs to UUIDs, including assessment of all foreign key relationships
and estimation of migration complexity.
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from sqlalchemy import inspect, MetaData, Table, ForeignKey, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.database_manager import DatabaseManager
from src.data.models.sqlalchemy_models import Base, Work


@dataclass
class ForeignKeyRelationship:
    """Represents a foreign key relationship to the works table"""
    table_name: str
    column_name: str
    constraint_name: str
    is_nullable: bool
    record_count: int
    has_cascade_delete: bool
    relationship_type: str  # 'one_to_many', 'many_to_one', 'many_to_many'


@dataclass
class UUIDMigrationComplexity:
    """Represents the complexity assessment for UUID migration"""
    total_tables_affected: int
    total_foreign_keys: int
    total_records_to_update: int
    estimated_migration_time_minutes: int
    risk_level: str  # 'low', 'medium', 'high'
    critical_dependencies: List[str]
    migration_phases: List[str]


@dataclass
class UUIDImpactReport:
    """Complete UUID impact assessment report"""
    assessment_date: str
    database_type: str
    works_table_record_count: int
    foreign_key_relationships: List[ForeignKeyRelationship]
    migration_complexity: UUIDMigrationComplexity
    recommendations: List[str]
    migration_strategy: str


class UUIDImpactAssessment:
    """Main class for UUID impact assessment"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = db_manager.get_session()
        self.engine = db_manager.get_engine()
        self.metadata = MetaData()
        self.metadata.reflect(bind=self.engine)
    
    def analyze_foreign_key_relationships(self) -> List[ForeignKeyRelationship]:
        """Analyze all foreign key relationships to the works table"""
        relationships = []
        
        # Get the works table
        works_table = self.metadata.tables.get('works')
        if works_table is None:
            raise ValueError("Works table not found in database")
        
        # Find all tables that reference works table
        for table_name, table in self.metadata.tables.items():
            for column in table.columns:
                for fk in column.foreign_keys:
                    if fk.column.table.name == 'works':
                        # Count records in this table
                        record_count = self.session.execute(
                            text(f"SELECT COUNT(*) FROM {table_name}")
                        ).scalar()
                        
                        # Check if column is nullable
                        is_nullable = column.nullable
                        
                        # Check for cascade delete
                        has_cascade_delete = 'CASCADE' in str(fk.ondelete).upper() if fk.ondelete else False
                        
                        # Determine relationship type
                        relationship_type = self._determine_relationship_type(table_name, column.name)
                        
                        relationships.append(ForeignKeyRelationship(
                            table_name=table_name,
                            column_name=column.name,
                            constraint_name=fk.constraint.name if fk.constraint else f"fk_{table_name}_{column.name}",
                            is_nullable=is_nullable,
                            record_count=record_count,
                            has_cascade_delete=has_cascade_delete,
                            relationship_type=relationship_type
                        ))
        
        return relationships
    
    def _determine_relationship_type(self, table_name: str, column_name: str) -> str:
        """Determine the type of relationship based on table and column names"""
        # Known relationship patterns
        if table_name == 'works' and column_name == 'parent_id':
            return 'self_referential'
        elif column_name.endswith('_id') and 'work' in column_name:
            return 'many_to_one'
        elif table_name.endswith('_lines') or 'register' in table_name:
            return 'one_to_many'
        elif 'association' in table_name or 'materials' in table_name:
            return 'many_to_many'
        else:
            return 'one_to_many'
    
    def assess_migration_complexity(self, relationships: List[ForeignKeyRelationship]) -> UUIDMigrationComplexity:
        """Assess the complexity of UUID migration"""
        
        # Count works records
        works_count = self.session.query(Work).count()
        
        # Calculate totals
        total_tables = len(set(rel.table_name for rel in relationships))
        total_foreign_keys = len(relationships)
        total_records = sum(rel.record_count for rel in relationships)
        
        # Identify critical dependencies
        critical_deps = []
        for rel in relationships:
            if rel.record_count > 10000:
                critical_deps.append(f"{rel.table_name} ({rel.record_count:,} records)")
            elif not rel.is_nullable:
                critical_deps.append(f"{rel.table_name} (non-nullable FK)")
        
        # Estimate migration time (rough calculation)
        # Base time: 5 minutes setup + 1 minute per 1000 records + complexity factors
        base_time = 5
        record_time = max(1, total_records // 1000)
        complexity_factor = len(critical_deps) * 2
        estimated_time = base_time + record_time + complexity_factor
        
        # Determine risk level
        if total_records > 100000 or len(critical_deps) > 5:
            risk_level = 'high'
        elif total_records > 10000 or len(critical_deps) > 2:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Define migration phases
        phases = [
            "Phase 1: Add UUID columns to all affected tables",
            "Phase 2: Generate UUIDs for existing works records",
            "Phase 3: Update foreign key references to use UUIDs",
            "Phase 4: Add UUID-based constraints and indexes",
            "Phase 5: Update application code to use UUIDs",
            "Phase 6: Remove integer ID columns (optional)"
        ]
        
        return UUIDMigrationComplexity(
            total_tables_affected=total_tables,
            total_foreign_keys=total_foreign_keys,
            total_records_to_update=total_records,
            estimated_migration_time_minutes=estimated_time,
            risk_level=risk_level,
            critical_dependencies=critical_deps,
            migration_phases=phases
        )
    
    def generate_recommendations(self, complexity: UUIDMigrationComplexity) -> List[str]:
        """Generate recommendations based on complexity assessment"""
        recommendations = []
        
        if complexity.risk_level == 'high':
            recommendations.extend([
                "Consider phased migration approach with extensive testing",
                "Implement comprehensive backup and rollback procedures",
                "Plan for extended maintenance window",
                "Consider blue-green deployment strategy"
            ])
        elif complexity.risk_level == 'medium':
            recommendations.extend([
                "Implement thorough testing in staging environment",
                "Plan for maintenance window during low-usage period",
                "Prepare rollback procedures"
            ])
        else:
            recommendations.extend([
                "Migration can be performed with standard procedures",
                "Minimal downtime expected"
            ])
        
        # General recommendations
        recommendations.extend([
            "Add UUID columns before migration to minimize downtime",
            "Use batch processing for large table updates",
            "Implement UUID validation at application level",
            "Consider keeping integer IDs for backward compatibility initially",
            "Update all API endpoints to support UUID lookups",
            "Implement UUID-based synchronization logic"
        ])
        
        return recommendations
    
    def determine_migration_strategy(self, complexity: UUIDMigrationComplexity) -> str:
        """Determine the recommended migration strategy"""
        if complexity.risk_level == 'high':
            return "phased_migration_with_dual_keys"
        elif complexity.risk_level == 'medium':
            return "staged_migration_with_validation"
        else:
            return "direct_migration_with_backup"
    
    def generate_impact_report(self) -> UUIDImpactReport:
        """Generate complete UUID impact assessment report"""
        
        # Analyze relationships
        relationships = self.analyze_foreign_key_relationships()
        
        # Assess complexity
        complexity = self.assess_migration_complexity(relationships)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(complexity)
        
        # Determine strategy
        strategy = self.determine_migration_strategy(complexity)
        
        # Count works records
        works_count = self.session.query(Work).count()
        
        # Get database type from engine URL
        db_type = "unknown"
        try:
            engine_url = str(self.engine.url)
            if engine_url.startswith('sqlite'):
                db_type = "sqlite"
            elif engine_url.startswith('postgresql'):
                db_type = "postgresql"
            elif engine_url.startswith('mssql'):
                db_type = "mssql"
        except:
            db_type = "unknown"
        
        return UUIDImpactReport(
            assessment_date=datetime.now().isoformat(),
            database_type=db_type,
            works_table_record_count=works_count,
            foreign_key_relationships=relationships,
            migration_complexity=complexity,
            recommendations=recommendations,
            migration_strategy=strategy
        )
    
    def save_report_to_file(self, report: UUIDImpactReport, filename: str = None) -> str:
        """Save the impact report to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uuid_impact_assessment_{timestamp}.json"
        
        filepath = os.path.join("migration_results", filename)
        os.makedirs("migration_results", exist_ok=True)
        
        # Convert to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def print_summary_report(self, report: UUIDImpactReport):
        """Print a human-readable summary of the impact report"""
        print("\n" + "="*80)
        print("UUID MIGRATION IMPACT ASSESSMENT REPORT")
        print("="*80)
        print(f"Assessment Date: {report.assessment_date}")
        print(f"Database Type: {report.database_type}")
        print(f"Works Records: {report.works_table_record_count:,}")
        print()
        
        print("FOREIGN KEY RELATIONSHIPS:")
        print("-" * 40)
        for rel in report.foreign_key_relationships:
            nullable_str = "nullable" if rel.is_nullable else "NOT NULL"
            cascade_str = "CASCADE" if rel.has_cascade_delete else "NO CASCADE"
            print(f"  {rel.table_name}.{rel.column_name}")
            print(f"    Records: {rel.record_count:,} | {nullable_str} | {cascade_str}")
            print(f"    Type: {rel.relationship_type}")
            print()
        
        print("MIGRATION COMPLEXITY:")
        print("-" * 40)
        complexity = report.migration_complexity
        print(f"  Tables Affected: {complexity.total_tables_affected}")
        print(f"  Foreign Keys: {complexity.total_foreign_keys}")
        print(f"  Records to Update: {complexity.total_records_to_update:,}")
        print(f"  Estimated Time: {complexity.estimated_migration_time_minutes} minutes")
        print(f"  Risk Level: {complexity.risk_level.upper()}")
        print()
        
        if complexity.critical_dependencies:
            print("CRITICAL DEPENDENCIES:")
            print("-" * 40)
            for dep in complexity.critical_dependencies:
                print(f"  • {dep}")
            print()
        
        print("MIGRATION STRATEGY:")
        print("-" * 40)
        print(f"  Recommended: {report.migration_strategy}")
        print()
        
        print("RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
        print()
        
        print("MIGRATION PHASES:")
        print("-" * 40)
        for phase in complexity.migration_phases:
            print(f"  • {phase}")
        print()


def main():
    """Main function to run UUID impact assessment"""
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        # Create assessment tool
        assessment = UUIDImpactAssessment(db_manager)
        
        # Generate report
        print("Analyzing UUID migration impact...")
        report = assessment.generate_impact_report()
        
        # Save to file
        filepath = assessment.save_report_to_file(report)
        print(f"Report saved to: {filepath}")
        
        # Print summary
        assessment.print_summary_report(report)
        
        return report
        
    except Exception as e:
        print(f"Error during UUID impact assessment: {e}")
        raise


if __name__ == "__main__":
    main()