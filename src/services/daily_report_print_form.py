"""Daily report print form generator"""
from typing import Optional
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from .print_form_generator import PrintFormGenerator
from ..data.database_manager import DatabaseManager


class DailyReportPrintForm(PrintFormGenerator):
    """Generator for daily report print forms"""
    
    def __init__(self):
        """Initialize daily report print form generator"""
        super().__init__(orientation='landscape')
        self.db = DatabaseManager().get_connection()
    
    def generate(self, report_id: int) -> Optional[bytes]:
        """
        Generate daily report print form
        
        Args:
            report_id: ID of the daily report
            
        Returns:
            PDF content as bytes or None if report not found
        """
        # Load report data
        report_data = self._load_report_data(report_id)
        if not report_data:
            return None
        
        # Create document elements
        elements = []
        
        # Title
        elements.append(self.create_title("ЕЖЕДНЕВНЫЙ ОТЧЕТ О ВЫПОЛНЕННЫХ РАБОТАХ"))
        elements.append(self.create_spacer(10))
        
        # Document info header
        info_data = [
            ("Дата отчета:", self.format_date(report_data['date'])),
            ("Смета №:", f"{report_data['estimate_number']} от {self.format_date(report_data['estimate_date'])}"),
            ("Объект:", report_data['object_name'] or ""),
            ("Бригадир:", report_data['foreman_name'] or ""),
        ]
        elements.append(self.create_info_table(info_data))
        elements.append(self.create_spacer(15))
        
        # Lines table
        lines_table = self._create_lines_table(report_data['lines'])
        elements.append(lines_table)
        elements.append(self.create_spacer(15))
        
        # Totals
        total_planned = sum(line['planned_labor'] for line in report_data['lines'])
        total_actual = sum(line['actual_labor'] for line in report_data['lines'])
        total_deviation = ((total_actual - total_planned) / total_planned * 100) if total_planned > 0 else 0
        
        elements.append(self._create_totals_section(total_planned, total_actual, total_deviation))
        elements.append(self.create_spacer(20))
        
        # Signatures
        elements.append(self._create_signatures_section(report_data))
        
        # Generate PDF
        return self.create_pdf(elements)
    
    def _load_report_data(self, report_id: int) -> Optional[dict]:
        """Load daily report data from database"""
        cursor = self.db.cursor()
        
        # Load report header
        cursor.execute("""
            SELECT 
                dr.id, dr.date,
                e.number as estimate_number, e.date as estimate_date,
                o.name as object_name,
                p.full_name as foreman_name
            FROM daily_reports dr
            LEFT JOIN estimates e ON dr.estimate_id = e.id
            LEFT JOIN objects o ON e.object_id = o.id
            LEFT JOIN persons p ON dr.foreman_id = p.id
            WHERE dr.id = ?
        """, (report_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        report_data = {
            'id': row['id'],
            'date': row['date'],
            'estimate_number': row['estimate_number'],
            'estimate_date': row['estimate_date'],
            'object_name': row['object_name'],
            'foreman_name': row['foreman_name'],
            'lines': []
        }
        
        # Load report lines with estimate line data
        cursor.execute("""
            SELECT 
                drl.line_number,
                w.name as work_name,
                drl.planned_labor,
                drl.actual_labor,
                drl.deviation_percent,
                drl.id as line_id,
                '' as unit,
                0 as quantity
            FROM daily_report_lines drl
            LEFT JOIN works w ON drl.work_id = w.id
            WHERE drl.daily_report_id = ?
            ORDER BY drl.line_number
        """, (report_id,))
        
        # Try to get unit and quantity from works table
        # cursor.execute("""
        #     SELECT 
        #         drl.line_number,
        #         w.name as work_name,
        #         drl.planned_labor,
        #         drl.actual_labor,
        #         drl.deviation_percent,
        #         drl.id as line_id,
        #         w.unit,
        #         0 as quantity
        #     FROM daily_report_lines drl
        #     LEFT JOIN works w ON drl.work_id = w.id
        #     WHERE drl.report_id = ?
        #     ORDER BY drl.line_number
        # """, (report_id,))
        
        for line_row in cursor.fetchall():
            # Load executors for this line
            cursor.execute("""
                SELECT p.full_name
                FROM daily_report_executors dre
                JOIN persons p ON dre.executor_id = p.id
                WHERE dre.report_line_id = ?
                ORDER BY p.full_name
            """, (line_row['line_id'],))
            
            executors = [row['full_name'] for row in cursor.fetchall()]
            
            report_data['lines'].append({
                'line_number': line_row['line_number'],
                'work_name': line_row['work_name'] or "",
                'unit': line_row['unit'] or "",
                'quantity': line_row['quantity'] or 0,
                'planned_labor': line_row['planned_labor'],
                'actual_labor': line_row['actual_labor'],
                'deviation_percent': line_row['deviation_percent'],
                'executors': executors
            })
        
        return report_data
    
    def _create_lines_table(self, lines: list) -> 'Table':
        """Create table with daily report lines"""
        from reportlab.lib import colors
        
        # Table header
        header = [
            "№\nп/п",
            "Наименование\nвыполненных работ",
            "Ед.\nизм.",
            "Объем\nработ",
            "Плановые\nтрудозатраты, ч",
            "Фактические\nтрудозатраты, ч",
            "Отклонение,\n%",
            "Исполнители\n(ФИО)"
        ]
        
        # Table data
        table_data = [header]
        
        for line in lines:
            executors_str = ", ".join(line['executors']) if line['executors'] else ""
            
            row = [
                str(line['line_number']),
                line['work_name'],
                line.get('unit', ''),
                self.format_number(line.get('quantity', 0), 2),
                self.format_number(line['planned_labor'], 2),
                self.format_number(line['actual_labor'], 2),
                self.format_number(line['deviation_percent'], 1),
                executors_str
            ]
            table_data.append(row)
        
        # Column widths
        col_widths = [
            10 * mm,   # № п/п
            45 * mm,   # Наименование
            12 * mm,   # Ед.изм.
            15 * mm,   # Объем
            20 * mm,   # План. труд.
            20 * mm,   # Факт. труд.
            15 * mm,   # Откл.
            33 * mm    # Исполнители
        ]
        
        # Custom style for lines table
        custom_style = [
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # № column
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),    # Work name column
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),  # Unit column
            ('ALIGN', (3, 0), (6, -1), 'RIGHT'),   # Numeric columns
            ('ALIGN', (7, 0), (7, -1), 'LEFT'),    # Executors column
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]
        
        return self.create_table(table_data, col_widths, custom_style)
    
    def _create_totals_section(self, total_planned: float, total_actual: float, total_deviation: float) -> 'Table':
        """Create totals section"""
        from reportlab.lib import colors
        
        data = [
            ["ИТОГО:", ""],
            [f"Плановые трудозатраты: {self.format_number(total_planned, 2)} ч.", ""],
            [f"Фактические трудозатраты: {self.format_number(total_actual, 2)} ч.", ""],
            [f"Отклонение: {self.format_number(total_deviation, 1)}%", ""]
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
    
    def _create_signatures_section(self, report_data: dict) -> 'Table':
        """Create signatures section"""
        from reportlab.lib import colors
        
        foreman_name = report_data['foreman_name'] or "_______________"
        
        data = [
            ["Бригадир:", f"{foreman_name}", "____________________"],
            ["", "", "(подпись)"],
            ["", "", ""],
            ["Принял:", "_______________", "____________________"],
            ["", "", "(подпись)"]
        ]
        
        col_widths = [30 * mm, 70 * mm, 70 * mm]
        
        style = [
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle(style))
        return table
