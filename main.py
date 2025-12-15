import sys
import os
import re
from typing import Optional, Dict
from urllib.parse import urlparse
import ollama
import google.generativeai as genai
from dotenv import load_dotenv
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
from cli.command_manager import CommandManager

load_dotenv()

console = Console()


class NighthawkAssistant:
    """AI-powered security assistant with modular tool support"""
    
    def __init__(self, model: str = "dolphin-llama3:8b"):
        self.model = model
        self.current_model = "ollama"
        self.console = Console()
        self.tools = {}
        self.active_tool = None
        self.conversation_history = []
        self.scan_results = {}
        self.last_target = None
        
        self.command_manager = CommandManager()
        self.gemini_chat = None
        self._init_gemini()
        self._register_tools()
    
    def _init_gemini(self):
        """Initialize Google Gemini API"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction="You are Nighthawk, a security expert assistant. Help with security scanning, provide clear insights, and remember conversation context. Your responses can be spoken aloud with text-to-speech."
                )
                self.gemini_chat = model.start_chat(history=[])
                console.print("[dim green]✓ Google Gemini initialized[/dim green]")
            else:
                console.print("[dim yellow]⚠ Google API key not found - Gemini unavailable[/dim yellow]")
        except Exception as e:
            console.print(f"[dim yellow]⚠ Gemini initialization failed: {e}[/dim yellow]")
            self.gemini_chat = None
    
    def _register_tools(self):
        nmap = NmapTool()
        self.tools['nmap'] = nmap
        metasploit = MetasploitTool()
        self.tools['metasploit'] = metasploit
    
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
        url_pattern = r'https?://([a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?)'
        matches = re.findall(url_pattern, text)
        if matches:
            return matches[0]
        try:
            parsed = urlparse(text)
            if parsed.netloc:
                return parsed.netloc
            elif parsed.path and '.' in parsed.path:
                return parsed.path.split('/')[0]
        except:
            pass
        
        return None
    
    def detect_user_intent(self, user_request: str) -> str:
        """Use AI to determine if user wants to scan/exploit or just chat"""
        intent_prompt = """You are an intent classifier for a security assistant. Analyze the user's message and determine their intent.

Respond with ONLY ONE WORD:

SCAN - User wants to actively PERFORM a network scan, port scan, or service enumeration on a specific target
Examples: "Scan 192.168.1.1", "Run nmap on example.com", "Check what ports are open on that server"

EXPLOIT - User wants to actively EXECUTE an exploit, attack, or penetration test on a target
Examples: "Exploit vsftpd on that server", "Hack the target", "Use metasploit to attack", "Run the exploit"

CHAT - User is asking questions, having conversation, or seeking information WITHOUT wanting to execute tools
Examples: "What is port 80 used for?", "Which port is most dangerous?", "How does nmap work?", "Tell me about SQL injection"

Key distinction: Questions ABOUT security = CHAT. Commands to DO security actions = SCAN/EXPLOIT.

User message: """
        
        try:
            # Call Ollama directly to avoid conversation history pollution
            if self.current_model == "gemini" and self.gemini_chat:
                # For Gemini, create a new temporary chat for classification
                temp_model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction="You are an intent classifier. Respond with only: SCAN, EXPLOIT, or CHAT. Questions about security = CHAT. Commands to execute tools = SCAN or EXPLOIT."
                )
                temp_chat = temp_model.start_chat(history=[])
                response = temp_chat.send_message(intent_prompt + user_request)
                intent = response.text.strip().upper()
            else:
                # For Ollama, make a direct call without polluting conversation history
                response = ollama.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an intent classifier. Respond with ONLY one word: SCAN, EXPLOIT, or CHAT. Questions about security = CHAT. Commands to execute tools = SCAN or EXPLOIT."},
                        {"role": "user", "content": intent_prompt + user_request}
                    ]
                )
                intent = response['message']['content'].strip().upper()
            
            if ' ' in intent:
                intent = intent.split()[0]
            
            if intent in ['SCAN', 'EXPLOIT', 'CHAT']:
                return intent
            
            request_lower = user_request.lower()
            if any(word in request_lower for word in ['scan', 'nmap', 'port', 'enumerate']):
                return 'SCAN'
            elif any(word in request_lower for word in ['exploit', 'hack', 'metasploit', 'penetrate']):
                return 'EXPLOIT'
            else:
                return 'CHAT'
                
        except Exception as e:
            return self._fallback_intent_detection(user_request)
    
    def _fallback_intent_detection(self, user_request: str) -> str:
        """Fallback keyword-based intent detection if AI fails"""
        scan_keywords = [
            'scan', 'nmap', 'port', 'detect', 'find ports', 'check target',
            'enumerate', 'discover services',
            'test target', 'probe target', 'analyze target', 'security check',
            'open ports', 'services running', 'os detection',
            'stealth', 'udp scan', 'tcp scan'
        ]
        
        # Exploit-related action patterns
        exploit_patterns = [
            r'find\s+(the\s+|that\s+)?exploit',
            r'run\s+(the\s+|that\s+)?exploit',
            r'use\s+(the\s+|that\s+)?exploit',
            r'exploit\s+(the\s+|this\s+|that\s+|all\s+)?target',
            r'exploit\s+(the\s+|this\s+|that\s+|all\s+)?website',
            r'exploit\s+(the\s+|all\s+)?port',
            r'exploit\s+everything',
            r'exploit\s+all',
            r'try\s+(the\s+|that\s+|an?\s+)?exploit',
            r'attempt\s+(the\s+|that\s+|an?\s+)?exploit',
            r'launch\s+(the\s+|that\s+|an?\s+)?exploit',
            r'execute\s+(the\s+|that\s+)?exploit',
            r'run\s+metasploit',
            r'use\s+metasploit',
            r'start\s+metasploit',
            r'msfconsole',
            r'hack\s+(the\s+|this\s+|that\s+)?target',
            r'hack\s+(the\s+|this\s+|that\s+)?website',
            r'hack\s+all',
            r'penetrate',
            r'pwn'
        ]
        
        request_lower = user_request.lower()
        
        for pattern in exploit_patterns:
            if re.search(pattern, request_lower):
                return 'EXPLOIT'
        
        # Check scan keywords
        for keyword in scan_keywords:
            if keyword in request_lower:
                return 'SCAN'
        
        # If contains IP or domain, likely a scan
        if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b', request_lower):
            return 'SCAN'
        
        return 'CHAT'
    
    def classify_intent(self, user_request: str) -> str:
        """Alias for detect_user_intent - used by TUI for compatibility"""
        return self.detect_user_intent(user_request)
    
    def detect_tool(self, user_request: str, ai_response: str) -> Optional[str]:
        for tool_name in self.tools.keys():
            if tool_name in ai_response.lower():
                return tool_name
        for tool_name in self.tools.keys():
            if tool_name in user_request.lower():
                return tool_name
        return None
    
    def ask_ollama(self, user_request: str, tool_context: Optional[str] = None, 
                   output_to_analyze: Optional[str] = None, is_casual: bool = False) -> str:
        if output_to_analyze:
            system_prompt = """You are a security expert analyzing scan results.
Provide clear, actionable insights. Remember previous scan results to give comprehensive advice."""
            context = ""
            if self.scan_results:
                context = "\n\nPrevious scan results for context:\n"
                for target, result in list(self.scan_results.items())[-3:]:
                    if isinstance(result, str):
                        context += f"- {target}: {result[:200]}...\n"
                    elif isinstance(result, dict):
                        if 'open_ports' in result:
                            ports = [p.get('port', '?') for p in result.get('open_ports', [])]
                            context += f"- {target}: Found {len(ports)} open ports: {', '.join(ports[:5])}\n"
                        else:
                            context += f"- {target}: (parsed data available)\n"
            
            prompt = f"""Analyze this security scan output:{context}

{output_to_analyze}

Provide:
1. Summary of findings
2. Key discoveries (ports, services, vulnerabilities)
3. Security concerns
4. Recommended next steps (consider previous scans if relevant)"""
        elif is_casual:
            system_prompt = """You are Nighthawk, a friendly security assistant.
You can have normal conversations AND help with security scanning.
Be helpful, conversational, and remember context.
Don't try to scan things unless the user explicitly asks for it.

Note: Your responses can be read aloud with text-to-speech if the user has enabled it in Settings."""
            prompt = user_request
        else:
            if tool_context:
                system_prompt = tool_context
            else:
                request_lower = user_request.lower()
                system_prompt = """You are a Kali Linux security expert.
Generate ONLY the command to execute, nothing else.
Do NOT respond with explanations or questions - ONLY the command."""
                if any(word in request_lower for word in ['scan', 'nmap', 'port', 'network']):
                    if 'nmap' in self.tools:
                        system_prompt = self.tools['nmap'].get_ai_prompt()
                elif any(word in request_lower for word in ['exploit', 'metasploit', 'vulnerability']):
                    if 'metasploit' in self.tools:
                        system_prompt = """You are a penetration testing expert.
Generate ONLY the Metasploit command, no explanations.
Format: use exploit/... or search ..."""
            
            prompt = f"""User request: {user_request}

CRITICAL: Respond with ONLY the command. No explanations, no questions, no greetings.
Just the command on a single line.

Example:
User: "scan example.com"
You: nmap -sV example.com

User: "quick scan 192.168.1.1"  
You: nmap -F 192.168.1.1

Now respond to: {user_request}"""
        try:
            messages = [{"role": "system", "content": system_prompt}]
            for msg in self.conversation_history[-5:]:
                messages.append(msg)
            messages.append({"role": "user", "content": prompt})
            
            response = ollama.chat(model=self.model, messages=messages)
            ai_message = response['message']['content']
            
            self.conversation_history.append({"role": "user", "content": user_request})
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            return ai_message
        except Exception as e:
            return f"Error communicating with Ollama: {e}"
    
    def ask_gemini(self, user_request: str, tool_context: Optional[str] = None, 
                   output_to_analyze: Optional[str] = None, is_casual: bool = False) -> str:
        if not self.gemini_chat:
            return "Error: Google Gemini is not initialized. Check your API key in .env file."
        
        try:
            if output_to_analyze:
                context = ""
                if self.scan_results:
                    context = "\n\nPrevious scan results for context:\n"
                    for target, result in list(self.scan_results.items())[-3:]:
                        if isinstance(result, str):
                            context += f"- {target}: {result[:200]}...\n"
                        elif isinstance(result, dict):
                            if 'open_ports' in result:
                                ports = [p.get('port', '?') for p in result.get('open_ports', [])]
                                context += f"- {target}: Found {len(ports)} open ports: {', '.join(ports[:5])}\n"
                            else:
                                context += f"- {target}: (parsed data available)\n"
                prompt = f"""Analyze this security scan output:{context}

{output_to_analyze}

Provide:
1. Summary of findings
2. Key discoveries (ports, services, vulnerabilities)
3. Security concerns
4. Recommended next steps (consider previous scans if relevant)"""
            elif is_casual:
                prompt = user_request
            else:
                if tool_context:
                    prompt = f"{tool_context}\n\nUser request: {user_request}\n\nGenerate the appropriate security tool command. Respond with ONLY the command (one line, no explanations)."
                else:
                    prompt = f"""User request: {user_request}

Generate the appropriate security tool command.
Respond with ONLY the command (one line, no explanations)."""
            response = self.gemini_chat.send_message(prompt, stream=True)
            ai_message = ""
            for chunk in response:
                ai_message += chunk.text
            
            if not ai_message or len(ai_message.strip()) == 0:
                console.print("[dim yellow]⚠ Gemini blocked response (safety filters), falling back to Ollama...[/dim yellow]")
                return self.ask_ollama(user_request, tool_context, output_to_analyze, is_casual)
            
            self.conversation_history.append({"role": "user", "content": user_request})
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            return ai_message
        except Exception as e:
            error_msg = str(e)
            if "finish_reason" in error_msg or "valid Part" in error_msg or "SAFETY" in error_msg.upper():
                console.print("[dim yellow]⚠ Gemini safety filters triggered, switching to Ollama...[/dim yellow]")
                return self.ask_ollama(user_request, tool_context, output_to_analyze, is_casual)
            return f"Error communicating with Google Gemini: {e}"
    
    def ask_ai(self, user_request: str, tool_context: Optional[str] = None, 
               output_to_analyze: Optional[str] = None, is_casual: bool = False) -> str:
        """Route to appropriate AI model based on current_model setting"""
        if self.current_model == "gemini" and self.gemini_chat:
            return self.ask_gemini(user_request, tool_context, output_to_analyze, is_casual)
        else:
            return self.ask_ollama(user_request, tool_context, output_to_analyze, is_casual)
    
    def switch_model(self, model_name: str) -> bool:
        """Switch between AI models"""
        model_name = model_name.lower()
        if model_name in ["ollama", "dolphin", "local"]:
            self.current_model = "ollama"
            console.print(f"[green]✓ Switched to Ollama ({self.model})[/green]")
            return True
        elif model_name in ["gemini", "google"]:
            if self.gemini_chat:
                self.current_model = "gemini"
                console.print("[green]✓ Switched to Google Gemini 2.5 Flash (for chat)[/green]")
                console.print("[dim]Note: Exploitation uses auto-fallback: 2.5 Pro → 2.0 Flash → Ollama[/dim]")
                return True
            else:
                console.print("[red]✗ Gemini is not available. Check your API key in .env file.[/red]")
                return False
        else:
            console.print(f"[red]✗ Unknown model: {model_name}[/red]")
            console.print("[yellow]Available models: ollama, gemini[/yellow]")
            return False
    
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
        model_status = f"Ollama ({self.model})"
        if self.gemini_chat:
            model_status += " + Gemini 2.5 Pro + Gemini 2.0 Flash"
        
        console.print(Panel.fit(
            "[bold cyan]Nighthawk Security Assistant[/bold cyan]\n"
            "AI-powered security tool orchestrator\n\n"
            f"Models: {model_status}\n"
            f"Active: [bold]{self.current_model}[/bold]\n"
            f"Fallback Chain: Gemini 2.5 Pro → 2.0 Flash → Ollama\n"
            f"Tools: {', '.join(self.tools.keys())}",
            border_style="cyan",
            title="🦅 Nighthawk",
            subtitle="Triple AI Fallback System"
        ))
        
        # Check prerequisites
        if not self.check_ollama_connection():
            return
        
        if not self.check_tools():
            console.print("\n[yellow]Warning: Some tools are not available[/yellow]")
        
        console.print("\n[green]✓[/green] System ready!")
        console.print("\n[yellow]Commands:[/yellow]")
        console.print("  - Type your request in natural language")
        console.print("  - Type 'help' to see all CLI commands")
        console.print("  - Type 'tools' to see available tools")
        console.print("  - Type 'model <name>' to switch models (ollama/gemini)")
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
                
                # Handle model switching
                if user_input.lower().startswith('model '):
                    model_name = user_input[6:].strip()
                    self.switch_model(model_name)
                    continue
                
                if not user_input.strip():
                    continue
                
                # Check if it's a CLI command
                if self.command_manager.parse_and_execute(user_input, self):
                    continue
                
                # Use AI to detect user intent (silently)
                intent = self.detect_user_intent(user_input)
                
                if intent == 'CHAT':
                    # Casual conversation mode (no mode indicator)
                    ai_response = self.ask_ai(user_input, is_casual=True)
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Nighthawk", border_style="cyan"))
                    continue
                
                # SCAN or EXPLOIT mode - show mode indicator
                if intent == 'SCAN':
                    console.print("\n[dim]🔍 Scan mode[/dim]")
                elif intent == 'EXPLOIT':
                    console.print("\n[dim]💥 Exploit mode[/dim]")
                
                # Extract hostname if URL present
                hostname = self.extract_hostname(user_input)
                if hostname and ('http://' in user_input or 'https://' in user_input):
                    console.print(f"[dim]Extracted hostname: {hostname}[/dim]")
                    user_input_for_ai = user_input.replace('https://', '').replace('http://', '')
                    user_input_for_ai = re.sub(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[^\s]*)?', 
                                              hostname, user_input_for_ai)
                else:
                    user_input_for_ai = user_input
                
                if intent == 'EXPLOIT' and 'metasploit' in self.tools:
                    tool_name = 'metasploit'
                    tool = self.tools['metasploit']
                    scan_context = self.prepare_scan_context(hostname or self.last_target)
                    
                    if scan_context and not isinstance(scan_context, dict):
                        console.print(f"[red]Error: Invalid scan context type: {type(scan_context)}[/red]")
                        console.print("[yellow]Please run a scan first before exploiting[/yellow]")
                        continue
                    
                    if not scan_context:
                        console.print("[yellow]⚠ No previous scan data found![/yellow]")
                        console.print("[cyan]💡 Tip: Run an nmap scan first, then I can find exploits based on the results.[/cyan]")
                        console.print(f"[dim]Example: 'scan {hostname or 'target.com'}' then 'exploit that target'[/dim]")
                        continue
                    
                    console.print(f"[dim]Using previous scan data for {scan_context.get('target', 'target')}[/dim]")
                    commands = tool.generate_command(user_input_for_ai, scan_context)
                    
                    if commands:
                        result = tool.execute(commands)
                        if result['success']:
                            tool.format_output(result, commands)
                            target = hostname or self.last_target or "unknown"
                            self.scan_results[f"{target}_metasploit"] = result['stdout']
                            console.print("\n[dim]Analyzing exploit results...[/dim]")
                            analysis = self.ask_ai(user_input, output_to_analyze=result['stdout'])
                            self.display_analysis(analysis)
                        else:
                            console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
                    else:
                        console.print("[yellow]Could not generate Metasploit commands[/yellow]")
                    continue
                
                tool_context = self.tools['nmap'].get_ai_prompt()
                ai_response = self.ask_ai(user_input_for_ai, tool_context=tool_context)
                tool_name = self.detect_tool(user_input, ai_response)
                
                if not tool_name:
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Response", border_style="cyan"))
                    continue
                
                tool = self.tools[tool_name]
                command = tool.generate_command(user_input, ai_response)
                
                if command:
                    console.print(f"\n[yellow]Generated command:[/yellow] {command}")
                    result = tool.execute(command)
                    
                    if result['success']:
                        target = hostname if hostname else "unknown"
                        self.scan_results[target] = result['stdout']
                        self.last_target = target
                        
                        if tool_name == 'nmap' and hasattr(tool, 'parse_scan_data'):
                            parsed_data = tool.parse_scan_data(result['stdout'])
                            self.scan_results[f"{target}_parsed"] = parsed_data
                        
                        self.display_results(result['stdout'], tool_name)
                        console.print("\n[dim]Analyzing results...[/dim]")
                        analysis = self.ask_ai(user_input, output_to_analyze=result['stdout'])
                        self.display_analysis(analysis)
                    else:
                        console.print(f"[bold red]Error executing {tool_name}:[/bold red]\n{result['stderr']}")
                else:
                    md = Markdown(ai_response)
                    console.print(Panel(md, title="Response", border_style="cyan"))
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'quit' to exit.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
    
    def prepare_scan_context(self, target: Optional[str] = None) -> Optional[Dict]:
        if not target:
            target = self.last_target
        if not target or target not in self.scan_results:
            return None
        parsed_key = f"{target}_parsed"
        if parsed_key in self.scan_results:
            scan_data = self.scan_results[parsed_key]
            scan_data['target'] = target
            return scan_data
        if 'metasploit' in self.tools:
            raw_output = self.scan_results.get(target, '')
            if raw_output:
                metasploit_tool = self.tools['metasploit']
                parsed_data = metasploit_tool.parse_scan_data(raw_output)
                parsed_data['target'] = target
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
