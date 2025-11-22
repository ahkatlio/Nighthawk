"""
Help Command
Shows all available CLI commands
"""

from .base_command import BaseCommand

class HelpCommand(BaseCommand):
    """Display help for all commands"""
    
    def __init__(self):
        super().__init__(
            name="help",
            description="Show all available CLI commands",
            usage="help [command]"
        )
    
    def execute(self, assistant, args: list) -> str:
        """Execute help command"""
        from rich.console import Console
        from rich.table import Table
        from rich import box
        from rich.panel import Panel
        
        console = Console()
        
        # Get command manager from assistant
        if not hasattr(assistant, 'command_manager'):
            console.print("[red]Command manager not initialized[/red]")
            return ""
        
        # If specific command requested
        if args:
            command_name = args[0].lower()
            command = assistant.command_manager.get_command(command_name)
            if command:
                console.print(Panel(command.get_help(), border_style="cyan", title="Command Help"))
            else:
                console.print(f"[red]Unknown command: {command_name}[/red]")
            return ""
        
        # Show all commands
        table = Table(title="Available CLI Commands", box=box.ROUNDED)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="yellow")
        table.add_column("Usage", style="green")
        
        for cmd_name, command in sorted(assistant.command_manager.commands.items()):
            table.add_row(cmd_name, command.description, command.usage)
        
        console.print(table)
        
        # Add usage info
        info = """[bold]How to use CLI commands:[/bold]
Type the command name at the prompt, e.g., [cyan]status[/cyan], [cyan]help[/cyan], [cyan]tokens[/cyan]

For detailed help on a specific command: [cyan]help <command>[/cyan]

[bold]Regular commands:[/bold]
• [cyan]tools[/cyan] - Show available security tools
• [cyan]model <name>[/cyan] - Switch AI models (ollama/gemini)
• [cyan]quit[/cyan] - Exit Nighthawk"""
        
        console.print(Panel(info, border_style="blue", title="ℹ Usage"))
        
        return ""
