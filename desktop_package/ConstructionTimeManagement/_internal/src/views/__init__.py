"""Views module"""

# Base forms
from .base_list_form import BaseListForm
from .base_document_form import BaseDocumentForm
from .base_table_part import BaseTablePart

# Reference forms
from .counterparty_form import CounterpartyForm
from .counterparty_list_form_v2 import CounterpartyListFormV2 as CounterpartyListForm
from .work_form import WorkForm
from .work_list_form_v2 import WorkListFormV2 as WorkListForm
from .person_form import PersonForm
from .person_list_form_v2 import PersonListFormV2 as PersonListForm
from .organization_form import OrganizationForm
from .organization_list_form_v2 import OrganizationListFormV2 as OrganizationListForm
from .object_form import ObjectForm
from .object_list_form_v2 import ObjectListFormV2 as ObjectListForm

# Dialogs
from .reference_picker_dialog import ReferencePickerDialog
from .employee_picker_dialog import EmployeePickerDialog

# Document forms
from .timesheet_list_form_v2 import TimesheetListFormV2 as TimesheetListForm
from .timesheet_document_form import TimesheetDocumentForm

# Main windows
from .login_form import LoginForm
from .main_window import MainWindow

__all__ = [
    'BaseListForm',
    'BaseDocumentForm',
    'BaseTablePart',
    'CounterpartyForm',
    'CounterpartyListForm',
    'WorkForm',
    'WorkListForm',
    'PersonForm',
    'PersonListForm',
    'OrganizationForm',
    'OrganizationListForm',
    'ObjectForm',
    'ObjectListForm',
    'ReferencePickerDialog',
    'EmployeePickerDialog',
    'TimesheetListForm',
    'TimesheetDocumentForm',
    'LoginForm',
    'MainWindow',
]
