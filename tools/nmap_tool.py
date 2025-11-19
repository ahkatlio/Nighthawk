"""
Nmap tool integration
"""

import subprocess
import re
from typing import Dict, Optional
from .base_tool import BaseTool
from rich.console import Console

console = Console()


class NmapTool(BaseTool):
    """Nmap network scanner integration"""
    
    def __init__(self):
        super().__init__(name="nmap", command="nmap")
    
    def check_installed(self) -> bool:
        """Check if nmap is installed"""
        try:
            result = subprocess.run(
                ["nmap", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Extract version
                version_match = re.search(r'Nmap version ([\d.]+)', result.stdout)
                if version_match:
                    console.print(f"[green]✓[/green] Nmap {version_match.group(1)} detected")
                return True
            return False
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] nmap not found: {e}")
            return False
    
    def generate_command(self, user_request: str, ai_response: str) -> Optional[str]:
        """Extract and enhance nmap command from AI response"""
        command = None
        
        # Find the nmap command in the response
        for line in ai_response.split('\n'):
            line = line.strip()
            # Remove markdown code block markers
            if line.startswith('```'):
                continue
            if line.startswith('`') and line.endswith('`'):
                line = line.strip('`')
            if line.startswith('nmap'):
                command = line
                break
        
        if command:
            parts = command.split()
            
            # Flags that require root/sudo privileges
            root_flags = ['-O', '--osscan-guess', '-sS', '-sU', '-sA', '-sW', '-sM']
            needs_sudo = any(flag in parts for flag in root_flags)
            
            # Check if running as root
            import os
            is_root = os.geteuid() == 0
            
            if needs_sudo and not is_root:
                # Add sudo to the command instead of removing flags
                console.print("[yellow]⚠️  This scan requires root privileges[/yellow]")
                console.print("[cyan]Adding 'sudo' to command - you'll be prompted for your password[/cyan]")
                command = 'sudo ' + command
                parts = command.split()
            
            # Auto-add -Pn flag if not present (skip host discovery)
            if '-Pn' not in parts and '-sn' not in parts:
                # Find where to insert -Pn (after sudo and nmap)
                insert_pos = 1
                if parts[0] == 'sudo':
                    insert_pos = 2
                parts.insert(insert_pos, '-Pn')
                console.print("[dim]Added -Pn flag (skip host discovery)[/dim]")
            
            command = ' '.join(parts)
        
        return command
    
    def execute(self, command: str) -> Dict[str, any]:
        """Execute nmap command"""
        return self.run_command(command, timeout=300)
    
    def format_output(self, output: str) -> str:
        """Format nmap output for display"""
        return output
    
    def get_ai_prompt(self) -> str:
        """Get the AI system prompt for nmap"""
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
        """
        Parse nmap output to extract structured data for other tools
        
        Args:
            raw_output: Raw nmap scan output
        
        Returns:
            Dictionary with open_ports, services, os, ip
        """
        scan_data = {
            'open_ports': [],
            'services': [],
            'os': None,
            'ip': None
        }
        
        # Extract open ports and services
        # Pattern: PORT     STATE SERVICE    VERSION
        # Example: 22/tcp   open  ssh        OpenSSH 8.9p1
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
        
        # Extract IP address
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

