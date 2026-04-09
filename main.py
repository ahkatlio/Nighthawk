import sys
import os
import re
import asyncio
from typing import Optional, Dict
from urllib.parse import urlparse
import ollama
try:
    import google.generativeai as genai
    from google.generativeai.types import FunctionDeclaration, Tool
except ImportError:
    genai = None
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from tools.mcp_client import MCPToolClient
from cli.command_manager import CommandManager

load_dotenv()

console = Console()


class NighthawkAssistant:
    """AI-powered security assistant with MCP tool support"""
    
    def __init__(self, model: str = "dolphin-llama3:8b"):
        self.model = model
        self.current_model = "ollama"
        self.console = Console()
        self.conversation_history = []
        self.scan_results = {}
        self.last_target = None
        
        self.command_manager = CommandManager()
        self.gemini_chat = None
        self._init_gemini()
        self.mcp_client = MCPToolClient()
    
    def _init_gemini(self):
        """Initialize Google Gemini API"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction="You are Nighthawk, an advanced security expert assistant. Help with security scanning, provide clear insights, use tools when needed, and remember conversation context."
                )
                self.gemini_chat = model.start_chat(history=[])
                console.print("[dim green]✓ Google Gemini initialized[/dim green]")
            else:
                console.print("[dim yellow]⚠ Google API key not found - Gemini unavailable[/dim yellow]")
        except Exception as e:
            console.print(f"[dim yellow]⚠ Gemini initialization failed: {e}[/dim yellow]")
            self.gemini_chat = None

    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            ollama.list()
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] Cannot connect to Ollama: {e}")
            self.console.print("[yellow]Make sure Ollama is running with: ollama serve[/yellow]")
            return False
            
    def switch_model(self, model_name: str) -> bool:
        """Switch between AI models"""
        model_name = model_name.lower()
        if model_name in ["ollama", "dolphin", "local"]:
            self.current_model = "ollama"
            self.console.print(f"[green]✓ Switched to Ollama ({self.model})[/green]")
            return True
        elif model_name in ["gemini", "google"]:
            if self.gemini_chat:
                self.current_model = "gemini"
                self.console.print("[green]✓ Switched to Google Gemini 2.5 Flash[/green]")
                return True
            else:
                self.console.print("[red]✗ Gemini is not available. Check your API key in .env file.[/red]")
                return False
        else:
            self.console.print(f"[red]✗ Unknown model: {model_name}[/red]")
            return False

    def cleanup(self):
        """Clean up temporary data (called on exit)"""
        self.conversation_history.clear()
        self.scan_results.clear()
        self.console.print("[dim]Memory cleared - all conversation and scan data deleted[/dim]")

    async def show_tools(self):
        """Show available tools directly from MCP server"""
        tools = await self.mcp_client.get_tools()
        table = Table(title="Available MCP Tools", box=box.ROUNDED)
        table.add_column("Tool", style="cyan")
        table.add_column("Description", style="yellow")
        for tool in tools:
            table.add_row(tool['name'], tool.get('description', ''))
        self.console.print(table)
    
    # ---------------------------------------------------------
    # NEW: NATIVE MCP TOOL CALLING
    # ---------------------------------------------------------

    async def process_request(self, user_input: str, log_callback=None) -> str:
        """Handles the native AI tool calling loop using the active model."""
        def log(msg):
            self.console.print(msg)
            if log_callback:
                log_callback(msg)
                
        try:
            tools_schema = await self.mcp_client.get_tools()
        except Exception as e:
            return f"Error retrieving tools from MCP Server: {e}"
        
        self.conversation_history.append({"role": "user", "content": user_input})
        
        if self.current_model == "gemini" and self.gemini_chat:
            return await self._chat_gemini_with_tools(user_input, tools_schema, log)
        else:
            return await self._chat_ollama_with_tools(tools_schema, log)

    async def _chat_gemini_with_tools(self, user_input: str, tools_schema, log_callback) -> str:
        # Convert MCP schema to Gemini FunctionDeclarations loosely
        formatted_tools = []
        for t in tools_schema:
            try:
                schema_properties = t.get("inputSchema", {}).get("properties", {})
                required = t.get("inputSchema", {}).get("required", [])
                formatted_tools.append(
                    {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("inputSchema", {})
                    }
                )
            except:
                pass
                
        try:
            sys_msg = (
                "You are an AI assistant orchestrating security tools. You have access to these tools: " + str(formatted_tools) + 
                "\n\nCRITICAL INSTRUCTION: To execute a tool, your response MUST be a dictionary EXACTLY in this format:"
                "\n{'tool_call': 'tool_name', 'arguments': {'parameter_name': 'parameter_value'}}"
                "\n\nDO NOT write Python code (like print(tool())). DO NOT use 'tool_code'. ONLY use the format above."
            )
            
            response = self.gemini_chat.send_message(
                sys_msg + "\n\nUser message: " + user_input
            )
            
            if "{" in response.text and "}" in response.text:
                try:
                    import ast
                    import json
                    import re
                    start = response.text.find("{")
                    end = -1
                    if start != -1:
                        brace_count = 0
                        for i in range(start, len(response.text)):
                            if response.text[i] == '{':
                                brace_count += 1
                            elif response.text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i
                                    break
                                    
                    if start != -1 and end != -1:
                        dict_str = response.text[start:end+1]
                        call_data = None
                        
                        try:
                            call_data = json.loads(dict_str)
                        except Exception:
                            try:
                                modified_str = dict_str.replace("'", '"')
                                modified_str = re.sub(r'\bTrue\b', 'true', modified_str)
                                modified_str = re.sub(r'\bFalse\b', 'false', modified_str)
                                modified_str = re.sub(r'\bNone\b', 'null', modified_str)
                                call_data = json.loads(modified_str)
                            except Exception:
                                try:
                                    call_data = ast.literal_eval(dict_str)
                                except Exception:
                                    pass
                                    
                        if call_data and isinstance(call_data, dict):
                            tool_name = call_data.get('tool_call') or call_data.get('name')
                            if tool_name:
                                args = call_data.get('arguments', {})
                                safe_args_str = str(args).replace("[", "\\[")
                                log_callback(f"\n[yellow]🛠 Executing tool via Gemini:[/yellow] {tool_name}\n[dim]{safe_args_str}[/dim]")
                                
                                result = await self.mcp_client.execute_tool(tool_name, args)
                                log_callback(f"[green]✓ Tool succeeded.[/green] [dim]Output ({len(str(result))} chars)[/dim] Analyzing results...")
                                
                                follow_up = self.gemini_chat.send_message("Tool returned: " + str(result) + "\n\nPlease summarize the findings.")
                                final_text = follow_up.text
                                self.conversation_history.append({"role": "assistant", "content": final_text})
                                return final_text
                except Exception as e:
                    log_callback(f"[dim yellow]⚠ Gemini dictionary parsing failed: {e}[/dim yellow]")
            
            self.conversation_history.append({"role": "assistant", "content": response.text})
            return response.text
        except Exception as e:
            log_callback(f"[dim yellow]⚠ Gemini error: {e}[/dim yellow]")
            return f"Error communicating with Gemini: {e}"

    async def _chat_ollama_with_tools(self, tools_schema, log_callback) -> str:
        formatted_tools = []
        for t in tools_schema:
            formatted_tools.append({
                "name": t.get("name"),
                "description": t.get("description", ""),
                "parameters": t.get("inputSchema", {})
            })
            
        sys_msg = (
            "You are an AI assistant orchestrating security tools. You have access to these tools: " + str(formatted_tools) + 
            "\n\nCRITICAL INSTRUCTION: To execute a tool, your response MUST be a dictionary EXACTLY in this format:"
            "\n{'tool_call': 'tool_name', 'arguments': {'parameter_name': 'parameter_value'}}"
            "\n\nDO NOT write Python code (like print(tool())). DO NOT use 'tool_code'. ONLY use the dictionary format above and nothing else."
        )
        
        messages = [{"role": "system", "content": sys_msg}] + self.conversation_history
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            response_message = response.get('message', {})
            response_text = response_message.get('content', '')
            
            if "{" in response_text and "}" in response_text:
                try:
                    import ast
                    import json
                    import re
                    
                    # 1. Find the first '{' and precisely match its closing '}'
                    start = response_text.find("{")
                    end = -1
                    if start != -1:
                        brace_count = 0
                        for i in range(start, len(response_text)):
                            if response_text[i] == '{':
                                brace_count += 1
                            elif response_text[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end = i
                                    break
                                    
                    if start != -1 and end != -1:
                        dict_str = response_text[start:end+1]
                        
                        call_data = None
                        try:
                            # Try parsing as strict JSON first
                            call_data = json.loads(dict_str)
                        except Exception:
                            try:
                                # Fallback 1: Replace single quotes with double quotes for valid JSON
                                modified_str = dict_str.replace("'", '"')
                                # Fix python booleans/none if they were generated
                                modified_str = re.sub(r'\bTrue\b', 'true', modified_str)
                                modified_str = re.sub(r'\bFalse\b', 'false', modified_str)
                                modified_str = re.sub(r'\bNone\b', 'null', modified_str)
                                call_data = json.loads(modified_str)
                            except Exception:
                                # Fallback 2: AST Eval for Python dictionary representation
                                try:
                                    call_data = ast.literal_eval(dict_str)
                                except Exception:
                                    pass
                                    
                        if call_data and isinstance(call_data, dict):
                            tool_name = call_data.get('tool_call') or call_data.get('name')
                            arguments = call_data.get('arguments', {})
                            
                            # Extreme fallback if dolphin-llama3 output `{'tool_code': "print(nikto_scan(target='...'))"}`
                            tool_code_fallback = call_data.get('tool_code', '')
                            if not tool_name and tool_code_fallback:
                                match = re.search(r'([a-zA-Z0-9_]+)\(', str(tool_code_fallback))
                                if match:
                                    tool_name = match.group(1)
                                    args_match = re.search(r'target=[\'"]([^\'"]+)[\'"]', str(tool_code_fallback))
                                    if args_match:
                                        arguments = {'target': args_match.group(1)}

                            if tool_name:
                                safe_args_str = str(arguments).replace("[", "\\[")
                                log_callback(f"\n[yellow]🛠 Executing tool via Ollama:[/yellow] {tool_name}\n[dim]{safe_args_str}[/dim]")
                                
                                try:
                                    tool_result = await self.mcp_client.execute_tool(tool_name, arguments)
                                    log_callback(f"[green]✓ Tool succeeded.[/green] [dim]Output ({len(str(tool_result))} chars)[/dim] Analyzing results...")
                                except Exception as e:
                                    tool_result = f"Error running {tool_name}: {e}"
                                    log_callback(f"[red]❌ Tool failed:[/red] {e}")
                                    
                                self.conversation_history.append({"role": "assistant", "content": response_text})
                                self.conversation_history.append({
                                    "role": "user",
                                    "content": f"Tool '{tool_name}' returned: {tool_result}\n\nPlease summarize the findings."
                                })
                                
                                return await self._chat_ollama_with_tools(tools_schema, log_callback)
                except Exception as e:
                    log_callback(f"[dim yellow]⚠ Could not parse tool call dict:[/dim yellow] {e}")
                    pass # Continue outputting raw text if everything fails
                
            self.conversation_history.append({"role": "assistant", "content": response_text})
            return response_text

            
        except Exception as e:
            return f"Error with Ollama: {e}"

    # ---------------------------------------------------------
    # INTERACTIVE CLI MODE
    # ---------------------------------------------------------

    async def run_interactive(self):
        model_status = f"Ollama ({self.model})"
        if self.gemini_chat:
            model_status += " + Gemini 2.5 Flash"
        
        self.console.print(Panel.fit(
            "[bold cyan]Nighthawk Security Assistant[/bold cyan]\n"
            "AI-powered security tool orchestrator with MCP\n\n"
            f"Models: {model_status}\n"
            f"Active: [bold]{self.current_model}[/bold]\n",
            border_style="cyan",
            title="🦅 Nighthawk",
            subtitle="MCP Enabled"
        ))
        
        if not self.check_ollama_connection():
            return
            
        await self.mcp_client.connect()
        self.console.print("\n[green]✓[/green] MCP Server Connected!")
        self.console.print("\n[yellow]Commands:[/yellow]")
        self.console.print("  - Type your request directly (e.g. 'scan target.com', 'what is port 80?')")
        self.console.print("  - Type 'tools' to see available MCP tools")
        self.console.print("  - Type 'quit' to exit\n")

        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.cleanup()
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break
                    
                if user_input.lower() == 'tools':
                    await self.show_tools()
                    continue
                    
                if user_input.lower().startswith('model '):
                    self.switch_model(user_input[6:].strip())
                    continue
                    
                if not user_input.strip():
                    continue

                if self.command_manager.parse_and_execute(user_input, self):
                    continue

                ai_response = await self.process_request(user_input)
                self.console.print(Panel(Markdown(ai_response), title="Nighthawk", border_style="cyan"))
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                self.console.print(f"[bold red]Error in main loop:[/bold red] {e}")
                
        await self.mcp_client.close()

    def interactive_mode(self):
        """Wrapper for old non-async calls"""
        asyncio.run(self.run_interactive())


def main():
    """Main entry point"""
    assistant = NighthawkAssistant()
    assistant.interactive_mode()

if __name__ == "__main__":
    main()
