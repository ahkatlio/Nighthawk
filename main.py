#!/usr/bin/env python3
"""
Nighthawk Security Assistant
AI-powered security tool orchestrator using Ollama
"""

import sys
import re
from typing import Optional, Dict
from urllib.parse import urlparse
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
from rich import box

from tools.nmap_tool import NmapTool
from tools.metasploit_tool import MetasploitTool
from tools.base_tool import BaseTool

console = Console()


class NighthawkAssistant:
    """AI-powered security assistant with modular tool support"""
    
    def __init__(self, model: str = "dolphin-llama3:8b"):
        self.model = model
        self.console = Console()
        self.tools = {}
        self.active_tool = None
        self.conversation_history = []  # Temporary conversation storage
        self.scan_results = {}  # Temporary scan results storage (stores tool outputs)
        self.last_target = None  # Remember the last scanned target
        
        # Register available tools
        self._register_tools()
    
    def _register_tools(self):
        """Register all available security tools"""
        # Add Nmap
        nmap = NmapTool()
        self.tools['nmap'] = nmap
        
        # Add Metasploit
        metasploit = MetasploitTool()
        self.tools['metasploit'] = metasploit
        
        # Future tools will be added here:
        # self.tools['nikto'] = NiktoTool()
        # self.tools['sqlmap'] = SQLMapTool()
        # etc.
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            ollama.list()
            return True
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Cannot connect to Ollama: {e}")
            console.print("[yellow]Make sure Ollama is running with: ollama serve[/yellow]")
            return False
    
    def check_tools(self) -> bool:
        """Check which tools are installed"""
        console.print("\n[yellow]Checking installed tools...[/yellow]")
        all_ok = True
        for name, tool in self.tools.items():
            if not tool.check_installed():
                console.print(f"[red]✗[/red] {name} not found")
                all_ok = False
        return all_ok
    
    def extract_hostname(self, text: str) -> Optional[str]:
        """Extract hostname from URL or text"""
        # Try to find URLs in the text
        url_pattern = r'https?://([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?)'
        matches = re.findall(url_pattern, text)
        if matches:
            return matches[0]
        
        # Try to parse as URL
        try:
            parsed = urlparse(text)
            if parsed.netloc:
                return parsed.netloc
            elif parsed.path and '.' in parsed.path:
                return parsed.path.split('/')[0]
        except:
            pass
        
        return None
    
    def is_scan_request(self, user_request: str) -> bool:
        """Determine if user wants to scan or just chat"""
        scan_keywords = [
            'scan', 'nmap', 'port', 'detect', 'find', 'check',
            'vulnerability', 'exploit', 'enumerate', 'discover',
            'test', 'probe', 'analyze target', 'security check',
            'open ports', 'services running', 'os detection',
            'stealth', 'udp scan', 'tcp scan'
        ]
        
        # Exclude casual conversation patterns
        casual_patterns = [
            r'^(hi|hello|hey|yo)\b',
            r'\b(my name is|i am|i\'m)\b',
            r'^(thanks|thank you|thx)',
            r'^(how are you|what\'s up|sup)',
            r'^(help|info|about)',
            r'\b(weather|time|date)\b'
        ]
        
        request_lower = user_request.lower()
        
        # Check if it's casual conversation
        for pattern in casual_patterns:
            if re.search(pattern, request_lower):
                return False
        
        # Check if it contains scan keywords
        for keyword in scan_keywords:
            if keyword in request_lower:
                return True
        
        # If contains IP address or domain-like pattern with action words
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', request_lower):
            return True
        if re.search(r'https?://', request_lower) and any(k in request_lower for k in ['scan', 'check', 'test']):
            return True
        
        return False
    
    def detect_tool(self, user_request: str, ai_response: str) -> Optional[str]:
        """Detect which tool to use based on request and AI response"""
        # Check for tool keywords in AI response
        for tool_name in self.tools.keys():
            if tool_name in ai_response.lower():
                return tool_name
        
        # Fallback: check user request
        for tool_name in self.tools.keys():
            if tool_name in user_request.lower():
                return tool_name
        
        return None
    
    def ask_ollama(self, user_request: str, tool_context: Optional[str] = None, 
                   output_to_analyze: Optional[str] = None, is_casual: bool = False) -> str:
        """Ask Ollama to interpret user request or analyze tool output"""
        
        if output_to_analyze:
            # Analysis mode - include previous context
            system_prompt = """You are a security expert analyzing scan results.
Provide clear, actionable insights. Remember previous scan results to give comprehensive advice."""
            
            # Include recent scan results in context
            context = ""
            if self.scan_results:
                context = "\n\nPrevious scan results for context:\n"
                for target, result in list(self.scan_results.items())[-3:]:  # Last 3 scans
                    context += f"- {target}: {result[:200]}...\n"
            
            prompt = f"""Analyze this security scan output:{context}

{output_to_analyze}

Provide:
1. Summary of findings
2. Key discoveries (ports, services, vulnerabilities)
3. Security concerns
4. Recommended next steps (consider previous scans if relevant)"""
        
        elif is_casual:
            # Casual conversation mode
            system_prompt = """You are Nighthawk, a friendly security assistant.
You can have normal conversations AND help with security scanning.
Be helpful, conversational, and remember context.
Don't try to scan things unless the user explicitly asks for it."""
            
            prompt = user_request
        
        else:
            # Command generation mode
            if tool_context:
                system_prompt = tool_context
            else:
                system_prompt = """You are a Kali Linux security expert.
Help users with security scanning tasks by generating appropriate tool commands.
Respond with ONLY the command to execute, nothing else."""
            
            prompt = f"""User request: {user_request}

Generate the appropriate security tool command.
Respond with ONLY the command (one line, no explanations)."""
        
        try:
            # Build messages with conversation history for context
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history (last 5 messages)
            for msg in self.conversation_history[-5:]:
                messages.append(msg)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            ai_message = response['message']['content']
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": user_request})
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            
            return ai_message
        except Exception as e:
            return f"Error communicating with Ollama: {e}"
    
    def display_results(self, output: str, tool_name: str):
        """Display tool results in a formatted way"""
        console.print(f"\n[bold green]{tool_name.upper()} Results:[/bold green]")
        syntax = Syntax(output, "text", theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title=f"{tool_name} Output", border_style="green"))
    
    def display_analysis(self, analysis: str):
        """Display AI analysis of results"""
        console.print("\n[bold magenta]AI Analysis:[/bold magenta]")
        md = Markdown(analysis)
        console.print(Panel(md, title="Security Insights", border_style="magenta"))
    
    def interactive_mode(self):
        """Run interactive mode"""
        console.print(Panel.fit(
            "[bold cyan]Nighthawk Security Assistant[/bold cyan]\n"
            "AI-powered security tool orchestrator\n\n"
            f"Model: {self.model}\n"
            f"Tools: {', '.join(self.tools.keys())}",
            border_style="cyan",
            title="🦅 Nighthawk",
            subtitle="Powered by Ollama"
        ))
        
        # Check prerequisites
        if not self.check_ollama_connection():
            return
        
        if not self.check_tools():
            console.print("\n[yellow]Warning: Some tools are not available[/yellow]")
        
        console.print("\n[green]✓[/green] System ready!")
        console.print("\n[yellow]Commands:[/yellow]")
        console.print("  - Type your request in natural language")
        console.print("  - Type 'tools' to see available tools")
        console.print("  - Type 'quit' or 'exit' to leave\n")
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    # Clear temporary data on exit
                    self.cleanup()
                    console.print("[yellow]Clearing temporary data...[/yellow]")
                    console.print("[green]✓ All scan data cleared[/green]")
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if user_input.lower() == 'tools':
                    self.show_tools()
                    continue
                
                if not user_input.strip():
                    continue
                
                # Check if this is a scan request or casual conversation
                if not self.is_scan_request(user_input):
                    # Casual conversation mode
                    console.print("\n[dim]💬 Chat mode[/dim]")
                    ai_response = self.ask_ollama(user_input, is_casual=True)
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Nighthawk", border_style="cyan"))
                    continue
                
                # Scan request mode
                console.print("\n[dim]🔍 Scan mode[/dim]")
                
                # Extract hostname if URL present
                hostname = self.extract_hostname(user_input)
                if hostname and ('http://' in user_input or 'https://' in user_input):
                    console.print(f"[dim]Extracted hostname: {hostname}[/dim]")
                    user_input_for_ai = user_input.replace('https://', '').replace('http://', '')
                    user_input_for_ai = re.sub(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?', 
                                              hostname, user_input_for_ai)
                else:
                    user_input_for_ai = user_input
                
                # Detect if user wants exploits/metasploit
                wants_exploits = any(keyword in user_input.lower() for keyword in 
                                    ['exploit', 'metasploit', 'msfconsole', 'vulnerability', 'vuln', 'hack'])
                
                # Determine which tool to use
                if wants_exploits and 'metasploit' in self.tools:
                    tool_name = 'metasploit'
                    tool = self.tools['metasploit']
                    
                    # Prepare scan context from previous nmap results
                    scan_context = self.prepare_scan_context(hostname or self.last_target)
                    
                    if scan_context:
                        console.print(f"[dim]Using previous scan data for {scan_context.get('target', 'target')}[/dim]")
                    
                    # Generate Metasploit commands with context
                    commands = tool.generate_command(user_input_for_ai, scan_context)
                    
                    if commands:
                        # Execute Metasploit commands
                        result = tool.execute(commands)
                        
                        if result['success']:
                            tool.format_output(result, commands)
                            
                            # Store result
                            target = hostname or self.last_target or "unknown"
                            self.scan_results[f"{target}_metasploit"] = result['stdout']
                            
                            # Get AI analysis
                            console.print("\n[dim]Analyzing exploit results...[/dim]")
                            analysis = self.ask_ollama(
                                user_input,
                                output_to_analyze=result['stdout']
                            )
                            self.display_analysis(analysis)
                        else:
                            console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
                    else:
                        console.print("[yellow]Could not generate Metasploit commands[/yellow]")
                    
                    continue
                
                # Default to nmap or other scanning tools
                tool_context = self.tools['nmap'].get_ai_prompt()
                ai_response = self.ask_ollama(user_input_for_ai, tool_context=tool_context)
                
                # Detect which tool to use
                tool_name = self.detect_tool(user_input, ai_response)
                
                if not tool_name:
                    # No tool detected, just show AI response
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Response", border_style="cyan"))
                    continue
                
                tool = self.tools[tool_name]
                
                # Generate command
                command = tool.generate_command(user_input, ai_response)
                
                if command:
                    console.print(f"\n[yellow]Generated command:[/yellow] {command}")
                    
                    # Execute command
                    result = tool.execute(command)
                    
                    if result['success']:
                        # Store scan result temporarily
                        target = hostname if hostname else "unknown"
                        self.scan_results[target] = result['stdout']
                        self.last_target = target  # Remember last target
                        
                        # Parse and store structured data for Metasploit to use
                        if tool_name == 'nmap' and hasattr(tool, 'parse_scan_data'):
                            parsed_data = tool.parse_scan_data(result['stdout'])
                            self.scan_results[f"{target}_parsed"] = parsed_data
                        
                        self.display_results(result['stdout'], tool_name)
                        
                        # Get AI analysis
                        console.print("\n[dim]Analyzing results...[/dim]")
                        analysis = self.ask_ollama(
                            user_input,
                            output_to_analyze=result['stdout']
                        )
                        self.display_analysis(analysis)
                    else:
                        console.print(
                            f"[bold red]Error executing {tool_name}:[/bold red]\n{result['stderr']}"
                        )
                else:
                    # Just show the AI response
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Response", border_style="cyan"))
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
    
    def prepare_scan_context(self, target: Optional[str] = None) -> Optional[Dict]:
        """
        Prepare scan context from previous nmap results for use in other tools
        
        Args:
            target: Target to get context for (or use last_target)
        
        Returns:
            Dictionary with target, ip, open_ports, services, os info
        """
        if not target:
            target = self.last_target
        
        if not target or target not in self.scan_results:
            return None
        
        # Check if we have parsed data
        parsed_key = f"{target}_parsed"
        if parsed_key in self.scan_results:
            scan_data = self.scan_results[parsed_key]
            scan_data['target'] = target
            return scan_data
        
        # If no parsed data, try to use the metasploit tool's parser
        if 'metasploit' in self.tools:
            raw_output = self.scan_results.get(target, '')
            if raw_output:
                metasploit_tool = self.tools['metasploit']
                parsed_data = metasploit_tool.parse_scan_data(raw_output)
                parsed_data['target'] = target
                
                # Cache it for future use
                self.scan_results[parsed_key] = parsed_data
                
                return parsed_data
        
        return None
    
    def cleanup(self):
        """Clean up temporary data (called on exit)"""
        self.conversation_history.clear()
        self.scan_results.clear()
        console.print("[dim]Memory cleared - all conversation and scan data deleted[/dim]")
    
    def show_tools(self):
        """Show available tools"""
        table = Table(title="Available Security Tools", box=box.ROUNDED)
        table.add_column("Tool", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Description", style="yellow")
        
        for name, tool in self.tools.items():
            status = "✓ Installed" if tool.check_installed() else "✗ Not Found"
            status_style = "green" if "✓" in status else "red"
            
            descriptions = {
                'nmap': 'Network scanner and security auditing tool',
                'nikto': 'Web server vulnerability scanner',
                'sqlmap': 'SQL injection detection and exploitation',
                'metasploit': 'Penetration testing framework',
            }
            
            table.add_row(
                name,
                f"[{status_style}]{status}[/{status_style}]",
                descriptions.get(name, "Security tool")
            )
        
        console.print(table)
        console.print("\n[dim]More tools coming soon...[/dim]")


def main():
    """Main entry point"""
    assistant = NighthawkAssistant()
    assistant.interactive_mode()


if __name__ == "__main__":
    main()
