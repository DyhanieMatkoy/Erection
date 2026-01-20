"""Test Report Generation Framework

This module provides comprehensive test report generation for the sync end-to-end testing system.
It supports multiple output formats including JSON, HTML, and plain text reports.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from jinja2 import Template


@dataclass
class TestPhaseResult:
    """Result of a test phase"""
    name: str
    status: str  # PASSED, FAILED, SKIPPED
    duration: float
    start_time: str
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentInfo:
    """Information about a test document"""
    type: str
    client_id: str
    document_id: str
    created_at: str
    sync_status: str = "unknown"
    verification_status: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    """Result of data verification"""
    total_documents: int
    verified_documents: int
    missing_documents: int
    consistency_checks_passed: int
    total_consistency_checks: int
    data_integrity_score: int
    details: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """Performance metrics summary"""
    total_sync_operations: int
    successful_syncs: int
    failed_syncs: int
    average_sync_duration: float
    min_sync_duration: float
    max_sync_duration: float
    total_data_transferred: int
    sync_success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TestReport:
    """Complete test report"""
    test_id: str
    test_name: str
    start_time: str
    end_time: str
    total_duration: float
    status: str  # PASSED, FAILED, PARTIAL
    
    # Configuration
    config: Dict[str, Any]
    
    # Results
    phases: List[TestPhaseResult]
    documents: List[DocumentInfo]
    verification: VerificationResult
    performance: PerformanceMetrics
    
    # Additional data
    errors: List[str]
    warnings: List[str]
    log_files: Dict[str, str]
    archived_databases: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TestReportGenerator:
    """Generates comprehensive test reports in multiple formats"""
    
    def __init__(self, test_id: str, config: Dict[str, Any]):
        """Initialize report generator
        
        Args:
            test_id: Unique test identifier
            config: Test configuration
        """
        self.test_id = test_id
        self.config = config
        
        # Create reports directory
        self.reports_dir = Path("test_reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Report data
        self.test_name = f"Sync End-to-End Test {test_id}"
        self.start_time = datetime.now(timezone.utc)
        self.phases: List[TestPhaseResult] = []
        self.documents: List[DocumentInfo] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.log_files: Dict[str, str] = {}
        
        # Performance tracking
        self.sync_operations: List[Dict[str, Any]] = []
        self.verification_results: Optional[VerificationResult] = None
    
    def add_phase_result(self, 
                        phase_name: str,
                        status: str,
                        duration: float,
                        start_time: datetime,
                        error: Optional[str] = None,
                        details: Optional[Dict[str, Any]] = None):
        """Add a test phase result
        
        Args:
            phase_name: Name of the test phase
            status: Phase status (PASSED, FAILED, SKIPPED)
            duration: Phase duration in seconds
            start_time: Phase start time
            error: Optional error message
            details: Optional additional details
        """
        phase_result = TestPhaseResult(
            name=phase_name,
            status=status,
            duration=duration,
            start_time=start_time.isoformat(),
            error=error,
            details=details
        )
        
        self.phases.append(phase_result)
    
    def add_document(self,
                    doc_type: str,
                    client_id: str,
                    document_id: str,
                    created_at: str,
                    sync_status: str = "unknown",
                    verification_status: str = "unknown"):
        """Add document information
        
        Args:
            doc_type: Type of document
            client_id: Client that created the document
            document_id: Document identifier
            created_at: Creation timestamp
            sync_status: Synchronization status
            verification_status: Verification status
        """
        document = DocumentInfo(
            type=doc_type,
            client_id=client_id,
            document_id=document_id,
            created_at=created_at,
            sync_status=sync_status,
            verification_status=verification_status
        )
        
        self.documents.append(document)
    
    def add_sync_operation(self, operation_result: Dict[str, Any]):
        """Add sync operation result
        
        Args:
            operation_result: Sync operation result dictionary
        """
        self.sync_operations.append(operation_result)
    
    def set_verification_results(self, verification_result: VerificationResult):
        """Set verification results
        
        Args:
            verification_result: Verification results
        """
        self.verification_results = verification_result
    
    def add_error(self, error: str):
        """Add error message
        
        Args:
            error: Error message
        """
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add warning message
        
        Args:
            warning: Warning message
        """
        self.warnings.append(warning)
    
    def set_log_files(self, log_files: Dict[str, str]):
        """Set log file paths
        
        Args:
            log_files: Dictionary of log file paths
        """
        self.log_files = log_files
    
    def generate_report(self, 
                       output_file: Optional[str] = None,
                       formats: List[str] = None) -> Dict[str, str]:
        """Generate comprehensive test report
        
        Args:
            output_file: Optional output file path
            formats: List of formats to generate (json, html, txt)
            
        Returns:
            Dictionary of generated file paths
        """
        if formats is None:
            formats = ['json']
        
        # Build complete report
        report = self._build_complete_report()
        
        # Generate reports in requested formats
        generated_files = {}
        
        for format_type in formats:
            if format_type == 'json':
                file_path = self._generate_json_report(report, output_file)
                generated_files['json'] = file_path
            elif format_type == 'html':
                file_path = self._generate_html_report(report, output_file)
                generated_files['html'] = file_path
            elif format_type == 'txt':
                file_path = self._generate_text_report(report, output_file)
                generated_files['txt'] = file_path
        
        return generated_files
    
    def _build_complete_report(self) -> TestReport:
        """Build complete test report
        
        Returns:
            Complete test report
        """
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Determine overall status
        failed_phases = [p for p in self.phases if p.status == 'FAILED']
        if failed_phases:
            if len(failed_phases) == len(self.phases):
                status = 'FAILED'
            else:
                status = 'PARTIAL'
        else:
            status = 'PASSED'
        
        # Build performance metrics
        performance = self._build_performance_metrics()
        
        # Build verification results
        verification = self.verification_results or VerificationResult(
            total_documents=0,
            verified_documents=0,
            missing_documents=0,
            consistency_checks_passed=0,
            total_consistency_checks=0,
            data_integrity_score=0,
            details=[]
        )
        
        return TestReport(
            test_id=self.test_id,
            test_name=self.test_name,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_duration=total_duration,
            status=status,
            config=self.config,
            phases=self.phases,
            documents=self.documents,
            verification=verification,
            performance=performance,
            errors=self.errors,
            warnings=self.warnings,
            log_files=self.log_files
        )
    
    def _build_performance_metrics(self) -> PerformanceMetrics:
        """Build performance metrics summary
        
        Returns:
            Performance metrics
        """
        if not self.sync_operations:
            return PerformanceMetrics(
                total_sync_operations=0,
                successful_syncs=0,
                failed_syncs=0,
                average_sync_duration=0.0,
                min_sync_duration=0.0,
                max_sync_duration=0.0,
                total_data_transferred=0,
                sync_success_rate=0.0
            )
        
        successful_ops = [op for op in self.sync_operations if op.get('status') == 'success']
        failed_ops = [op for op in self.sync_operations if op.get('status') == 'failed']
        
        durations = [op.get('duration', 0) for op in self.sync_operations if op.get('duration')]
        data_sizes = [op.get('data_size', 0) for op in self.sync_operations if op.get('data_size')]
        
        return PerformanceMetrics(
            total_sync_operations=len(self.sync_operations),
            successful_syncs=len(successful_ops),
            failed_syncs=len(failed_ops),
            average_sync_duration=sum(durations) / len(durations) if durations else 0.0,
            min_sync_duration=min(durations) if durations else 0.0,
            max_sync_duration=max(durations) if durations else 0.0,
            total_data_transferred=sum(data_sizes),
            sync_success_rate=(len(successful_ops) / len(self.sync_operations) * 100) if self.sync_operations else 0.0
        )
    
    def _generate_json_report(self, report: TestReport, output_file: Optional[str] = None) -> str:
        """Generate JSON report
        
        Args:
            report: Test report data
            output_file: Optional output file path
            
        Returns:
            Generated file path
        """
        if output_file:
            file_path = output_file
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = str(self.reports_dir / f"sync_test_report_{self.test_id}_{timestamp}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _generate_html_report(self, report: TestReport, output_file: Optional[str] = None) -> str:
        """Generate HTML report
        
        Args:
            report: Test report data
            output_file: Optional output file path
            
        Returns:
            Generated file path
        """
        if output_file:
            file_path = output_file.replace('.json', '.html')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = str(self.reports_dir / f"sync_test_report_{self.test_id}_{timestamp}.html")
        
        html_content = self._generate_html_content(report)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return file_path
    
    def _generate_text_report(self, report: TestReport, output_file: Optional[str] = None) -> str:
        """Generate plain text report
        
        Args:
            report: Test report data
            output_file: Optional output file path
            
        Returns:
            Generated file path
        """
        if output_file:
            file_path = output_file.replace('.json', '.txt')
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = str(self.reports_dir / f"sync_test_report_{self.test_id}_{timestamp}.txt")
        
        text_content = self._generate_text_content(report)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        return file_path
    
    def _generate_html_content(self, report: TestReport) -> str:
        """Generate HTML report content
        
        Args:
            report: Test report data
            
        Returns:
            HTML content string
        """
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report.test_name }} - Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }
        .status-passed { color: #28a745; font-weight: bold; }
        .status-failed { color: #dc3545; font-weight: bold; }
        .status-partial { color: #ffc107; font-weight: bold; }
        .section { margin: 20px 0; }
        .section h2 { color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { color: #666; font-size: 14px; }
        .phase-list { list-style: none; padding: 0; }
        .phase-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; }
        .phase-item.failed { border-left-color: #dc3545; }
        .document-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .document-table th, .document-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .document-table th { background-color: #f2f2f2; }
        .error-list { background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; }
        .warning-list { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ report.test_name }}</h1>
            <p><strong>Test ID:</strong> {{ report.test_id }}</p>
            <p><strong>Status:</strong> <span class="status-{{ report.status.lower() }}">{{ report.status }}</span></p>
            <p><strong>Duration:</strong> {{ "%.2f"|format(report.total_duration) }} seconds</p>
            <p><strong>Start Time:</strong> {{ report.start_time }}</p>
            <p><strong>End Time:</strong> {{ report.end_time }}</p>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{{ report.performance.total_sync_operations }}</div>
                    <div class="metric-label">Total Sync Operations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ report.performance.successful_syncs }}</div>
                    <div class="metric-label">Successful Syncs</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "%.1f"|format(report.performance.sync_success_rate) }}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ "%.2f"|format(report.performance.average_sync_duration) }}s</div>
                    <div class="metric-label">Avg Sync Duration</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ report.verification.data_integrity_score }}%</div>
                    <div class="metric-label">Data Integrity Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{{ report.verification.verified_documents }}/{{ report.verification.total_documents }}</div>
                    <div class="metric-label">Documents Verified</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Test Phases</h2>
            <ul class="phase-list">
                {% for phase in report.phases %}
                <li class="phase-item {{ 'failed' if phase.status == 'FAILED' else '' }}">
                    <strong>{{ phase.name }}</strong> - {{ phase.status }} ({{ "%.2f"|format(phase.duration) }}s)
                    {% if phase.error %}
                    <br><em>Error: {{ phase.error }}</em>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
        </div>

        <div class="section">
            <h2>Documents Created</h2>
            <table class="document-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Client ID</th>
                        <th>Document ID</th>
                        <th>Created At</th>
                        <th>Sync Status</th>
                        <th>Verification Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for doc in report.documents %}
                    <tr>
                        <td>{{ doc.type }}</td>
                        <td>{{ doc.client_id }}</td>
                        <td>{{ doc.document_id }}</td>
                        <td>{{ doc.created_at }}</td>
                        <td>{{ doc.sync_status }}</td>
                        <td>{{ doc.verification_status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        {% if report.errors %}
        <div class="section">
            <h2>Errors</h2>
            <div class="error-list">
                <ul>
                    {% for error in report.errors %}
                    <li>{{ error }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        {% if report.warnings %}
        <div class="section">
            <h2>Warnings</h2>
            <div class="warning-list">
                <ul>
                    {% for warning in report.warnings %}
                    <li>{{ warning }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        <div class="section">
            <h2>Configuration</h2>
            <pre>{{ report.config | tojson(indent=2) }}</pre>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(html_template)
        return template.render(report=report)
    
    def _generate_text_content(self, report: TestReport) -> str:
        """Generate plain text report content
        
        Args:
            report: Test report data
            
        Returns:
            Text content string
        """
        lines = [
            "=" * 80,
            f"SYNC END-TO-END TEST REPORT",
            "=" * 80,
            f"Test ID: {report.test_id}",
            f"Test Name: {report.test_name}",
            f"Status: {report.status}",
            f"Duration: {report.total_duration:.2f} seconds",
            f"Start Time: {report.start_time}",
            f"End Time: {report.end_time}",
            "",
            "PERFORMANCE METRICS",
            "-" * 40,
            f"Total Sync Operations: {report.performance.total_sync_operations}",
            f"Successful Syncs: {report.performance.successful_syncs}",
            f"Failed Syncs: {report.performance.failed_syncs}",
            f"Success Rate: {report.performance.sync_success_rate:.1f}%",
            f"Average Sync Duration: {report.performance.average_sync_duration:.2f}s",
            f"Min Sync Duration: {report.performance.min_sync_duration:.2f}s",
            f"Max Sync Duration: {report.performance.max_sync_duration:.2f}s",
            f"Total Data Transferred: {report.performance.total_data_transferred} bytes",
            "",
            "VERIFICATION RESULTS",
            "-" * 40,
            f"Total Documents: {report.verification.total_documents}",
            f"Verified Documents: {report.verification.verified_documents}",
            f"Missing Documents: {report.verification.missing_documents}",
            f"Consistency Checks Passed: {report.verification.consistency_checks_passed}/{report.verification.total_consistency_checks}",
            f"Data Integrity Score: {report.verification.data_integrity_score}%",
            "",
            "TEST PHASES",
            "-" * 40
        ]
        
        for phase in report.phases:
            lines.append(f"  {phase.name}: {phase.status} ({phase.duration:.2f}s)")
            if phase.error:
                lines.append(f"    Error: {phase.error}")
        
        lines.extend([
            "",
            "DOCUMENTS CREATED",
            "-" * 40
        ])
        
        for doc in report.documents:
            lines.append(f"  {doc.type} - {doc.client_id} - {doc.document_id} - {doc.sync_status}")
        
        if report.errors:
            lines.extend([
                "",
                "ERRORS",
                "-" * 40
            ])
            for error in report.errors:
                lines.append(f"  - {error}")
        
        if report.warnings:
            lines.extend([
                "",
                "WARNINGS",
                "-" * 40
            ])
            for warning in report.warnings:
                lines.append(f"  - {warning}")
        
        lines.extend([
            "",
            "CONFIGURATION",
            "-" * 40,
            json.dumps(report.config, indent=2),
            "",
            "=" * 80
        ])
        
        return "\n".join(lines)
    
    def generate_summary_report(self) -> str:
        """Generate a brief summary report
        
        Returns:
            Summary report string
        """
        report = self._build_complete_report()
        
        summary_lines = [
            f"Test Summary - {report.test_id}",
            f"Status: {report.status}",
            f"Duration: {report.total_duration:.2f}s",
            f"Sync Operations: {report.performance.successful_syncs}/{report.performance.total_sync_operations}",
            f"Data Integrity: {report.verification.data_integrity_score}%",
            f"Documents: {len(report.documents)} created"
        ]
        
        if report.errors:
            summary_lines.append(f"Errors: {len(report.errors)}")
        
        if report.warnings:
            summary_lines.append(f"Warnings: {len(report.warnings)}")
        
        return " | ".join(summary_lines)