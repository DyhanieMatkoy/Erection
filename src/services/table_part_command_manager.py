"""
Table Part Command Manager Service.

This module provides command management functionality for table parts,
bridging panel buttons with form methods and handling command discovery,
registration, and execution.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import inspect
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CommandAvailability(Enum):
    """Command availability states"""
    ALWAYS = "always"
    REQUIRES_SELECTION = "requires_selection"
    REQUIRES_ROWS = "requires_rows"
    REQUIRES_EDIT_MODE = "requires_edit_mode"
    CUSTOM = "custom"


@dataclass
class FormCommand:
    """Configuration for a form command"""
    id: str
    name: str
    method_name: str
    form_instance: Any
    availability: CommandAvailability = CommandAvailability.ALWAYS
    parameters: List[Any] = field(default_factory=list)
    enabled: bool = True
    custom_availability_check: Optional[Callable[[], bool]] = None
    
    def is_available(self, context: 'CommandContext') -> bool:
        """Check if command is available in current context"""
        if not self.enabled:
            return False
        
        if self.custom_availability_check:
            return self.custom_availability_check()
        
        if self.availability == CommandAvailability.ALWAYS:
            return True
        elif self.availability == CommandAvailability.REQUIRES_SELECTION:
            return len(context.selected_rows) > 0
        elif self.availability == CommandAvailability.REQUIRES_ROWS:
            return len(context.table_data) > 0
        elif self.availability == CommandAvailability.REQUIRES_EDIT_MODE:
            return context.additional_data.get('edit_mode', False)
        
        return True


@dataclass
class CommandContext:
    """Context information for command execution"""
    selected_rows: List[int] = field(default_factory=list)
    table_data: List[Dict[str, Any]] = field(default_factory=list)
    current_row: Optional[int] = None
    current_column: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: Optional[str] = None
    data: Any = None
    affected_rows: List[int] = field(default_factory=list)
    refresh_required: bool = False


class ICommandDiscovery(ABC):
    """Interface for command discovery strategies"""
    
    @abstractmethod
    def discover_commands(self, form_instance: Any) -> List[FormCommand]:
        """Discover commands from a form instance"""
        pass


class AttributeBasedDiscovery(ICommandDiscovery):
    """Discovers commands based on method attributes"""
    
    def discover_commands(self, form_instance: Any) -> List[FormCommand]:
        """
        Discover commands by looking for methods with table_command attribute.
        
        Methods should be decorated with @table_command decorator.
        """
        commands = []
        
        for method_name in dir(form_instance):
            if method_name.startswith('_'):
                continue
                
            method = getattr(form_instance, method_name)
            if not callable(method):
                continue
            
            # Check if method has table_command attribute
            if hasattr(method, '_table_command_config'):
                config = method._table_command_config
                command = FormCommand(
                    id=config.get('id', method_name),
                    name=config.get('name', method_name.replace('_', ' ').title()),
                    method_name=method_name,
                    form_instance=form_instance,
                    availability=config.get('availability', CommandAvailability.ALWAYS),
                    parameters=config.get('parameters', []),
                    enabled=config.get('enabled', True)
                )
                commands.append(command)
        
        return commands


class NamingConventionDiscovery(ICommandDiscovery):
    """Discovers commands based on naming conventions"""
    
    COMMAND_PATTERNS = {
        'add_row': ('add_row', 'add_table_row', 'insert_row', 'create_row'),
        'delete_row': ('delete_row', 'remove_row', 'delete_selected', 'remove_selected'),
        'move_up': ('move_up', 'move_row_up', 'row_up'),
        'move_down': ('move_down', 'move_row_down', 'row_down'),
        'import_data': ('import_data', 'import_rows', 'load_data'),
        'export_data': ('export_data', 'export_rows', 'save_data'),
        'print_data': ('print_data', 'print_table', 'print_rows')
    }
    
    def discover_commands(self, form_instance: Any) -> List[FormCommand]:
        """Discover commands based on method naming patterns"""
        commands = []
        
        for command_id, patterns in self.COMMAND_PATTERNS.items():
            for pattern in patterns:
                if hasattr(form_instance, pattern):
                    method = getattr(form_instance, pattern)
                    if callable(method):
                        # Determine availability based on command type
                        availability = self._get_default_availability(command_id)
                        
                        command = FormCommand(
                            id=command_id,
                            name=self._get_default_name(command_id),
                            method_name=pattern,
                            form_instance=form_instance,
                            availability=availability
                        )
                        commands.append(command)
                        break  # Use first matching pattern
        
        return commands
    
    def _get_default_availability(self, command_id: str) -> CommandAvailability:
        """Get default availability for standard commands"""
        if command_id in ['delete_row', 'move_up', 'move_down']:
            return CommandAvailability.REQUIRES_SELECTION
        elif command_id in ['export_data']:
            return CommandAvailability.REQUIRES_ROWS
        else:
            return CommandAvailability.ALWAYS
    
    def _get_default_name(self, command_id: str) -> str:
        """Get default display name for standard commands"""
        names = {
            'add_row': 'Добавить строку',
            'delete_row': 'Удалить строки',
            'move_up': 'Переместить выше',
            'move_down': 'Переместить ниже',
            'import_data': 'Импорт данных',
            'export_data': 'Экспорт данных',
            'print_data': 'Печать данных'
        }
        return names.get(command_id, command_id.replace('_', ' ').title())


class TablePartCommandManager:
    """
    Command manager for table parts.
    
    Provides functionality to:
    - Discover commands from form instances
    - Register and manage form commands
    - Execute commands with proper context
    - Handle command availability and state updates
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
    """
    
    def __init__(self, discovery_strategies: Optional[List[ICommandDiscovery]] = None):
        """
        Initialize command manager.
        
        Args:
            discovery_strategies: List of command discovery strategies to use
        """
        self.registered_commands: Dict[str, FormCommand] = {}
        self.discovery_strategies = discovery_strategies or [
            AttributeBasedDiscovery(),
            NamingConventionDiscovery()
        ]
        self.command_state_cache: Dict[str, bool] = {}
        self.last_context: Optional[CommandContext] = None
    
    def discover_and_register_commands(self, form_instance: Any) -> List[FormCommand]:
        """
        Discover and register commands from a form instance.
        
        Args:
            form_instance: Form instance to discover commands from
            
        Returns:
            List of discovered and registered commands
            
        Requirements: 2.1, 2.2
        """
        discovered_commands = []
        
        for strategy in self.discovery_strategies:
            try:
                commands = strategy.discover_commands(form_instance)
                discovered_commands.extend(commands)
                logger.info(f"Discovered {len(commands)} commands using {strategy.__class__.__name__}")
            except Exception as e:
                logger.warning(f"Command discovery failed with {strategy.__class__.__name__}: {e}")
        
        # Register discovered commands
        for command in discovered_commands:
            self.register_command(command)
        
        logger.info(f"Total registered commands: {len(self.registered_commands)}")
        return discovered_commands
    
    def register_command(self, command: FormCommand):
        """
        Register a form command.
        
        Args:
            command: Form command to register
            
        Requirements: 2.2
        """
        self.registered_commands[command.id] = command
        logger.debug(f"Registered command: {command.id} -> {command.method_name}")
    
    def unregister_command(self, command_id: str):
        """
        Unregister a form command.
        
        Args:
            command_id: ID of command to unregister
        """
        if command_id in self.registered_commands:
            del self.registered_commands[command_id]
            logger.debug(f"Unregistered command: {command_id}")
    
    def execute_command(self, command_id: str, context: CommandContext) -> CommandResult:
        """
        Execute a registered command.
        
        Args:
            command_id: ID of command to execute
            context: Execution context
            
        Returns:
            Command execution result
            
        Requirements: 2.3, 2.4
        """
        if command_id not in self.registered_commands:
            return CommandResult(
                success=False,
                message=f"Command '{command_id}' not found"
            )
        
        command = self.registered_commands[command_id]
        
        # Check availability
        if not command.is_available(context):
            return CommandResult(
                success=False,
                message=f"Command '{command_id}' is not available in current context"
            )
        
        try:
            # Get the method from form instance
            method = getattr(command.form_instance, command.method_name)
            
            # Prepare method arguments
            args = self._prepare_method_arguments(method, command, context)
            
            # Execute the method
            result = method(*args)
            
            # Handle different return types
            if isinstance(result, CommandResult):
                return result
            elif isinstance(result, bool):
                return CommandResult(
                    success=result,
                    message="Command executed" if result else "Command failed"
                )
            else:
                return CommandResult(
                    success=True,
                    message="Command executed successfully",
                    data=result
                )
        
        except Exception as e:
            logger.error(f"Command execution failed for '{command_id}': {e}")
            return CommandResult(
                success=False,
                message=f"Command execution failed: {str(e)}"
            )
    
    def _prepare_method_arguments(
        self,
        method: Callable,
        command: FormCommand,
        context: CommandContext
    ) -> List[Any]:
        """Prepare arguments for method execution based on signature"""
        sig = inspect.signature(method)
        args = []
        
        # Add predefined parameters
        args.extend(command.parameters)
        
        # Add context-based parameters if method expects them
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            elif param_name == 'context':
                args.append(context)
            elif param_name == 'selected_rows':
                args.append(context.selected_rows)
            elif param_name == 'table_data':
                args.append(context.table_data)
            elif param_name == 'current_row':
                args.append(context.current_row)
            elif param_name == 'current_column':
                args.append(context.current_column)
        
        return args
    
    def update_command_states(self, context: CommandContext) -> Dict[str, bool]:
        """
        Update command availability states.
        
        Args:
            context: Current context for availability checking
            
        Returns:
            Dictionary mapping command IDs to availability states
            
        Requirements: 2.5
        """
        self.last_context = context
        states = {}
        
        for command_id, command in self.registered_commands.items():
            is_available = command.is_available(context)
            states[command_id] = is_available
            self.command_state_cache[command_id] = is_available
        
        return states
    
    def get_command_state(self, command_id: str) -> bool:
        """
        Get cached command availability state.
        
        Args:
            command_id: ID of command to check
            
        Returns:
            True if command is available, False otherwise
        """
        return self.command_state_cache.get(command_id, False)
    
    def get_available_commands(self, context: Optional[CommandContext] = None) -> List[FormCommand]:
        """
        Get list of currently available commands.
        
        Args:
            context: Context to check availability against. Uses last context if None.
            
        Returns:
            List of available commands
        """
        check_context = context or self.last_context
        if not check_context:
            return list(self.registered_commands.values())
        
        available = []
        for command in self.registered_commands.values():
            if command.is_available(check_context):
                available.append(command)
        
        return available
    
    def get_registered_commands(self) -> Dict[str, FormCommand]:
        """Get all registered commands"""
        return self.registered_commands.copy()
    
    def clear_commands(self):
        """Clear all registered commands"""
        self.registered_commands.clear()
        self.command_state_cache.clear()
        self.last_context = None


# Decorator for marking methods as table commands
def table_command(
    command_id: Optional[str] = None,
    name: Optional[str] = None,
    availability: CommandAvailability = CommandAvailability.ALWAYS,
    parameters: Optional[List[Any]] = None,
    enabled: bool = True
):
    """
    Decorator to mark methods as table commands.
    
    Args:
        command_id: Unique identifier for the command
        name: Display name for the command
        availability: When the command is available
        parameters: Default parameters for the command
        enabled: Whether the command is enabled by default
    
    Example:
        @table_command(command_id='add_row', name='Add Row', availability=CommandAvailability.ALWAYS)
        def add_new_row(self, context: CommandContext):
            # Implementation
            pass
    """
    def decorator(func):
        func._table_command_config = {
            'id': command_id or func.__name__,
            'name': name or func.__name__.replace('_', ' ').title(),
            'availability': availability,
            'parameters': parameters or [],
            'enabled': enabled
        }
        return func
    
    return decorator