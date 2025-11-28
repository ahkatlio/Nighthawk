from .base_command import BaseCommand
import google.generativeai as genai

class TokenCommand(BaseCommand):    
    def __init__(self):
        super().__init__(
            name="tokens",
            description="Show Gemini API token usage statistics",
            usage="tokens"
        )
    
    def execute(self, assistant, args: list) -> str:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        
        console = Console()
        
        if not assistant.gemini_chat:
            console.print("[yellow]⚠ Google Gemini is not initialized[/yellow]")
            return ""
        
        try:
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0
            
            for msg in assistant.conversation_history:
                tokens = len(msg.get('content', '')) // 4
                total_tokens += tokens
                
                if msg.get('role') == 'user':
                    prompt_tokens += tokens
                else:
                    completion_tokens += tokens
            
            FREE_TIER_INPUT_TPM = 1000000
            FREE_TIER_OUTPUT_TPM = 8000
            FREE_TIER_CONTEXT = 1000000
            
            prompt_pct = (prompt_tokens / FREE_TIER_INPUT_TPM) * 100 if prompt_tokens > 0 else 0
            completion_pct = (completion_tokens / FREE_TIER_OUTPUT_TPM) * 100 if completion_tokens > 0 else 0
            context_pct = (total_tokens / FREE_TIER_CONTEXT) * 100 if total_tokens > 0 else 0
            
            table = Table(title="Gemini Token Usage (Session)", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="yellow", justify="right")
            table.add_column("Limit", style="green", justify="right")
            table.add_column("Usage %", style="magenta", justify="right")
            
            table.add_row(
                "Prompt Tokens",
                f"{prompt_tokens:,}",
                f"{FREE_TIER_INPUT_TPM:,}/min",
                f"{prompt_pct:.2f}%" if prompt_pct > 0 else "0%"
            )
            
            table.add_row(
                "Completion Tokens",
                f"{completion_tokens:,}",
                f"{FREE_TIER_OUTPUT_TPM:,}/min",
                f"{completion_pct:.2f}%" if completion_pct > 0 else "0%"
            )
            
            table.add_row(
                "Total Session Tokens",
                f"{total_tokens:,}",
                f"{FREE_TIER_CONTEXT:,}",
                f"{context_pct:.4f}%" if context_pct > 0 else "0%"
            )
            
            table.add_row("", "", "", "")
            
            msg_count = len(assistant.conversation_history)
            table.add_row(
                "Conversation Messages",
                str(msg_count),
                "Unlimited",
                "-"
            )
            
            console.print(table)
            
            if context_pct < 50:
                status_color = "green"
                status_msg = "✓ Low usage - plenty of context available"
            elif context_pct < 80:
                status_color = "yellow"
                status_msg = "⚠ Moderate usage - consider clearing history soon"
            else:
                status_color = "red"
                status_msg = "⚠ High usage - clear history to free context"
            
            console.print(f"\n[{status_color}]{status_msg}[/{status_color}]")
            
            info = f"""[bold]Gemini 2.5 Flash Free Tier:[/bold]
• Input: 1,000,000 tokens/minute
• Output: 8,000 tokens/minute  
• Context: 1,000,000 tokens max
• Requests: 1,500 per day

[bold]Current Session:[/bold]
• Messages: {msg_count}
• Avg tokens/message: {total_tokens // msg_count if msg_count > 0 else 0}
• Context used: {context_pct:.4f}%

[dim]Note: Token counts are estimates (1 token ≈ 4 characters).
Use 'clear history' to free up context window.[/dim]"""
            
            console.print(Panel(info, border_style="blue", title="ℹ Info"))
            
            return ""
            
        except Exception as e:
            console.print(f"[red]Error retrieving token info: {e}[/red]")
            return ""
