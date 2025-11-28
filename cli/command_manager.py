from typing import Dict, Optional
from .base_command import BaseCommand
from .status_command import StatusCommand
from .token_command import TokenCommand
from .help_command import HelpCommand
from .clear_command import ClearCommand

class CommandManager:    
    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}
        self._register_commands()
    
    def _register_commands(self):
        commands = [
            StatusCommand(),
            TokenCommand(),
            HelpCommand(),
            ClearCommand(),
        ]
        
        for command in commands:
            self.commands[command.name] = command
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        return self.commands.get(name.lower())
    
    def execute(self, name: str, assistant, args: list = None) -> bool:
        """
        Execute a command
        
        Args:
            name: Command name
            assistant: NighthawkAssistant instance
            args: Command arguments
            
        Returns:
            True if command was found and executed, False otherwise
        """
        if args is None:
            args = []
        
        command = self.get_command(name)
        if command:
            command.execute(assistant, args)
            return True
        
        return False
    
    def is_command(self, input_text: str) -> bool:
        parts = input_text.strip().split()
        if not parts:
            return False
        
        command_name = parts[0].lower()
        return command_name in self.commands
    
    def parse_and_execute(self, input_text: str, assistant) -> bool:
        """
        Parse input and execute command if it's a CLI command
        
        Args:
            input_text: User input
            assistant: NighthawkAssistant instance
            
        Returns:
            True if command was executed, False if not a command
        """
        parts = input_text.strip().split()
        if not parts:
            return False
        
        command_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        return self.execute(command_name, assistant, args)
