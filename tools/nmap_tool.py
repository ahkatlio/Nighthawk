import subprocess
import re
from typing import Dict, Optional
from .base_tool import BaseTool
from rich.console import Console

console = Console()


class NmapTool(BaseTool):
    def __init__(self):
        super().__init__(name="nmap", command="nmap")
    
    def check_installed(self) -> bool:
        try:
            result = subprocess.run(
                ["nmap", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_match = re.search(r'Nmap version ([\d.]+)', result.stdout)
                if version_match:
                    console.print(f"[green]✓[/green] Nmap {version_match.group(1)} detected")
                return True
            return False
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] nmap not found: {e}")
            return False
    
    def generate_command(self, user_request: str, ai_response: str) -> Optional[str]:
        command = None
        
        for line in ai_response.split('\n'):
            line = line.strip()
            if line.startswith('```'):
                continue
            if line.startswith('`') and line.endswith('`'):
                line = line.strip('`')
            if line.startswith('nmap'):
                command = line
                break
        
        if not command:
            console.print("[yellow]No nmap command in AI response, generating basic scan...[/yellow]")
            
            import re
            url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            
            target = None
            
            ip_match = re.search(ip_pattern, user_request)
            if ip_match:
                target = ip_match.group(0)
            else:
                url_match = re.search(url_pattern, user_request)
                if url_match:
                    target = url_match.group(1)
            
            if target:
                command = f"nmap -Pn -sV -sC {target}"
                console.print(f"[cyan]Generated command: {command}[/cyan]")
            else:
                console.print("[red]Could not extract target from request[/red]")
                return None
        
        if command:
            parts = command.split()
            
            root_flags = ['-O', '--osscan-guess', '-sS', '-sU', '-sA', '-sW', '-sM']
            needs_sudo = any(flag in parts for flag in root_flags)
            
            import os
            is_root = os.geteuid() == 0
            
            if needs_sudo and not is_root:
                console.print("[yellow]⚠️  This scan requires root privileges[/yellow]")
                console.print("[cyan]Adding 'sudo' to command - you'll be prompted for your password[/cyan]")
                command = 'sudo ' + command
                parts = command.split()
            
            if '-Pn' not in parts and '-sn' not in parts:
                insert_pos = 1
                if parts[0] == 'sudo':
                    insert_pos = 2
                parts.insert(insert_pos, '-Pn')
                console.print("[dim]Added -Pn flag (skip host discovery)[/dim]")
            
            command = ' '.join(parts)
        
        return command
    
    def execute(self, command: str) -> Dict[str, any]:
        return self.run_command(command, timeout=300)
    
    def format_output(self, output: str) -> str:
        return output
    
    def get_ai_prompt(self) -> str:
        return """You are a Kali Linux security expert specializing in nmap network scanning.

When generating nmap commands:
1. Extract hostname/IP from URLs (e.g., https://example.com/path → example.com)
2. Generate appropriate nmap command with ONLY the hostname or IP
3. Respond with ONLY the nmap command on a single line
4. Do NOT include http://, https://, or any path - just hostname
5. Use the most appropriate flags for the scan type requested

Common scan types:
- Quick scan: nmap -F [target]
- Service detection: nmap -sV [target]
- OS detection: nmap -O [target] (will prompt for sudo)
- Full TCP scan: nmap -p- [target]
- Stealth SYN scan: nmap -sS [target] (will prompt for sudo)
- UDP scan: nmap -sU [target] (will prompt for sudo)
- Comprehensive: nmap -A [target] (will prompt for sudo)
- Version + OS: nmap -sV -O [target] (will prompt for sudo)

When user asks about IP address or OS:
- Use -O for OS detection (system will add sudo if needed)
- Use -sV for service/version detection
- Use -A for aggressive scan (OS + version + scripts)

Examples:
- "scan https://example.com" → nmap -sV example.com
- "quick scan of 192.168.1.1" → nmap -F 192.168.1.1
- "find IP and OS of example.com" → nmap -O example.com
- "detect OS on target" → nmap -O target.com
- "stealth scan target" → nmap -sS target.com

NOTE: The system automatically adds -Pn flag to skip host discovery if target seems down.

When analyzing nmap output, provide:
1. Clear summary of findings
2. Open ports and services discovered
3. Potential security concerns
4. Recommended next steps for deeper analysis"""
    
    def parse_scan_data(self, raw_output: str) -> dict:
        scan_data = {
            'open_ports': [],
            'services': [],
            'os': None,
            'ip': None
        }
        
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
        
        os_patterns = [
            r'OS details?: (.+)',
            r'Running: (.+)',
            r'OS CPE: cpe:/o:([^:]+):([^:]+)'
        ]
        
        for pattern in os_patterns:
            os_match = re.search(pattern, raw_output)
            if os_match:
                scan_data['os'] = os_match.group(1).strip()
                break
        
        ip_patterns = [
            r'Nmap scan report for .*?\(([0-9.]+)\)',
            r'Nmap scan report for ([0-9.]+)'
        ]
        
        for pattern in ip_patterns:
            ip_match = re.search(pattern, raw_output)
            if ip_match:
                scan_data['ip'] = ip_match.group(1)
                break
        
        return scan_data

