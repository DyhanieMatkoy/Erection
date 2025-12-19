"""UI utilities for button styling and icons"""
import configparser
import os


class ButtonStyler:
    """Utility class for button styling with font icons"""
    
    # Icon mappings for standard commands
    ICON_MAP = {
        'create': '⊕',  # Plus circle
        'copy': '⧉',    # Clone/duplicate symbol
        'edit': '✏️',
        'delete': '✕',  # Cross
        'post': '→',    # Arrow right
        'unpost': '↶',  # Undo arrow
        'refresh': '🔄',
        'print': '🖨️',
        'save': '💾',
        'save_and_close': '💾➡️',
        'close': '❌',
        'cancel': '❌',
        'ok': '✅',
        'yes': '✅',
        'no': '❌',
        'add': '➕',
        'remove': '➖',
        'search': '🔍',
        'filter': '🔽',
        'clear': '❌',
        'clear_filter': '❌',
        'export': '📤',
        'import': '📥',
        'settings': '⚙️',
        'help': '❓',
        'info': 'ℹ️',
        'warning': '⚠️',
        'error': '❗',
        'up': '⬆️',
        'down': '⬇️',
        'left': '⬅️',
        'right': '➡️',
        'first': '⏮️',
        'last': '⏭️',
        'previous': '⬅️',
        'next': '➡️',
        'play': '▶️',
        'pause': '⏸️',
        'stop': '⏹️',
        'record': '⏺️',
        'folder': '📁',
        'file': '📄',
        'document': '📄',
        'list': '📋',
        'table': '📊',
        'chart': '📈',
        'calendar': '📅',
        'clock': '🕐',
        'user': '👤',
        'users': '👥',
        'group': '👥',
        'organization': '🏢',
        'counterparty': '🏢',
        'person': '👤',
        'object': '🏗️',
        'work': '🔧',
        'timesheet': '⏰',
        'report': '📊',
        'estimate': '💰',
        'contract': '📝',
        'invoice': '🧾',
        'payment': '💳',
        'money': '💰',
        'phone': '📞',
        'email': '📧',
        'address': '📍',
        'website': '🌐',
    }
    
    # Default labels for commands
    LABEL_MAP = {
        'create': 'Создать',
        'copy': 'Копировать',
        'edit': 'Изменить',
        'delete': 'Удалить',
        'post': 'Провести',
        'unpost': 'Отменить проведение',
        'refresh': 'Обновить',
        'print': 'Печать',
        'save': 'Сохранить',
        'save_and_close': 'Сохранить и закрыть',
        'close': 'Закрыть',
        'cancel': 'Отмена',
        'add': 'Добавить',
        'remove': 'Удалить',
        'search': 'Поиск',
        'filter': 'Фильтр',
        'export': 'Экспорт',
        'import': 'Импорт',
        'settings': 'Настройки',
        'help': 'Справка',
    }
    
    def __init__(self):
        self.button_style = self._load_button_style()
    
    def _load_button_style(self) -> str:
        """Load button style from settings"""
        config = configparser.ConfigParser()
        config_file = 'env.ini'
        
        if os.path.exists(config_file):
            try:
                config.read(config_file, encoding='utf-8')
                if config.has_section('Interface') and config.has_option('Interface', 'button_style'):
                    return config.get('Interface', 'button_style')
            except:
                pass
        
        return 'text'  # Default
    
    def get_button_text(self, command_id: str, label: str = None) -> str:
        """Get button text based on current style setting"""
        if label is None:
            label = self.LABEL_MAP.get(command_id, command_id)
        
        icon = self.ICON_MAP.get(command_id, '')
        
        if self.button_style == 'icons':
            return icon or label
        elif self.button_style == 'both':
            return f"{icon} {label}" if icon else label
        else:  # text
            return label
    
    def get_button_tooltip(self, command_id: str, label: str = None) -> str:
        """Get button tooltip based on current style setting"""
        if label is None:
            label = self.LABEL_MAP.get(command_id, command_id)
        
        if self.button_style == 'icons':
            return label  # Show text as tooltip when only icons are shown
        else:
            return label  # Show label as tooltip for other styles
    
    def apply_style(self, button, command_id: str, label: str = None):
        """Apply styling to a button"""
        text = self.get_button_text(command_id, label)
        tooltip = self.get_button_tooltip(command_id, label)
        
        button.setText(text)
        button.setToolTip(tooltip)
        
        # Adjust button size based on style
        if self.button_style == 'icons':
            button.setMaximumWidth(40)
            button.setMinimumWidth(40)
        else:
            button.setMaximumWidth(150)  # Default max width
            button.setMinimumWidth(80)   # Default min width


# Global instance
_button_styler = None

def get_button_styler() -> ButtonStyler:
    """Get global button styler instance"""
    global _button_styler
    if _button_styler is None:
        _button_styler = ButtonStyler()
    return _button_styler