from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class CommandDefinition(BaseModel):
    id: str
    category: str # 'standard', 'form', 'global'
    name: str
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    description: Optional[str] = None
    requires_selection: bool = False
    requires_single_selection: bool = False
    is_group: bool = False
    children: List['CommandDefinition'] = []

class StandardCommandRegistry:
    """Registry of all available commands in the system"""
    
    _commands: Dict[str, CommandDefinition] = {}
    
    @classmethod
    def register(cls, command: CommandDefinition):
        cls._commands[command.id] = command
        
    @classmethod
    def get(cls, command_id: str) -> Optional[CommandDefinition]:
        return cls._commands.get(command_id)
        
    @classmethod
    def get_all(cls) -> List[CommandDefinition]:
        return list(cls._commands.values())

    @classmethod
    def get_for_form_type(cls, form_type: str) -> List[CommandDefinition]:
        # specific logic to return commands relevant for a form type
        # For now, return all standard commands + specific ones
        return cls.get_all() # Simplified

# Initialize Standard Commands
def _init_standard_commands():
    commands = [
        CommandDefinition(id="create", category="standard", name="Create", icon="plus", shortcut="Insert"),
        CommandDefinition(id="copy", category="standard", name="Copy", icon="copy", shortcut="F9", requires_selection=True, requires_single_selection=True),
        CommandDefinition(id="edit", category="standard", name="Edit", icon="edit", shortcut="F2", requires_selection=True, requires_single_selection=True),
        CommandDefinition(id="delete", category="standard", name="Delete", icon="trash", shortcut="Del", requires_selection=True),
        CommandDefinition(id="post", category="standard", name="Post", icon="check", shortcut="Ctrl+Enter", requires_selection=True),
        CommandDefinition(id="unpost", category="standard", name="Unpost", icon="x", requires_selection=True),
        CommandDefinition(id="refresh", category="standard", name="Refresh", icon="refresh", shortcut="F5"),
        CommandDefinition(id="print", category="standard", name="Print", icon="printer", requires_selection=True, is_group=True),
    ]
    for cmd in commands:
        StandardCommandRegistry.register(cmd)

_init_standard_commands()
