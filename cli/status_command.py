from .base_command import BaseCommand

class StatusCommand(BaseCommand):    
    def __init__(self):
        super().__init__(
            name="status",
            description="Show current system status and active model",
            usage="status"
        )
    
    def execute(self, assistant, args: list) -> str:
        from rich.table import Table
        from rich import box
        from rich.console import Console
        
        console = Console()
        
        table = Table(title="Nighthawk Status", box=box.ROUNDED, show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="yellow")
        
        model_name = assistant.current_model.upper()
        if assistant.current_model == "ollama":
            model_name += f" ({assistant.model})"
        else:
            model_name += " (Gemini 2.5 Flash - Chat)"
        
        table.add_row("Active Model", model_name)
        
        if assistant.gemini_chat:
            table.add_row("Exploitation AI", "Auto-fallback (2.5 Pro → 2.0 Flash → Ollama)")
        else:
            table.add_row("Exploitation AI", "Ollama only")
        
        available = ["Ollama (Local)"]
        if assistant.gemini_chat:
            available.append("Gemini 2.5 Pro (Primary)")
            available.append("Gemini 2.0 Flash (Fast)")
        table.add_row("AI Models", ", ".join(available))
        table.add_row("Fallback Chain", "2.5 Pro → 2.0 Flash → Ollama" if assistant.gemini_chat else "Ollama only")
        
        scan_count = len([k for k in assistant.scan_results.keys() if not k.endswith('_parsed') and not k.endswith('_metasploit')])
        table.add_row("Cached Scans", str(scan_count))
        
        msg_count = len(assistant.conversation_history)
        table.add_row("Conversation Messages", str(msg_count))
        
        last_target = assistant.last_target or "None"
        table.add_row("Last Target", last_target)
        
        tool_status = []
        for name, tool in assistant.tools.items():
            status = "✓" if tool.check_installed() else "✗"
            tool_status.append(f"{status} {name}")
        table.add_row("Tools", " | ".join(tool_status))
        
        console.print(table)
        return ""
