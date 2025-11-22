"""
Status Command
Shows current system status including active model
"""

from .base_command import BaseCommand

class StatusCommand(BaseCommand):
    """Display current system status"""
    
    def __init__(self):
        super().__init__(
            name="status",
            description="Show current system status and active model",
            usage="status"
        )
    
    def execute(self, assistant, args: list) -> str:
        """Execute status command"""
        from rich.table import Table
        from rich import box
        from rich.console import Console
        
        console = Console()
        
        # Create status table
        table = Table(title="Nighthawk Status", box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        # Active model
        model_name = assistant.current_model.upper()
        if assistant.current_model == "ollama":
            model_name += f" ({assistant.model})"
        else:
            model_name += " (gemini-2.5-flash)"
        
        table.add_row("Active Model", model_name)
        
        # Available models
        available = ["Ollama"]
        if assistant.gemini_chat:
            available.append("Gemini")
        table.add_row("Available Models", ", ".join(available))
        
        # Scan results count
        scan_count = len([k for k in assistant.scan_results.keys() if not k.endswith('_parsed') and not k.endswith('_metasploit')])
        table.add_row("Cached Scans", str(scan_count))
        
        # Conversation history
        msg_count = len(assistant.conversation_history)
        table.add_row("Conversation Messages", str(msg_count))
        
        # Last target
        last_target = assistant.last_target or "None"
        table.add_row("Last Target", last_target)
        
        # Tools status
        tool_status = []
        for name, tool in assistant.tools.items():
            status = "✓" if tool.check_installed() else "✗"
            tool_status.append(f"{status} {name}")
        table.add_row("Tools", " | ".join(tool_status))
        
        console.print(table)
        return ""
