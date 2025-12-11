"""Estimate print form generator"""
from typing import Optional
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from .print_form_generator import PrintFormGenerator
from ..data.models.estimate import Estimate
from ..data.database_manager import DatabaseManager


class EstimatePrintForm(PrintFormGenerator):
    """Generator for estimate print forms"""
    
    def __init__(self):
        """Initialize estimate print form generator"""
        super().__init__(orientation='landscape')
        self.db = DatabaseManager().get_connection()
    
    def generate(self, estimate_id: int) -> Optional[bytes]:
        """
        Generate estimate print form based on АРСД format
        
        Args:
            estimate_id: ID of the estimate
            
        Returns:
            PDF content as bytes or None if estimate not found
        """
        # Load estimate data
        estimate_data = self._load_estimate_data(estimate_id)
        if not estimate_data:
            return None
        
        # Create document elements
        elements = []
        
        # Header with approval section
        elements.append(self.create_spacer(5))
        approval_table = self._create_approval_section(estimate_data)
        elements.append(approval_table)
        elements.append(self.create_spacer(15))
        
        # Title
        elements.append(self.create_title(f"ЛОКАЛЬНЫЙ СМЕТНЫЙ РАСЧЕТ №{estimate_data['number']}"))
        elements.append(self.create_paragraph("(локальная смета)"))
        elements.append(self.create_spacer(10))
        
        # Object description
        object_desc = estimate_data['object_name'] or "Объект не указан"
        elements.append(self.create_centered_paragraph(object_desc))
        elements.append(self.create_small_centered_paragraph("(наименование работ и затрат, наименование объекта)"))
        elements.append(self.create_spacer(15))
        
        # Lines table
        lines_table = self._create_lines_table(estimate_data['lines'])
        elements.append(lines_table)
        elements.append(self.create_spacer(10))
        
        # Totals
        elements.append(self._create_totals_section(estimate_data))
        
        # Generate PDF
        return self.create_pdf(elements)
    
    def _load_estimate_data(self, estimate_id: int) -> Optional[dict]:
        """Load estimate data from database"""
        cursor = self.db.cursor()
        
        # Load estimate header
        cursor.execute("""
            SELECT 
                e.id, e.number, e.date, e.total_sum, e.total_labor,
                c.name as customer_name,
                o.name as object_name,
                org.name as contractor_name,
                p.full_name as responsible_name
            FROM estimates e
            LEFT JOIN counterparties c ON e.customer_id = c.id
            LEFT JOIN objects o ON e.object_id = o.id
            LEFT JOIN organizations org ON e.contractor_id = org.id
            LEFT JOIN persons p ON e.responsible_id = p.id
            WHERE e.id = ?
        """, (estimate_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        estimate_data = {
            'id': row['id'],
            'number': row['number'],
            'date': row['date'],
            'total_sum': row['total_sum'],
            'total_labor': row['total_labor'],
            'customer_name': row['customer_name'],
            'object_name': row['object_name'],
            'contractor_name': row['contractor_name'],
            'responsible_name': row['responsible_name'],
            'lines': []
        }
        
        # Load estimate lines including group information
        cursor.execute("""
            SELECT 
                el.line_number,
                el.work_id,
                w.name as work_name,
                w.code as work_code,
                el.quantity,
                el.unit,
                el.price,
                el.labor_rate,
                el.sum,
                el.planned_labor
            FROM estimate_lines el
            LEFT JOIN works w ON el.work_id = w.id
            WHERE el.estimate_id = ?
            ORDER BY el.line_number
        """, (estimate_id,))
        
        for line_row in cursor.fetchall():
            # Check if this is a group row (work_id = -1)
            is_group = line_row['work_id'] == -1
            
            estimate_data['lines'].append({
                'line_number': line_row['line_number'],
                'work_name': line_row['work_name'] or line_row['unit'] if not is_group else "",
                'work_code': line_row['work_code'] or "",
                'quantity': line_row['quantity'],
                'unit': line_row['unit'] if not is_group else "",
                'price': line_row['price'],
                'labor_rate': line_row['labor_rate'],
                'sum': line_row['sum'],
                'planned_labor': line_row['planned_labor'],
                'is_group': is_group,
                'group_name': line_row['unit'] if is_group else ""
            })
        
        return estimate_data
    
    def _create_approval_section(self, estimate_data: dict) -> 'Table':
        """Create approval section with customer and contractor"""
        from reportlab.lib import colors
        
        customer_name = estimate_data['customer_name'] or "_______________"
        contractor_name = estimate_data['contractor_name'] or "_______________"
        
        data = [
            ["Согласовано:", "", "", "Утверждаю:", ""],
            [f"Заказчик: {customer_name}", "", "", f"Подрядчик: {contractor_name}", ""],
            ["Генеральный директор", "", "", "Директор", ""],
            ["____________________", "", "", "____________________", ""]
        ]
        
        # Wider columns for landscape format
        col_widths = [70 * mm, 30 * mm, 30 * mm, 70 * mm, 77 * mm]
        
        style = [
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(style))
        return table
    
    def _create_lines_table(self, lines: list) -> 'Table':
        """Create table with estimate lines in АРСД format"""
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        
        # Multi-row header
        header1 = ["", "", "", "", "", "на единицу работ", "", "", "", "на полный объём работ", "", "", ""]
        header2 = [
            "N",
            "Код",
            "Наименование работ и затрат",
            "ЕдИзм",
            "Кол-во",
            "Зарплата",
            "Материалы,\nмеханизмы",
            "Всего",
            "ТЗ",
            "Зарплата",
            "Материалы,\nмеханизмы",
            "Всего",
            "ТЗ"
        ]
        
        # Style for wrapping text in name column
        name_style = ParagraphStyle(
            name='NameColumn',
            fontName=self.font_name,
            fontSize=8,
            leading=10,
            wordWrap='CJK'
        )
        
        # Style for group rows (bold)
        group_style = ParagraphStyle(
            name='GroupColumn',
            fontName=self.font_name_bold,
            fontSize=9,
            leading=11,
            wordWrap='CJK'
        )
        
        # Table data
        table_data = [header1, header2]
        group_spans = []  # Track which rows are groups for spanning
        
        for idx, line in enumerate(lines):
            row_idx = idx + 2  # +2 because of header rows
            
            # Check if this is a group
            if line.get('is_group', False):
                # Group row - spans entire width
                group_text = line.get('group_name', '') or line['work_name']
                row = [
                    str(line['line_number']),
                    Paragraph(group_text, group_style),
                    "", "", "", "", "", "", "", "", "", "", ""
                ]
                table_data.append(row)
                # Mark this row for spanning (from column 1 to end)
                group_spans.append(row_idx)
            else:
                # Regular work line
                # Calculate unit costs
                unit_labor = line['labor_rate'] if line['quantity'] > 0 else 0
                unit_materials = (line['price'] - unit_labor) if line['price'] > unit_labor else 0
                unit_total = line['price']
                unit_tz = line['labor_rate'] / line['quantity'] if line['quantity'] > 0 else 0
                
                # Total costs
                total_labor = unit_labor * line['quantity']
                total_materials = unit_materials * line['quantity']
                total_sum = line['sum']
                total_tz = line['planned_labor']
                
                # Use Paragraph for work name to enable text wrapping
                work_name_para = Paragraph(line['work_name'], name_style)
                
                row = [
                    str(line['line_number']),
                    line.get('work_code', ''),
                    work_name_para,  # Wrapped text
                    line['unit'],
                    self.format_number(line['quantity'], 2),
                    self.format_number(unit_labor, 2),
                    self.format_number(unit_materials, 2),
                    self.format_number(unit_total, 2),
                    self.format_number(unit_tz, 2),
                    self.format_number(total_labor, 2),
                    self.format_number(total_materials, 2),
                    self.format_number(total_sum, 2),
                    self.format_number(total_tz, 2)
                ]
                table_data.append(row)
        
        # Column widths - optimized for landscape A4 with 10mm margins (277mm available)
        col_widths = [
            10 * mm,   # N
            18 * mm,   # Код
            70 * mm,   # Наименование (расширена)
            15 * mm,   # ЕдИзм
            14 * mm,   # Кол-во
            17 * mm,   # Зарплата (ед)
            17 * mm,   # Материалы (ед)
            17 * mm,   # Всего (ед)
            14 * mm,   # ТЗ (ед)
            17 * mm,   # Зарплата (полн)
            17 * mm,   # Материалы (полн)
            17 * mm,   # Всего (полн)
            14 * mm    # ТЗ (полн)
        ]
        
        # Custom style
        custom_style = [
            # Header styling
            ('SPAN', (5, 0), (8, 0)),   # "на единицу работ"
            ('SPAN', (9, 0), (12, 0)),  # "на полный объём работ"
            ('ALIGN', (5, 0), (8, 0), 'CENTER'),
            ('ALIGN', (9, 0), (12, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), self.font_name_bold),
            ('FONTSIZE', (0, 0), (-1, 1), 8),
            
            # Data rows
            ('ALIGN', (0, 2), (0, -1), 'CENTER'),   # N column
            ('ALIGN', (1, 2), (1, -1), 'LEFT'),     # Code column
            ('ALIGN', (2, 2), (2, -1), 'LEFT'),     # Name column
            ('ALIGN', (3, 2), (3, -1), 'CENTER'),   # Unit column
            ('ALIGN', (4, 2), (-1, -1), 'RIGHT'),   # Numeric columns
            ('FONTNAME', (0, 2), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 2), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),    # Top alignment for wrapped text
        ]
        
        # Add spans for group rows
        for group_row_idx in group_spans:
            # Span from column 1 (after line number) to the end
            custom_style.append(('SPAN', (1, group_row_idx), (12, group_row_idx)))
            # Make group rows stand out
            custom_style.append(('BACKGROUND', (0, group_row_idx), (-1, group_row_idx), colors.lightgrey))
            custom_style.append(('FONTNAME', (1, group_row_idx), (1, group_row_idx), self.font_name_bold))
        
        return self.create_table(table_data, col_widths, custom_style)
    
    def _create_totals_section(self, estimate_data: dict) -> 'Table':
        """Create totals section"""
        from reportlab.lib import colors
        
        data = [
            ["ИТОГО по смете:", ""],
            [f"Всего: {self.format_number(estimate_data['total_sum'])} руб.", ""],
            [f"Трудозатраты: {self.format_number(estimate_data['total_labor'])} ч.", ""]
        ]
        
        col_widths = [100 * mm, 70 * mm]
        
        style = [
            ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(style))
        return table
