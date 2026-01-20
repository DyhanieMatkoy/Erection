"""Data Verification Engine

This module provides comprehensive data verification functionality for the sync end-to-end testing system.
It verifies document propagation, content consistency, and data integrity across all desktop clients.
"""

import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timezone
from dataclasses import dataclass, asdict


@dataclass
class DocumentVerification:
    """Result of document verification"""
    document_id: str
    document_type: str
    document_number: str
    client_id: str
    exists: bool
    content_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    verification_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyCheck:
    """Result of consistency check"""
    check_type: str
    check_name: str
    passed: bool
    details: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationReport:
    """Comprehensive verification report"""
    total_documents: int
    verified_documents: int
    missing_documents: int
    consistency_checks_passed: int
    total_consistency_checks: int
    data_integrity_score: int
    verification_time: str
    details: List[Dict[str, Any]]
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseQueryUtilities:
    """Utilities for querying database content"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize database query utilities
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def get_document_by_number(self, 
                              db_manager,
                              doc_type: str,
                              doc_number: str) -> Optional[Dict[str, Any]]:
        """Get document by number from database
        
        Args:
            db_manager: Database manager instance
            doc_type: Document type (estimate, daily_report, timesheet)
            doc_number: Document number
            
        Returns:
            Document data or None if not found
        """
        try:
            table_map = {
                'estimate': 'estimates',
                'daily_report': 'daily_reports',
                'timesheet': 'timesheets'
            }
            
            table_name = table_map.get(doc_type)
            if not table_name:
                raise ValueError(f"Unknown document type: {doc_type}")
            
            query = f"SELECT * FROM {table_name} WHERE number = ?"
            results = db_manager.execute_query(query, (doc_number,))
            
            if results:
                return dict(results[0])
            return None
            
        except Exception as e:
            self.logger.error(f"Error querying document {doc_number}: {e}")
            return None
    
    def get_document_lines(self,
                          db_manager,
                          doc_type: str,
                          doc_id: int) -> List[Dict[str, Any]]:
        """Get document lines from database
        
        Args:
            db_manager: Database manager instance
            doc_type: Document type
            doc_id: Document ID
            
        Returns:
            List of document lines
        """
        try:
            table_map = {
                'estimate': 'estimate_lines',
                'daily_report': 'daily_report_lines',
                'timesheet': 'timesheet_lines'
            }
            
            table_name = table_map.get(doc_type)
            if not table_name:
                return []
            
            id_field_map = {
                'estimate': 'estimate_id',
                'daily_report': 'report_id',
                'timesheet': 'timesheet_id'
            }
            
            id_field = id_field_map.get(doc_type)
            if not id_field:
                return []
            
            query = f"SELECT * FROM {table_name} WHERE {id_field} = ? ORDER BY line_number"
            results = db_manager.execute_query(query, (doc_id,))
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error querying document lines for {doc_id}: {e}")
            return []
    
    def get_all_documents(self, db_manager, doc_type: str) -> List[Dict[str, Any]]:
        """Get all documents of a specific type
        
        Args:
            db_manager: Database manager instance
            doc_type: Document type
            
        Returns:
            List of all documents
        """
        try:
            table_map = {
                'estimate': 'estimates',
                'daily_report': 'daily_reports',
                'timesheet': 'timesheets'
            }
            
            table_name = table_map.get(doc_type)
            if not table_name:
                return []
            
            query = f"SELECT * FROM {table_name} ORDER BY id"
            results = db_manager.execute_query(query)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error querying all {doc_type} documents: {e}")
            return []
    
    def get_database_statistics(self, db_manager) -> Dict[str, Any]:
        """Get database statistics
        
        Args:
            db_manager: Database manager instance
            
        Returns:
            Database statistics
        """
        try:
            stats = {}
            
            # Document counts
            document_tables = ['estimates', 'daily_reports', 'timesheets']
            for table in document_tables:
                try:
                    query = f"SELECT COUNT(*) as count FROM {table}"
                    result = db_manager.execute_query(query)
                    stats[f"{table}_count"] = result[0]['count'] if result else 0
                except Exception as e:
                    self.logger.warning(f"Error counting {table}: {e}")
                    stats[f"{table}_count"] = 0
            
            # Reference data counts
            reference_tables = ['counterparties', 'objects', 'organizations', 'persons', 'works']
            for table in reference_tables:
                try:
                    query = f"SELECT COUNT(*) as count FROM {table}"
                    result = db_manager.execute_query(query)
                    stats[f"{table}_count"] = result[0]['count'] if result else 0
                except Exception as e:
                    self.logger.warning(f"Error counting {table}: {e}")
                    stats[f"{table}_count"] = 0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database statistics: {e}")
            return {}


class ContentComparisonEngine:
    """Engine for comparing document content across clients"""
    
    def __init__(self, logger: logging.Logger):
        """Initialize content comparison engine
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def calculate_content_hash(self, content: Dict[str, Any]) -> str:
        """Calculate hash of document content
        
        Args:
            content: Document content dictionary
            
        Returns:
            Content hash string
        """
        try:
            # Create normalized content for hashing
            normalized_content = self._normalize_content_for_hash(content)
            
            # Convert to JSON string with sorted keys
            content_json = json.dumps(normalized_content, sort_keys=True, ensure_ascii=False)
            
            # Calculate SHA-256 hash
            return hashlib.sha256(content_json.encode('utf-8')).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating content hash: {e}")
            return "error"
    
    def _normalize_content_for_hash(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize content for consistent hashing
        
        Args:
            content: Original content
            
        Returns:
            Normalized content
        """
        normalized = {}
        
        # Skip fields that may vary between clients
        skip_fields = {
            'id', 'created_at', 'modified_at', 'posted_at'
        }
        
        for key, value in content.items():
            if key not in skip_fields:
                if isinstance(value, float):
                    # Round floats to avoid precision differences
                    normalized[key] = round(value, 6)
                elif isinstance(value, str) and value:
                    # Normalize string whitespace
                    normalized[key] = value.strip()
                else:
                    normalized[key] = value
        
        return normalized
    
    def compare_documents(self, 
                         doc1: Dict[str, Any],
                         doc2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two documents for consistency
        
        Args:
            doc1: First document
            doc2: Second document
            
        Returns:
            Comparison result
        """
        try:
            # Calculate hashes
            hash1 = self.calculate_content_hash(doc1)
            hash2 = self.calculate_content_hash(doc2)
            
            # Basic comparison
            comparison = {
                'identical': hash1 == hash2,
                'hash1': hash1,
                'hash2': hash2,
                'differences': []
            }
            
            if not comparison['identical']:
                # Find specific differences
                comparison['differences'] = self._find_differences(doc1, doc2)
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing documents: {e}")
            return {
                'identical': False,
                'error': str(e)
            }
    
    def _find_differences(self, 
                         doc1: Dict[str, Any],
                         doc2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find specific differences between documents
        
        Args:
            doc1: First document
            doc2: Second document
            
        Returns:
            List of differences
        """
        differences = []
        
        # Normalize both documents
        norm1 = self._normalize_content_for_hash(doc1)
        norm2 = self._normalize_content_for_hash(doc2)
        
        # Find all keys
        all_keys = set(norm1.keys()) | set(norm2.keys())
        
        for key in all_keys:
            val1 = norm1.get(key)
            val2 = norm2.get(key)
            
            if val1 != val2:
                differences.append({
                    'field': key,
                    'value1': val1,
                    'value2': val2,
                    'type': 'value_difference'
                })
        
        return differences


class DataVerificationEngine:
    """Main engine for data verification across desktop clients"""
    
    def __init__(self,
                 desktop_clients: List,
                 expected_documents: List[Dict[str, Any]],
                 logger: logging.Logger):
        """Initialize data verification engine
        
        Args:
            desktop_clients: List of TestDesktopClient instances
            expected_documents: List of expected document information
            logger: Logger instance
        """
        self.desktop_clients = desktop_clients
        self.expected_documents = expected_documents
        self.logger = logger
        
        # Initialize components
        self.db_utils = DatabaseQueryUtilities(logger)
        self.content_engine = ContentComparisonEngine(logger)
        
        # Verification results
        self.document_verifications: List[DocumentVerification] = []
        self.consistency_checks: List[ConsistencyCheck] = []
        
        self.logger.info(f"Data verification engine initialized for {len(desktop_clients)} clients")
    
    def verify_document_propagation(self) -> Dict[str, Any]:
        """Verify that all expected documents exist in all client databases
        
        Returns:
            Document propagation verification results
        """
        try:
            self.logger.info("Starting document propagation verification")
            
            verification_results = {
                'success': True,
                'total_documents': len(self.expected_documents),
                'total_clients': len(self.desktop_clients),
                'expected_verifications': len(self.expected_documents) * len(self.desktop_clients),
                'successful_verifications': 0,
                'failed_verifications': 0,
                'missing_documents': [],
                'verification_details': [],
                'passed_checks': 0,
                'total_checks': 0
            }
            
            # Verify each expected document in each client
            for expected_doc in self.expected_documents:
                doc_type = expected_doc['type']
                doc_number = expected_doc.get('document_number') or expected_doc.get('document_id')
                
                for client in self.desktop_clients:
                    verification_results['total_checks'] += 1
                    
                    try:
                        # Query document in client database
                        document = self.db_utils.get_document_by_number(
                            client.db_manager, doc_type, doc_number
                        )
                        
                        if document:
                            # Document found
                            doc_verification = DocumentVerification(
                                document_id=str(document.get('id', 'unknown')),
                                document_type=doc_type,
                                document_number=doc_number,
                                client_id=client.client_id,
                                exists=True,
                                content_hash=self.content_engine.calculate_content_hash(document),
                                metadata={
                                    'created_at': document.get('created_at'),
                                    'modified_at': document.get('modified_at'),
                                    'total_sum': document.get('total_sum'),
                                    'total_labor': document.get('total_labor')
                                },
                                verification_time=datetime.now(timezone.utc).isoformat()
                            )
                            
                            self.document_verifications.append(doc_verification)
                            verification_results['successful_verifications'] += 1
                            verification_results['passed_checks'] += 1
                            
                            verification_results['verification_details'].append({
                                'document': doc_number,
                                'client': client.client_id,
                                'status': 'found',
                                'hash': doc_verification.content_hash
                            })
                            
                        else:
                            # Document not found
                            doc_verification = DocumentVerification(
                                document_id='not_found',
                                document_type=doc_type,
                                document_number=doc_number,
                                client_id=client.client_id,
                                exists=False,
                                verification_time=datetime.now(timezone.utc).isoformat()
                            )
                            
                            self.document_verifications.append(doc_verification)
                            verification_results['failed_verifications'] += 1
                            verification_results['success'] = False
                            
                            verification_results['missing_documents'].append({
                                'document': doc_number,
                                'type': doc_type,
                                'client': client.client_id
                            })
                            
                            verification_results['verification_details'].append({
                                'document': doc_number,
                                'client': client.client_id,
                                'status': 'missing'
                            })
                            
                    except Exception as e:
                        self.logger.error(f"Error verifying document {doc_number} in {client.client_id}: {e}")
                        verification_results['failed_verifications'] += 1
                        verification_results['success'] = False
                        
                        verification_results['verification_details'].append({
                            'document': doc_number,
                            'client': client.client_id,
                            'status': 'error',
                            'error': str(e)
                        })
            
            self.logger.info(f"Document propagation verification completed: "
                           f"{verification_results['successful_verifications']}/{verification_results['expected_verifications']} successful")
            
            return verification_results
            
        except Exception as e:
            self.logger.error(f"Document propagation verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_content_consistency(self) -> Dict[str, Any]:
        """Verify content consistency across all clients
        
        Returns:
            Content consistency verification results
        """
        try:
            self.logger.info("Starting content consistency verification")
            
            consistency_results = {
                'success': True,
                'total_documents': len(self.expected_documents),
                'consistent_documents': 0,
                'inconsistent_documents': 0,
                'consistency_details': [],
                'passed_checks': 0,
                'total_checks': 0
            }
            
            # Group verifications by document
            doc_verifications = {}
            for verification in self.document_verifications:
                if verification.exists:
                    doc_key = f"{verification.document_type}:{verification.document_number}"
                    if doc_key not in doc_verifications:
                        doc_verifications[doc_key] = []
                    doc_verifications[doc_key].append(verification)
            
            # Check consistency for each document
            for doc_key, verifications in doc_verifications.items():
                consistency_results['total_checks'] += 1
                
                if len(verifications) < 2:
                    # Need at least 2 verifications to check consistency
                    continue
                
                # Compare all pairs of verifications
                hashes = [v.content_hash for v in verifications]
                unique_hashes = set(hashes)
                
                if len(unique_hashes) == 1:
                    # All hashes are the same - consistent
                    consistency_results['consistent_documents'] += 1
                    consistency_results['passed_checks'] += 1
                    
                    consistency_results['consistency_details'].append({
                        'document': doc_key,
                        'status': 'consistent',
                        'clients': [v.client_id for v in verifications],
                        'hash': hashes[0]
                    })
                    
                else:
                    # Different hashes - inconsistent
                    consistency_results['inconsistent_documents'] += 1
                    consistency_results['success'] = False
                    
                    consistency_results['consistency_details'].append({
                        'document': doc_key,
                        'status': 'inconsistent',
                        'clients': [v.client_id for v in verifications],
                        'hashes': {v.client_id: v.content_hash for v in verifications}
                    })
            
            self.logger.info(f"Content consistency verification completed: "
                           f"{consistency_results['consistent_documents']} consistent, "
                           f"{consistency_results['inconsistent_documents']} inconsistent")
            
            return consistency_results
            
        except Exception as e:
            self.logger.error(f"Content consistency verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_no_duplicates(self) -> Dict[str, Any]:
        """Verify that no duplicate documents exist
        
        Returns:
            Duplicate verification results
        """
        try:
            self.logger.info("Starting duplicate verification")
            
            duplicate_results = {
                'success': True,
                'total_clients': len(self.desktop_clients),
                'clients_with_duplicates': 0,
                'duplicate_details': [],
                'passed_checks': 0,
                'total_checks': 0
            }
            
            # Check each client for duplicates
            for client in self.desktop_clients:
                duplicate_results['total_checks'] += 1
                
                try:
                    client_duplicates = self._find_duplicates_in_client(client)
                    
                    if client_duplicates:
                        duplicate_results['clients_with_duplicates'] += 1
                        duplicate_results['success'] = False
                        
                        duplicate_results['duplicate_details'].append({
                            'client': client.client_id,
                            'duplicates': client_duplicates
                        })
                    else:
                        duplicate_results['passed_checks'] += 1
                        
                        duplicate_results['duplicate_details'].append({
                            'client': client.client_id,
                            'status': 'no_duplicates'
                        })
                        
                except Exception as e:
                    self.logger.error(f"Error checking duplicates in {client.client_id}: {e}")
                    duplicate_results['success'] = False
                    
                    duplicate_results['duplicate_details'].append({
                        'client': client.client_id,
                        'status': 'error',
                        'error': str(e)
                    })
            
            self.logger.info(f"Duplicate verification completed: "
                           f"{duplicate_results['clients_with_duplicates']} clients with duplicates")
            
            return duplicate_results
            
        except Exception as e:
            self.logger.error(f"Duplicate verification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_duplicates_in_client(self, client) -> List[Dict[str, Any]]:
        """Find duplicate documents in a client database
        
        Args:
            client: TestDesktopClient instance
            
        Returns:
            List of duplicate document information
        """
        duplicates = []
        
        try:
            # Check each document type
            document_types = ['estimate', 'daily_report', 'timesheet']
            
            for doc_type in document_types:
                documents = self.db_utils.get_all_documents(client.db_manager, doc_type)
                
                # Group by document number
                doc_groups = {}
                for doc in documents:
                    doc_number = doc.get('number', '')
                    if doc_number:
                        if doc_number not in doc_groups:
                            doc_groups[doc_number] = []
                        doc_groups[doc_number].append(doc)
                
                # Find groups with more than one document
                for doc_number, docs in doc_groups.items():
                    if len(docs) > 1:
                        duplicates.append({
                            'type': doc_type,
                            'number': doc_number,
                            'count': len(docs),
                            'ids': [doc.get('id') for doc in docs]
                        })
            
        except Exception as e:
            self.logger.error(f"Error finding duplicates in {client.client_id}: {e}")
        
        return duplicates
    
    def generate_verification_report(self) -> VerificationReport:
        """Generate comprehensive verification report
        
        Returns:
            Complete verification report
        """
        try:
            # Run all verifications
            propagation_results = self.verify_document_propagation()
            consistency_results = self.verify_content_consistency()
            duplicate_results = self.verify_no_duplicates()
            
            # Calculate totals
            total_checks = (
                propagation_results.get('total_checks', 0) +
                consistency_results.get('total_checks', 0) +
                duplicate_results.get('total_checks', 0)
            )
            
            passed_checks = (
                propagation_results.get('passed_checks', 0) +
                consistency_results.get('passed_checks', 0) +
                duplicate_results.get('passed_checks', 0)
            )
            
            # Calculate integrity score
            integrity_score = int((passed_checks / total_checks * 100)) if total_checks > 0 else 0
            
            # Collect all details
            all_details = []
            all_details.extend(propagation_results.get('verification_details', []))
            all_details.extend(consistency_results.get('consistency_details', []))
            all_details.extend(duplicate_results.get('duplicate_details', []))
            
            # Collect errors
            errors = []
            if not propagation_results.get('success', True):
                errors.append("Document propagation verification failed")
            if not consistency_results.get('success', True):
                errors.append("Content consistency verification failed")
            if not duplicate_results.get('success', True):
                errors.append("Duplicate verification failed")
            
            report = VerificationReport(
                total_documents=len(self.expected_documents),
                verified_documents=propagation_results.get('successful_verifications', 0),
                missing_documents=propagation_results.get('failed_verifications', 0),
                consistency_checks_passed=passed_checks,
                total_consistency_checks=total_checks,
                data_integrity_score=integrity_score,
                verification_time=datetime.now(timezone.utc).isoformat(),
                details=all_details,
                errors=errors
            )
            
            self.logger.info(f"Verification report generated: {integrity_score}% integrity score")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate verification report: {e}")
            return VerificationReport(
                total_documents=0,
                verified_documents=0,
                missing_documents=0,
                consistency_checks_passed=0,
                total_consistency_checks=0,
                data_integrity_score=0,
                verification_time=datetime.now(timezone.utc).isoformat(),
                details=[],
                errors=[str(e)]
            )
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of verification results
        
        Returns:
            Verification summary
        """
        report = self.generate_verification_report()
        
        return {
            'data_integrity_score': report.data_integrity_score,
            'total_documents': report.total_documents,
            'verified_documents': report.verified_documents,
            'missing_documents': report.missing_documents,
            'consistency_checks_passed': report.consistency_checks_passed,
            'total_consistency_checks': report.total_consistency_checks,
            'has_errors': len(report.errors) > 0,
            'error_count': len(report.errors)
        }