"""
Table Part Print Service

This module provides printing services for table parts, including
HTML generation, PDF creation, and printer output with proper
page breaks and formatting.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import html
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextDocument, QPageSize
from PyQt6.QtPrintSupport import QPrinter


class PrintFormat(Enum):
    """Print output formats"""
    PRINTER = "printer"
    PDF = "pdf"


class PageOrientation(Enum):
    """Page orientation options"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class PrintConfiguration:
    """Configuration for table part printing"""
    orientation: PageOrientation = PageOrientation.PORTRAIT
    scale_percent: int = 100
    top_margin_mm: int = 20
    bottom_margin_mm: int = 20
    left_margin_mm: int = 15
    right_margin_mm: int = 15
    repeat_headers: bool = True
    show_grid: bool = True
    fit_to_width: bool = False
    format: PrintFormat = PrintFormat.PRINTER
    table_name: str = "Табличная часть"
    max_rows_per_page: int = 50  # For automatic page breaks


class TablePartPrintService(QObject):
    """
    Service for printing table parts with proper formatting and page breaks.
    
    Features:
    - HTML generation with print-optimized styling
    - Automatic page breaks for large tables
    - Repeating column headers on each page
    - Configurable margins and orientation
    - Support for printer and PDF output
    """
    
    printStarted = pyqtSignal()
    printProgress = pyqtSignal(int)  # Progress percentage
    printCompleted = pyqtSignal(bool)  # Success status
    printError = pyqtSignal(str)  # Error message
    
    def __init__(self):
        super().__init__()
    
    def generate_html_preview(self, table_data: List[Dict[str, Any]], 
                            config: PrintConfiguration) -> str:
        """
        Generate HTML preview of the table for printing.
        
        Args:
            table_data: List of dictionaries representing table rows
            config: Print configuration
            
        Returns:
            HTML string with print-optimized formatting
        """
        if not table_data:
            return "<p>Нет данных для печати</p>"
        
        # Get column names from first row
        columns = list(table_data[0].keys()) if table_data else []
        
        # Generate CSS styles
        css_styles = self._generate_css_styles(config)
        
        # Generate HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{html.escape(config.table_name)}</title>
            <style>
                {css_styles}
            </style>
        </head>
        <body>
            <div class="page-container">
                {self._generate_table_html(table_data, columns, config)}
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_css_styles(self, config: PrintConfiguration) -> str:
        """Generate CSS styles for print formatting"""
        grid_style = "border-collapse: collapse;" if config.show_grid else "border-collapse: separate;"
        border_style = "1px solid #000;" if config.show_grid else "none;"
        
        # Calculate page dimensions based on orientation
        if config.orientation == PageOrientation.LANDSCAPE:
            page_width = "297mm"
            page_height = "210mm"
        else:
            page_width = "210mm"
            page_height = "297mm"
        
        # Calculate content width considering margins
        content_width = f"calc({page_width} - {config.left_margin_mm}mm - {config.right_margin_mm}mm)"
        
        css = f"""
        @page {{
            size: A4 {config.orientation.value};
            margin: {config.top_margin_mm}mm {config.right_margin_mm}mm {config.bottom_margin_mm}mm {config.left_margin_mm}mm;
            @top-center {{
                content: "{html.escape(config.table_name)}";
                font-size: 10pt;
                font-weight: bold;
            }}
            @bottom-center {{
                content: "Страница " counter(page) " из " counter(pages);
                font-size: 9pt;
            }}
        }}
        
        body {{
            font-family: Arial, sans-serif;
            font-size: 10pt;
            margin: 0;
            padding: 0;
            line-height: 1.2;
            counter-reset: page;
        }}
        
        .page-container {{
            width: {content_width};
            max-width: 100%;
        }}
        
        .table-title {{
            font-size: 14pt;
            font-weight: bold;
            text-align: center;
            margin-bottom: 10mm;
            page-break-inside: avoid;
            page-break-after: avoid;
        }}
        
        .table-section {{
            margin-bottom: 5mm;
        }}
        
        .page-section {{
            page-break-inside: avoid;
            min-height: 50mm; /* Minimum content per page */
        }}
        
        table {{
            width: 100%;
            {grid_style}
            font-size: 9pt;
            page-break-inside: auto;
        }}
        
        th, td {{
            border: {border_style}
            padding: 2mm;
            text-align: left;
            vertical-align: top;
            word-wrap: break-word;
            page-break-inside: avoid;
        }}
        
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
            page-break-inside: avoid;
            page-break-after: avoid;
        }}
        
        .header-row {{
            page-break-inside: avoid;
            page-break-after: avoid;
            background-color: #f0f0f0 !important;
        }}
        
        .page-break {{
            page-break-before: always;
            counter-increment: page;
        }}
        
        .no-break {{
            page-break-inside: avoid;
        }}
        
        /* Ensure headers repeat on each page */
        .repeated-header {{
            display: table-header-group;
        }}
        
        /* Prevent widows and orphans */
        tr {{
            page-break-inside: avoid;
        }}
        
        /* Style for continued table indicator */
        .table-continued {{
            font-style: italic;
            font-size: 8pt;
            text-align: right;
            margin-bottom: 2mm;
            color: #666;
        }}
        
        /* Row number styling */
        .row-number, .row-number-header {{
            width: 30px;
            text-align: center;
            font-weight: bold;
            background-color: #f8f8f8;
        }}
        
        .row-number {{
            font-size: 8pt;
            color: #666;
        }}
        
        @media print {{
            .page-container {{
                width: 100%;
            }}
            
            table {{
                font-size: 8pt;
            }}
            
            th, td {{
                padding: 1mm;
            }}
            
            /* Ensure proper page breaks in print */
            .page-break {{
                page-break-before: always;
            }}
            
            /* Hide elements that shouldn't print */
            .no-print {{
                display: none !important;
            }}
        }}
        """
        
        # Add fit-to-width styling if enabled
        if config.fit_to_width:
            css += """
            table {
                table-layout: fixed;
            }
            
            th, td {
                overflow: hidden;
                text-overflow: ellipsis;
            }
            """
        
        return css
    
    def _generate_table_html(self, table_data: List[Dict[str, Any]], 
                           columns: List[str], 
                           config: PrintConfiguration) -> str:
        """Generate HTML table with proper page breaks and multi-page handling"""
        html_parts = []
        
        # Add title (only on first page)
        html_parts.append(f'<div class="table-title">{html.escape(config.table_name)}</div>')
        
        # Split data into pages if needed
        if len(table_data) > config.max_rows_per_page:
            pages = self._split_data_into_pages(table_data, config.max_rows_per_page)
        else:
            pages = [table_data]
        
        total_pages = len(pages)
        
        # Generate each page
        for page_index, page_data in enumerate(pages):
            # Add page break for subsequent pages
            if page_index > 0:
                html_parts.append('<div class="page-break"></div>')
                
                # Add continuation indicator
                if page_index > 0:
                    html_parts.append(f'<div class="table-continued">{html.escape(config.table_name)} (продолжение)</div>')
            
            # Start page section
            html_parts.append('<div class="page-section">')
            html_parts.append('<div class="table-section">')
            html_parts.append('<table>')
            
            # Add header (on each page if configured, or just first page)
            if page_index == 0 or config.repeat_headers:
                header_class = "repeated-header" if config.repeat_headers and page_index > 0 else ""
                html_parts.append(f'<thead class="{header_class}">')
                html_parts.append(self._generate_header_html(columns))
                html_parts.append('</thead>')
            
            # Add table body
            html_parts.append('<tbody>')
            
            # Add data rows with row numbers for multi-page tables
            start_row_num = sum(len(pages[i]) for i in range(page_index)) + 1
            
            for local_row_index, row_data in enumerate(page_data):
                global_row_num = start_row_num + local_row_index
                html_parts.append(self._generate_row_html(row_data, columns, global_row_num))
            
            html_parts.append('</tbody>')
            html_parts.append('</table>')
            
            # Add page footer information
            if total_pages > 1:
                html_parts.append(f'<div class="table-continued">Страница {page_index + 1} из {total_pages}</div>')
            
            html_parts.append('</div>')  # table-section
            html_parts.append('</div>')  # page-section
        
        return '\n'.join(html_parts)
    
    def _split_data_into_pages(self, table_data: List[Dict[str, Any]], 
                             max_rows_per_page: int) -> List[List[Dict[str, Any]]]:
        """
        Split table data into pages with intelligent page breaks.
        
        Considers:
        - Maximum rows per page
        - Avoiding orphaned rows
        - Keeping related data together when possible
        """
        if len(table_data) <= max_rows_per_page:
            return [table_data]
        
        pages = []
        current_page = []
        
        for i, row in enumerate(table_data):
            current_page.append(row)
            
            # Check if we should start a new page
            should_break = False
            
            # Basic row limit check
            if len(current_page) >= max_rows_per_page:
                should_break = True
            
            # Avoid orphaned rows (less than 3 rows on last page)
            remaining_rows = len(table_data) - i - 1
            if (len(current_page) >= max_rows_per_page - 2 and 
                remaining_rows > 0 and remaining_rows < 3):
                should_break = True
            
            # Start new page if needed
            if should_break and current_page:
                pages.append(current_page)
                current_page = []
        
        # Add remaining rows to last page
        if current_page:
            pages.append(current_page)
        
        return pages
    
    def _generate_header_html(self, columns: List[str], include_row_numbers: bool = False) -> str:
        """
        Generate HTML for table header.
        
        Args:
            columns: List of column names
            include_row_numbers: Whether to include a row number column
            
        Returns:
            HTML string for the header row
        """
        header_cells = []
        
        # Add row number header if needed
        if include_row_numbers:
            header_cells.append('<th class="row-number-header">№</th>')
        
        # Add column headers
        for column in columns:
            escaped_column = html.escape(str(column))
            header_cells.append(f'<th>{escaped_column}</th>')
        
        return f'<tr class="header-row">{"".join(header_cells)}</tr>'
    
    def _generate_row_html(self, row_data: Dict[str, Any], columns: List[str], 
                         row_number: Optional[int] = None) -> str:
        """
        Generate HTML for a table row.
        
        Args:
            row_data: Dictionary containing row data
            columns: List of column names
            row_number: Optional row number for display
            
        Returns:
            HTML string for the row
        """
        row_cells = []
        
        # Add row number cell if provided
        if row_number is not None:
            row_cells.append(f'<td class="row-number">{row_number}</td>')
        
        # Add data cells
        for column in columns:
            value = row_data.get(column, "")
            escaped_value = html.escape(str(value) if value is not None else "")
            row_cells.append(f'<td>{escaped_value}</td>')
        
        return f'<tr class="no-break">{"".join(row_cells)}</tr>'
    
    def print_to_printer(self, table_data: List[Dict[str, Any]], 
                        config: PrintConfiguration, 
                        printer: QPrinter) -> bool:
        """
        Print table data to a physical printer.
        
        Args:
            table_data: Table data to print
            config: Print configuration
            printer: Configured QPrinter instance
            
        Returns:
            True if printing was successful, False otherwise
        """
        try:
            self.printStarted.emit()
            
            # Generate HTML content
            html_content = self.generate_html_preview(table_data, config)
            
            # Create text document
            document = QTextDocument()
            document.setHtml(html_content)
            
            # Configure document for printing
            self._configure_document_for_printing(document, config, printer)
            
            # Print the document
            document.print(printer)
            
            self.printCompleted.emit(True)
            return True
            
        except Exception as e:
            error_msg = f"Ошибка печати на принтер: {str(e)}"
            self.printError.emit(error_msg)
            self.printCompleted.emit(False)
            return False
    
    def print_to_pdf(self, table_data: List[Dict[str, Any]], 
                    config: PrintConfiguration, 
                    file_path: str) -> bool:
        """
        Print table data to PDF file.
        
        Args:
            table_data: Table data to print
            config: Print configuration
            file_path: Path to save PDF file
            
        Returns:
            True if PDF creation was successful, False otherwise
        """
        try:
            self.printStarted.emit()
            
            # Create PDF printer
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(file_path)
            
            # Configure printer
            if config.orientation == PageOrientation.LANDSCAPE:
                printer.setPageOrientation(QPageSize.Orientation.Landscape)
            else:
                printer.setPageOrientation(QPageSize.Orientation.Portrait)
            
            # Set margins (convert mm to points)
            margins = (
                config.left_margin_mm * 2.83465,
                config.top_margin_mm * 2.83465,
                config.right_margin_mm * 2.83465,
                config.bottom_margin_mm * 2.83465
            )
            printer.setPageMargins(*margins, QPrinter.Unit.Point)
            
            # Generate HTML content
            html_content = self.generate_html_preview(table_data, config)
            
            # Create and configure document
            document = QTextDocument()
            document.setHtml(html_content)
            
            self._configure_document_for_printing(document, config, printer)
            
            # Print to PDF
            document.print(printer)
            
            self.printCompleted.emit(True)
            return True
            
        except Exception as e:
            error_msg = f"Ошибка создания PDF: {str(e)}"
            self.printError.emit(error_msg)
            self.printCompleted.emit(False)
            return False
    
    def _configure_document_for_printing(self, document: QTextDocument, 
                                       config: PrintConfiguration, 
                                       printer: QPrinter):
        """Configure QTextDocument for printing"""
        # Set page size
        page_size = printer.pageLayout().pageSize()
        document.setPageSize(page_size.sizePoints())
        
        # Apply scaling if needed
        if config.scale_percent != 100:
            # Note: QTextDocument doesn't directly support scaling
            # This would need to be handled at the printer level
            pass
    
    def get_page_count(self, table_data: List[Dict[str, Any]], 
                      config: PrintConfiguration) -> int:
        """
        Calculate the number of pages needed for printing.
        
        Args:
            table_data: Table data
            config: Print configuration
            
        Returns:
            Estimated number of pages
        """
        if not table_data:
            return 0
        
        # Simple estimation based on rows per page
        rows_count = len(table_data)
        pages = (rows_count + config.max_rows_per_page - 1) // config.max_rows_per_page
        
        return max(1, pages)
    
    def validate_print_data(self, table_data: List[Dict[str, Any]]) -> tuple[bool, str]:
        """
        Validate table data for printing.
        
        Args:
            table_data: Table data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not table_data:
            return False, "Нет данных для печати"
        
        if not isinstance(table_data, list):
            return False, "Данные таблицы должны быть списком"
        
        if not all(isinstance(row, dict) for row in table_data):
            return False, "Каждая строка должна быть словарем"
        
        # Check if all rows have the same columns
        if table_data:
            first_row_keys = set(table_data[0].keys())
            for i, row in enumerate(table_data[1:], 1):
                if set(row.keys()) != first_row_keys:
                    return False, f"Строка {i} имеет отличающиеся колонки"
        
        return True, ""


def create_print_service() -> TablePartPrintService:
    """
    Factory function to create a table part print service.
    
    Returns:
        Configured TablePartPrintService instance
    """
    return TablePartPrintService()