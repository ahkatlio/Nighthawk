from .base_command import BaseCommand

class ClearCommand(BaseCommand):
    """Clear cached data"""
    
    def __init__(self):
        super().__init__(
            name="clear",
            description="Clear conversation history and scan results",
            usage="clear [history|scans|all]"
        )
    
    def execute(self, assistant, args: list) -> str:
        from rich.console import Console
        
        console = Console()
        
        target = args[0].lower() if args else "all"
        
        if target in ["history", "all"]:
            msg_count = len(assistant.conversation_history)
            assistant.conversation_history.clear()
            console.print(f"[green]✓ Cleared {msg_count} conversation messages[/green]")
        
        if target in ["scans", "all"]:
            scan_count = len(assistant.scan_results)
            assistant.scan_results.clear()
            assistant.last_target = None
            console.print(f"[green]✓ Cleared {scan_count} scan results[/green]")
        
        if target == "all":
            console.print("[green]✓ All data cleared[/green]")
        
        if target not in ["history", "scans", "all"]:
            console.print(f"[red]Unknown target: {target}[/red]")
            console.print("[yellow]Usage: clear [history|scans|all][/yellow]")
        
        return ""
