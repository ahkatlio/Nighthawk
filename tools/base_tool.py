"""
Base class for all security tools
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import subprocess
from rich.console import Console

console = Console()


class BaseTool(ABC):
    """Base class for security tool integrations"""
    
    def __init__(self, name: str, command: str):
        self.name = name
        self.command = command
        self.console = Console()
    
    @abstractmethod
    def check_installed(self) -> bool:
        """Check if the tool is installed"""
        pass
    
    @abstractmethod
    def generate_command(self, user_request: str, ai_response: str) -> Optional[str]:
        """Generate tool command from user request and AI response"""
        pass
    
    @abstractmethod
    def execute(self, command: str) -> Dict[str, any]:
        """Execute the tool command"""
        pass
    
    @abstractmethod
    def format_output(self, output: str) -> str:
        """Format the tool output for display"""
        pass
    
    def run_command(self, command: str, timeout: int = 300) -> Dict[str, any]:
        """Generic command execution with timeout"""
        try:
            console.print(f"\n[bold cyan]Executing:[/bold cyan] {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "tool": self.name
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "returncode": -1,
                "tool": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "tool": self.name
            }
