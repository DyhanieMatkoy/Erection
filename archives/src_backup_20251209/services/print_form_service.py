"""Print form service - manages PDF and Excel print forms"""
import configparser
import os
from typing import Optional, Tuple
from .estimate_print_form import EstimatePrintForm
from .daily_report_print_form import DailyReportPrintForm
from .excel_estimate_print_form import ExcelEstimatePrintForm
from .excel_daily_report_print_form import ExcelDailyReportPrintForm


class PrintFormService:
    """Service for managing print forms in different formats"""
    
    def __init__(self):
        """Initialize print form service"""
        self.config = self._load_config()
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from env.ini"""
        config = configparser.ConfigParser()
        if os.path.exists('env.ini'):
            config.read('env.ini', encoding='utf-8')
        return config
    
    def get_print_format(self) -> str:
        """Get configured print format (PDF or Excel)"""
        if 'PrintForms' in self.config and 'format' in self.config['PrintForms']:
            return self.config['PrintForms']['format'].upper()
        return 'PDF'
    
    def set_print_format(self, format_type: str) -> bool:
        """Set print format in configuration"""
        try:
            if 'PrintForms' not in self.config:
                self.config.add_section('PrintForms')
            
            self.config['PrintForms']['format'] = format_type.upper()
            
            # Save to file
            with open('env.ini', 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            return True
        except Exception as e:
            print(f"Error saving print format: {e}")
            return False
    
    def get_templates_path(self) -> str:
        """Get templates path from configuration"""
        if 'PrintForms' in self.config and 'templates_path' in self.config['PrintForms']:
            return self.config['PrintForms']['templates_path']
        return 'PrnForms'
    
    def generate_estimate(self, estimate_id: int) -> Optional[Tuple[bytes, str]]:
        """
        Generate estimate print form in configured format
        
        Args:
            estimate_id: ID of the estimate
            
        Returns:
            Tuple of (content bytes, file extension) or None if failed
        """
        format_type = self.get_print_format()
        
        if format_type == 'EXCEL':
            generator = ExcelEstimatePrintForm()
            content = generator.generate(estimate_id)
            if content:
                return (content, 'xlsx')
        else:  # PDF
            generator = EstimatePrintForm()
            content = generator.generate(estimate_id)
            if content:
                return (content, 'pdf')
        
        return None
    
    def generate_daily_report(self, report_id: int) -> Optional[Tuple[bytes, str]]:
        """
        Generate daily report print form in configured format
        
        Args:
            report_id: ID of the daily report
            
        Returns:
            Tuple of (content bytes, file extension) or None if failed
        """
        format_type = self.get_print_format()
        
        if format_type == 'EXCEL':
            generator = ExcelDailyReportPrintForm()
            content = generator.generate(report_id)
            if content:
                return (content, 'xlsx')
        else:  # PDF
            generator = DailyReportPrintForm()
            content = generator.generate(report_id)
            if content:
                return (content, 'pdf')
        
        return None
    
    def create_templates(self) -> Tuple[bool, str]:
        """
        Create default Excel templates
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Ensure templates directory exists
            templates_path = self.get_templates_path()
            if not os.path.exists(templates_path):
                os.makedirs(templates_path)
            
            # Create estimate template
            estimate_generator = ExcelEstimatePrintForm()
            estimate_success = estimate_generator.create_template()
            
            # Create daily report template
            report_generator = ExcelDailyReportPrintForm()
            report_success = report_generator.create_template()
            
            if estimate_success and report_success:
                return (True, f"Шаблоны успешно созданы в папке '{templates_path}'")
            elif estimate_success:
                return (True, f"Шаблон сметы создан в папке '{templates_path}', но не удалось создать шаблон ежедневного отчета")
            elif report_success:
                return (True, f"Шаблон ежедневного отчета создан в папке '{templates_path}', но не удалось создать шаблон сметы")
            else:
                return (False, "Не удалось создать шаблоны")
        except Exception as e:
            return (False, f"Ошибка при создании шаблонов: {str(e)}")
    
    def templates_exist(self) -> bool:
        """Check if templates exist"""
        templates_path = self.get_templates_path()
        estimate_template = os.path.join(templates_path, ExcelEstimatePrintForm.TEMPLATE_NAME)
        report_template = os.path.join(templates_path, ExcelDailyReportPrintForm.TEMPLATE_NAME)
        return os.path.exists(estimate_template) or os.path.exists(report_template)
