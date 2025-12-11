"""Print form generator base class"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from typing import List, Tuple, Any


class PrintFormGenerator:
    """Base class for generating print forms using ReportLab"""
    
    def __init__(self, orientation='portrait'):
        """Initialize print form generator
        
        Args:
            orientation: 'portrait' or 'landscape'
        """
        self.orientation = orientation
        self.page_size = landscape(A4) if orientation == 'landscape' else A4
        self.page_width, self.page_height = self.page_size
        # Reduced margins for landscape to maximize table width
        self.margin = 10 * mm if orientation == 'landscape' else 20 * mm
        self.styles = getSampleStyleSheet()
        
        # Register fonts with Cyrillic support
        self._register_fonts()
        
        # Create custom styles
        self._create_custom_styles()
    
    def _register_fonts(self):
        """Register fonts with Cyrillic support"""
        import os
        import sys
        
        # Try multiple font sources
        font_registered = False
        
        # Option 1: Try common Windows fonts with Cyrillic support
        windows_fonts = [
            (r'C:\Windows\Fonts\arial.ttf', r'C:\Windows\Fonts\arialbd.ttf', 'Arial'),
            (r'C:\Windows\Fonts\times.ttf', r'C:\Windows\Fonts\timesbd.ttf', 'Times'),
            (r'C:\Windows\Fonts\calibri.ttf', r'C:\Windows\Fonts\calibrib.ttf', 'Calibri'),
            (r'C:\Windows\Fonts\verdana.ttf', r'C:\Windows\Fonts\verdanab.ttf', 'Verdana'),
        ]
        
        for regular_path, bold_path, font_name in windows_fonts:
            try:
                if os.path.exists(regular_path):
                    pdfmetrics.registerFont(TTFont(font_name, regular_path))
                    if os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont(f'{font_name}-Bold', bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont(f'{font_name}-Bold', regular_path))
                    self.font_name = font_name
                    self.font_name_bold = f'{font_name}-Bold'
                    font_registered = True
                    print(f"Registered font: {font_name}")
                    break
            except Exception as e:
                print(f"Failed to register {font_name}: {e}")
                continue
        
        # Option 2: Try DejaVu fonts from project folder
        if not font_registered:
            project_fonts = [
                os.path.join('fonts', 'DejaVuSans.ttf'),
                os.path.join('fonts', 'DejaVuSans-Bold.ttf'),
            ]
            try:
                if os.path.exists(project_fonts[0]):
                    pdfmetrics.registerFont(TTFont('DejaVuSans', project_fonts[0]))
                    if os.path.exists(project_fonts[1]):
                        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', project_fonts[1]))
                    else:
                        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', project_fonts[0]))
                    self.font_name = 'DejaVuSans'
                    self.font_name_bold = 'DejaVuSans-Bold'
                    font_registered = True
                    print(f"Registered font: DejaVuSans from project folder")
            except Exception as e:
                print(f"Failed to register DejaVu from project: {e}")
        
        # Option 3: Fallback to Helvetica (will show squares for Cyrillic)
        if not font_registered:
            self.font_name = 'Helvetica'
            self.font_name_bold = 'Helvetica-Bold'
            print("WARNING: Using Helvetica - Cyrillic characters may not display correctly!")
            print("Please install fonts with Cyrillic support.")
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name_bold,
            fontSize=16,
            alignment=1,  # Center
            spaceAfter=12
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontName=self.font_name_bold,
            fontSize=12,
            spaceAfter=6
        ))
        
        # Normal text style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            spaceAfter=6
        ))
        
        # Small text style
        self.styles.add(ParagraphStyle(
            name='CustomSmall',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=8
        ))
    
    def create_pdf(self, elements: List[Any]) -> bytes:
        """
        Create PDF from list of elements
        
        Args:
            elements: List of ReportLab flowable elements
            
        Returns:
            PDF content as bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _encode_text(self, text: str) -> str:
        """Encode text for proper display in PDF"""
        if not text:
            return ""
        # Ensure text is properly encoded
        if isinstance(text, str):
            return text
        return str(text)
    
    def create_title(self, text: str) -> Paragraph:
        """Create title paragraph"""
        return Paragraph(self._encode_text(text), self.styles['CustomTitle'])
    
    def create_subtitle(self, text: str) -> Paragraph:
        """Create subtitle paragraph"""
        return Paragraph(self._encode_text(text), self.styles['CustomSubtitle'])
    
    def create_paragraph(self, text: str) -> Paragraph:
        """Create normal paragraph"""
        return Paragraph(self._encode_text(text), self.styles['CustomNormal'])
    
    def create_small_paragraph(self, text: str) -> Paragraph:
        """Create small paragraph"""
        return Paragraph(self._encode_text(text), self.styles['CustomSmall'])
    
    def create_centered_paragraph(self, text: str) -> Paragraph:
        """Create centered paragraph"""
        style = ParagraphStyle(
            name='TempCentered',
            parent=self.styles['CustomNormal'],
            alignment=1  # Center
        )
        return Paragraph(self._encode_text(text), style)
    
    def create_small_centered_paragraph(self, text: str) -> Paragraph:
        """Create small centered paragraph"""
        style = ParagraphStyle(
            name='TempSmallCentered',
            parent=self.styles['CustomSmall'],
            alignment=1  # Center
        )
        return Paragraph(self._encode_text(text), style)
    
    def create_spacer(self, height: float = 12) -> Spacer:
        """Create vertical spacer"""
        return Spacer(1, height)
    
    def create_table(
        self,
        data: List[List[Any]],
        col_widths: List[float] = None,
        style: List[Tuple] = None
    ) -> Table:
        """
        Create formatted table
        
        Args:
            data: Table data as list of rows
            col_widths: Column widths (optional)
            style: Additional table style commands (optional)
            
        Returns:
            Formatted Table object
        """
        # Default table style
        default_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]
        
        # Add custom style if provided
        if style:
            default_style.extend(style)
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(default_style))
        
        return table
    
    def format_number(self, value: float, decimals: int = 2) -> str:
        """Format number with specified decimal places"""
        return f"{value:.{decimals}f}"
    
    def format_date(self, date_obj) -> str:
        """Format date object to string"""
        if date_obj:
            # Handle string dates from SQLite
            if isinstance(date_obj, str):
                # Try to parse and reformat
                try:
                    from datetime import datetime
                    parsed = datetime.strptime(date_obj, "%Y-%m-%d")
                    return parsed.strftime("%d.%m.%Y")
                except:
                    return date_obj
            # Handle date objects
            return date_obj.strftime("%d.%m.%Y")
        return ""
    
    def create_info_table(self, data: List[Tuple[str, str]]) -> Table:
        """
        Create information table (label-value pairs)
        
        Args:
            data: List of (label, value) tuples
            
        Returns:
            Formatted Table object
        """
        table_data = [[label, value] for label, value in data]
        
        style = [
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), self.font_name_bold),
            ('FONTNAME', (1, 0), (1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]
        
        col_widths = [80 * mm, 100 * mm]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle(style))
        
        return table
