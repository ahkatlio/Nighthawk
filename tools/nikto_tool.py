"""
Nikto web scanner tool integration (Template - requires nikto installation)
"""

import subprocess
import re
from typing import Dict, Optional
from .base_tool import BaseTool
from rich.console import Console

console = Console()


class NiktoTool(BaseTool):
    """Nikto web vulnerability scanner integration"""
    
    def __init__(self):
        super().__init__(name="nikto", command="nikto")
    
    def check_installed(self) -> bool:
        """Check if nikto is installed"""
        try:
            result = subprocess.run(
                ["nikto", "-Version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                console.print(f"[green]✓[/green] Nikto detected")
                return True
            return False
        except Exception:
            return False
    
    def generate_command(self, user_request: str, ai_response: str) -> Optional[str]:
        """Extract nikto command from AI response"""
        command = None
        
        for line in ai_response.split('\n'):
            line = line.strip()
            if line.startswith('```'):
                continue
            if line.startswith('`') and line.endswith('`'):
                line = line.strip('`')
            if line.startswith('nikto'):
                command = line
                break
        
        return command
    
    def execute(self, command: str) -> Dict[str, any]:
        """Execute nikto command"""
        return self.run_command(command, timeout=600)  # 10 min timeout
    
    def format_output(self, output: str) -> str:
        """Format nikto output"""
        return output
    
    def get_ai_prompt(self) -> str:
        """Get the AI system prompt for nikto"""
        return """You are a web security expert specializing in Nikto vulnerability scanning.

When generating nikto commands:
1. Use format: nikto -h [target]
2. Add appropriate flags for the scan type
3. Extract hostname/domain from URLs

Common options:
- Basic scan: nikto -h target.com
- With SSL: nikto -h https://target.com
- Custom port: nikto -h target.com -p 8080
- Output to file: nikto -h target.com -o output.txt

Respond with ONLY the nikto command."""
