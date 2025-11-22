"""
Base Command Class
All CLI commands inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict

class BaseCommand(ABC):
    """Base class for all CLI commands"""
    
    def __init__(self, name: str, description: str, usage: str):
        self.name = name
        self.description = description
        self.usage = usage
    
    @abstractmethod
    def execute(self, assistant, args: list) -> str:
        """
        Execute the command
        
        Args:
            assistant: NighthawkAssistant instance
            args: Command arguments
            
        Returns:
            Output string
        """
        pass
    
    def get_help(self) -> str:
        """Get help text for this command"""
        return f"""[cyan]{self.name}[/cyan] - {self.description}
Usage: {self.usage}"""
