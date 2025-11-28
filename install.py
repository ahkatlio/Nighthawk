#!/usr/bin/env python3
"""
Nighthawk Security Tool Installer
A hacker-themed installer with cyberpunk visual effects
Because penetration testing tools deserve a dramatic installation
"""

import os
import sys
import platform
import subprocess
import time
import random
from pathlib import Path


class HackerEffects:
    """Cyberpunk visual effects system with ANSI color codes"""
    
    def __init__(self):
        # ANSI color codes for hacker aesthetic
        self.colors = {
            'red': '\x1b[31m',
            'green': '\x1b[32m',
            'yellow': '\x1b[33m',
            'blue': '\x1b[34m',
            'magenta': '\x1b[35m',
            'cyan': '\x1b[36m',
            'white': '\x1b[37m',
            'bright': '\x1b[1m',
            'reset': '\x1b[0m',
            # Hacker-style neon colors
            'neon_green': '\x1b[92m',
            'neon_red': '\x1b[91m',
            'neon_yellow': '\x1b[93m',
            'neon_cyan': '\x1b[96m',
            'dark_gray': '\x1b[90m',
            'orange': '\x1b[38;5;208m',
        }
    
    def box(self, text, title=''):
        """Create a cyberpunk box around text"""
        lines = text.split('\n')
        max_length = max(len(line) for line in lines)
        if title:
            max_length = max(max_length, len(title) + 4)
        
        top_border = '┌' + '─' * (max_length + 2) + '┐'
        bottom_border = '└' + '─' * (max_length + 2) + '┘'
        
        result = self.colors['neon_green'] + top_border + '\n'
        
        if title:
            result += f"│ {self.colors['neon_cyan']}{title.center(max_length)}{self.colors['neon_green']} │\n"
            result += '├' + '─' * (max_length + 2) + '┤\n'
        
        for line in lines:
            result += f"│ {self.colors['white']}{line.ljust(max_length)}{self.colors['neon_green']} │\n"
        
        result += bottom_border + self.colors['reset']
        return result
    
    def progress_bar(self, current, total, width=50):
        """Create a hacker-style progress bar"""
        percentage = round((current / total) * 100)
        filled = round((current / total) * width)
        empty = width - filled
        
        filled_bar = self.colors['neon_green'] + '█' * filled
        empty_bar = self.colors['dark_gray'] + '░' * empty
        
        return (f"{self.colors['neon_green']}[{filled_bar}{empty_bar}"
                f"{self.colors['neon_green']}] {self.colors['neon_cyan']}{percentage}%"
                f"{self.colors['reset']} {self.colors['dark_gray']}({current}/{total})"
                f"{self.colors['reset']}")
    
    def update_progress(self, current, total, text=''):
        """Update progress on the same line (clears line first)"""
        sys.stdout.write('\r\x1b[K')  # Clear entire line
        progress = self.progress_bar(current, total)
        sys.stdout.write(f"{progress} {self.colors['neon_cyan']}{text}{self.colors['reset']}")
        sys.stdout.flush()
        if current == total:
            print()  # New line when complete
    
    def glitch_text(self, text, iterations=3):
        """Hacker-style glitch text effect"""
        chars = '!@#$%^&*()_+-=[]{}|;:,.<>?01'
        
        for i in range(iterations):
            glitched = ''
            for char in text:
                if char == ' ':
                    glitched += ' '
                elif random.random() < 0.3:
                    glitched += self.colors['neon_red'] + random.choice(chars) + self.colors['reset']
                else:
                    glitched += char
            
            sys.stdout.write('\r' + glitched)
            sys.stdout.flush()
            time.sleep(0.1)
        
        sys.stdout.write('\r' + self.colors['neon_green'] + text + self.colors['reset'])
        sys.stdout.flush()
    
    def matrix_prompt(self, text):
        """Hacker-style terminal prompt"""
        return self.colors['neon_green'] + '> ' + self.colors['reset'] + self.colors['white'] + text + self.colors['reset']
    
    def status(self, status, message):
        """Hacker-style status indicator"""
        status_colors = {
            'success': self.colors['neon_green'],
            'warning': self.colors['neon_yellow'],
            'error': self.colors['neon_red'],
            'info': self.colors['neon_cyan'],
            'processing': self.colors['orange']
        }
        color = status_colors.get(status, self.colors['white'])
        symbol = '[+]' if status == 'success' else '[-]' if status == 'error' else '[*]'
        
        return color + symbol + ' ' + message + self.colors['reset']
    
    def type_writer(self, text, delay=0.03):
        """Animated typing effect"""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
    
    def loading_dots(self, text, duration=2.0):
        """Animated loading dots with hacker styling"""
        dots = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        start_time = time.time()
        i = 0
        
        while time.time() - start_time < duration:
            sys.stdout.write(f"\r{self.colors['neon_green']}{dots[i]} {self.colors['white']}{text}{self.colors['reset']}")
            sys.stdout.flush()
            i = (i + 1) % len(dots)
            time.sleep(0.1)
        
        sys.stdout.write('\r\x1b[K')
        sys.stdout.flush()
    
    def hack_animation(self, duration=1.5):
        """Hacking visualization"""
        chars = ['▓', '▒', '░', '█', '▀', '▄', '▌', '▐']
        start_time = time.time()
        
        while time.time() - start_time < duration:
            field = ''
            for _ in range(10):
                field += self.colors['neon_green'] + random.choice(chars) + ' '
            field += self.colors['neon_cyan'] + ' << HACKING >> ' + self.colors['reset']
            for _ in range(10):
                field += self.colors['neon_green'] + random.choice(chars) + ' '
            
            sys.stdout.write('\r' + field)
            sys.stdout.flush()
            time.sleep(0.15)
        
        sys.stdout.write('\r\x1b[K')
        sys.stdout.flush()


class NighthawkInstaller:
    """Main installer class with hacker styling"""
    
    def __init__(self):
        self.fx = HackerEffects()
        self.packages = []
        self.descriptions = []
        self.venv_path = Path('.venv')
        self.requirements_file = Path('requirements.txt')
    
    def get_python_command(self):
        """Get the appropriate Python command (respects pyenv)"""
        # First, check if there's a .python-version file (pyenv local)
        python_version_file = Path('.python-version')
        if python_version_file.exists():
            with open(python_version_file, 'r') as f:
                pyenv_version = f.read().strip()
                
                # Try using pyenv to get the exact python path
                try:
                    result = subprocess.run(['pyenv', 'which', 'python'], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True,
                                          env={**os.environ, 'PYENV_VERSION': pyenv_version})
                    if result.returncode == 0:
                        python_path = result.stdout.strip()
                        # Verify it's the right version
                        verify = subprocess.run([python_path, '--version'], 
                                              stdout=subprocess.PIPE, 
                                              stderr=subprocess.PIPE, 
                                              text=True)
                        version_output = verify.stdout or verify.stderr
                        if pyenv_version.split('.')[0:2] == version_output.split()[1].split('.')[0:2]:
                            return python_path
                except:
                    pass
                
                # Try with PYENV_VERSION environment variable set
                try:
                    # Check if 'python' with PYENV_VERSION works
                    test_env = os.environ.copy()
                    test_env['PYENV_VERSION'] = pyenv_version
                    result = subprocess.run(['python', '--version'], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True,
                                          env=test_env)
                    output = result.stdout or result.stderr
                    if pyenv_version.split('.')[0:2] == output.split()[1].split('.')[0:2]:
                        # Store this for later use
                        self.pyenv_version = pyenv_version
                        return 'python'
                except:
                    pass
        
        # Fallback to python3
        return 'python3'
    
    def _get_subprocess_env(self):
        """Get environment variables for subprocess calls"""
        env = os.environ.copy()
        if hasattr(self, 'pyenv_version'):
            env['PYENV_VERSION'] = self.pyenv_version
        return env
    
    def get_pip_command(self):
        """Get the path to pip in our virtual environment"""
        return str(self.venv_path / 'bin' / 'pip')
    
    def get_python_executable(self):
        """Get the path to Python in our virtual environment"""
        return str(self.venv_path / 'bin' / 'python')
    
    def show_header(self):
        """Display the epic hacker header"""
        os.system('clear')
        
        print(self.fx.colors['neon_green'] + '=' * 80 + self.fx.colors['reset'])
        time.sleep(0.2)
        
        self.fx.type_writer(self.fx.matrix_prompt('INITIATING NIGHTHAWK INSTALLATION PROTOCOL...'), 0.04)
        print()
        time.sleep(0.4)
        
        self.fx.type_writer(self.fx.matrix_prompt('ESTABLISHING SECURE CONNECTION TO UNDERGROUND NETWORK...'), 0.035)
        print()
        time.sleep(0.4)
        
        self.fx.hack_animation(1.5)
        print()
        
        self.fx.type_writer(self.fx.colors['neon_green'] + '>>> ACCESS GRANTED <<<' + self.fx.colors['reset'], 0.05)
        print()
        time.sleep(0.6)
        
        # ASCII Art Banner
        banner = f"""{self.fx.colors['neon_cyan']}
    ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗ █████╗ ██╗    ██╗██╗  ██╗
    ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝██║  ██║██╔══██╗██║    ██║██║ ██╔╝
    ██╔██╗ ██║██║██║  ███╗███████║   ██║   ███████║███████║██║ █╗ ██║█████╔╝ 
    ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██╔══██║██╔══██║██║███╗██║██╔═██╗ 
    ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║  ██║██║  ██║╚███╔███╔╝██║  ██╗
    ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝
{self.fx.colors['reset']}"""
        
        print(banner)
        print()
        
        header_text = """▓▓▓ NIGHTHAWK SECURITY FRAMEWORK ▓▓▓
[+] AI-Powered Penetration Testing Suite
[*] Platform: Linux
[*] Security Level: MAXIMUM
[!] Authorized Personnel Only"""
        
        print(self.fx.box(header_text, '< NIGHTHAWK INSTALLER >'))
        print()
        print(self.fx.colors['neon_green'] + '=' * 80 + self.fx.colors['reset'])
        print()
    
    def load_requirements(self):
        """Load packages from requirements.txt"""
        print()
        self.fx.type_writer(self.fx.matrix_prompt('SCANNING DEPENDENCY MANIFEST...'), 0.05)
        print()
        
        self.fx.loading_dots('[*] Analyzing requirements.txt', 1.5)
        
        if not self.requirements_file.exists():
            print(self.fx.status('error', 'CRITICAL ERROR: requirements.txt not found!'))
            print(self.fx.colors['neon_red'] + '(Did you clone the full repository?)' + self.fx.colors['reset'])
            sys.exit(1)
        
        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                pkg = line.split('#')[0].strip()
                if pkg:
                    self.packages.append(pkg)
                    description = line.split('#')[1].strip() if '#' in line else 'Security module'
                    self.descriptions.append(description)
        
        print(self.fx.status('success', f'DEPENDENCY SCAN COMPLETE: {len(self.packages)} packages detected'))
        print(self.fx.colors['dark_gray'] + f"(Loading up the arsenal...)" + self.fx.colors['reset'])
        print()
    
    def create_venv(self):
        """Create a virtual environment if it doesn't exist"""
        if self.venv_path.exists():
            print(self.fx.status('info', 'Virtual environment already exists - USING EXISTING'))
            print()
            return
        
        venv_text = """[*] CREATING ISOLATED ENVIRONMENT
[+] Establishing secure virtual environment
[*] Isolating dependencies from system"""
        
        print(self.fx.box(venv_text, '< VIRTUAL ENVIRONMENT >'))
        print()
        
        # Detect Python version being used
        python_cmd = self.get_python_command()
        try:
            version_result = subprocess.run([python_cmd, '--version'], 
                                          stdout=subprocess.PIPE, 
                                          stderr=subprocess.PIPE, 
                                          text=True)
            python_version = version_result.stdout.strip() or version_result.stderr.strip()
            print(self.fx.status('info', f'Using: {python_version}'))
        except:
            pass
        
        self.fx.loading_dots('[*] Materializing .venv directory', 1.5)
        
        try:
            subprocess.run([python_cmd, '-m', 'venv', str(self.venv_path)], 
                         check=True, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         env=self._get_subprocess_env())
            print(self.fx.status('success', 'VIRTUAL ENVIRONMENT CREATED SUCCESSFULLY'))
            
            # Verify the Python version in venv
            venv_python = self.get_python_executable()
            verify_result = subprocess.run([venv_python, '--version'], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE, 
                                         text=True)
            venv_version = verify_result.stdout.strip() or verify_result.stderr.strip()
            print(self.fx.status('success', f'Virtual environment using: {venv_version}'))
        except subprocess.CalledProcessError as e:
            print(self.fx.status('error', f'VIRTUAL ENVIRONMENT CREATION FAILED: {e}'))
            sys.exit(1)
        
        print()
    
    def check_package_installed(self, pkg_name):
        """Check if a package is already installed in venv"""
        package_name_only = pkg_name.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
        
        # Map package names to import names
        import_name_map = {
            'python-dotenv': 'dotenv',
            'google-generativeai': 'google.generativeai',
        }
        
        import_name = import_name_map.get(package_name_only.lower(), package_name_only.replace('-', '_'))
        
        python_path = self.get_python_executable() if self.venv_path.exists() else self.get_python_command()
        
        try:
            result = subprocess.run(
                [python_path, '-c', f'import {import_name}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def run_pip_install(self, pkg_name):
        """Install a package using pip in venv"""
        pip_path = self.get_pip_command() if self.venv_path.exists() else 'pip'
        
        try:
            subprocess.run(
                [pip_path, 'install', pkg_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=300
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Fallback to python -m pip
            try:
                python_path = self.get_python_executable() if self.venv_path.exists() else self.get_python_command()
                subprocess.run(
                    [python_path, '-m', 'pip', 'install', pkg_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=300
                )
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                return False
    
    def check_dependencies(self):
        """Check system dependencies"""
        print()
        self.fx.type_writer(self.fx.matrix_prompt('SCANNING SYSTEM FOR REQUIRED TOOLS...'), 0.04)
        print()
        print()
        
        deps = ['nmap', 'msfconsole']
        missing = []
        
        for dep in deps:
            self.fx.loading_dots(f'[*] Checking for {dep}', 0.8)
            
            result = subprocess.run(['which', dep], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                print(self.fx.status('success', f'{dep} - FOUND'))
            else:
                print(self.fx.status('error', f'{dep} - NOT FOUND'))
                missing.append(dep)
        
        print()
        
        if missing:
            print(self.fx.status('warning', f'MISSING DEPENDENCIES: {", ".join(missing)}'))
            print()
            print(self.fx.colors['neon_yellow'] + 'Please install the following:' + self.fx.colors['reset'])
            if 'nmap' in missing:
                print(self.fx.colors['white'] + '  • Nmap: https://nmap.org/download.html' + self.fx.colors['reset'])
            if 'msfconsole' in missing:
                print(self.fx.colors['white'] + '  • Metasploit: https://metasploit.com/download' + self.fx.colors['reset'])
            print()
            
            response = input(self.fx.colors['neon_cyan'] + 'Continue anyway? (y/N): ' + self.fx.colors['reset'])
            if response.lower() != 'y':
                print(self.fx.status('error', 'INSTALLATION ABORTED'))
                sys.exit(1)
        else:
            print(self.fx.status('success', 'ALL SYSTEM DEPENDENCIES VERIFIED'))
        print()
    
    def check_ollama(self):
        """Check if Ollama is installed"""
        print()
        self.fx.type_writer(self.fx.matrix_prompt('CHECKING AI ENGINE (OLLAMA)...'), 0.04)
        print()
        print()
        
        self.fx.loading_dots('[*] Detecting Ollama installation', 1.0)
        
        result = subprocess.run(['which', 'ollama'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            print(self.fx.status('success', 'Ollama - DETECTED'))
            
            # Check if dolphin-llama3:8b model is installed
            self.fx.loading_dots('[*] Checking for dolphin-llama3:8b model', 1.0)
            result = subprocess.run(['ollama', 'list'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if 'dolphin-llama3' in result.stdout:
                print(self.fx.status('success', 'AI Model dolphin-llama3:8b - READY'))
            else:
                print(self.fx.status('warning', 'AI Model dolphin-llama3:8b - NOT INSTALLED'))
                print(self.fx.colors['neon_yellow'] + '\nTo install the required AI model, run:' + self.fx.colors['reset'])
                print(self.fx.colors['white'] + '  ollama pull dolphin-llama3:8b' + self.fx.colors['reset'])
        else:
            print(self.fx.status('error', 'Ollama - NOT FOUND'))
            print(self.fx.colors['neon_red'] + '\nOllama is REQUIRED for Nighthawk!' + self.fx.colors['reset'])
            print(self.fx.colors['white'] + 'Install from: https://ollama.ai/download' + self.fx.colors['reset'])
            print()
            sys.exit(1)
        print()
    
    def install_packages(self):
        """Install all Python packages with hacker aesthetics"""
        print()
        install_text = """[*] DEPLOYING SECURITY MODULES
[+] Injecting dependencies into system
[*] Establishing encrypted channels"""
        
        print(self.fx.box(install_text, '< MODULE DEPLOYMENT >'))
        print()
        
        self.fx.type_writer(self.fx.matrix_prompt('SCANNING EXISTING SECURITY MODULES...'), 0.04)
        print()
        self.fx.loading_dots('[*] Checking system for existing modules', 2.0)
        
        missing_packages = []
        installed_packages = []
        
        # Scan with single progress bar
        for i, pkg in enumerate(self.packages, 1):
            self.fx.update_progress(i, len(self.packages), f'[*] Scanning {pkg}')
            
            if self.check_package_installed(pkg):
                installed_packages.append(pkg)
            else:
                missing_packages.append(pkg)
        
        sys.stdout.write('\r\x1b[K')
        sys.stdout.flush()
        
        print(self.fx.status('success', 
              f'RECONNAISSANCE COMPLETE: {len(installed_packages)} already deployed, {len(missing_packages)} missing'))
        print()
        
        if missing_packages:
            self.fx.type_writer(self.fx.matrix_prompt('DEPLOYING MISSING SECURITY MODULES...'), 0.04)
            print()
            print()
            
            # Install with single progress bar at bottom
            for i, pkg in enumerate(missing_packages, 1):
                self.fx.update_progress(i - 1, len(missing_packages), f'[*] Deploying {pkg}')
                
                success = self.run_pip_install(pkg)
                
                sys.stdout.write('\r\x1b[K')
                sys.stdout.flush()
                
                if success:
                    print(self.fx.status('success', f'[{i}/{len(missing_packages)}] {pkg} - DEPLOYED'))
                else:
                    print(self.fx.status('error', f'[{i}/{len(missing_packages)}] {pkg} - FAILED'))
            
            print()
            print(self.fx.status('success', 'ALL SECURITY MODULES SUCCESSFULLY DEPLOYED'))
            print()
        else:
            print(self.fx.status('info', 'ALL SECURITY MODULES ALREADY DEPLOYED - SKIPPING INSTALLATION'))
            print()
    
    def run_python_test(self, code):
        """Run a test using the virtual environment's Python"""
        python_path = self.get_python_executable() if self.venv_path.exists() else self.get_python_command()
        
        try:
            result = subprocess.run(
                [python_path, '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False
    
    def test_packages(self):
        """Test if packages are working with hacker theme"""
        print()
        test_text = """[*] INITIATING SYSTEM DIAGNOSTICS
[+] Testing module integrity
[*] Verifying security protocols"""
        
        print(self.fx.box(test_text, '< DIAGNOSTIC MODE >'))
        print()
        
        self.fx.loading_dots('[*] Running diagnostic suite', 2.0)
        
        tests = [
            ('Rich UI Framework', 'from rich.console import Console; Console().print("✓")'),
            ('Ollama AI Engine', 'import ollama'),
            ('Environment Variables', 'from dotenv import load_dotenv; load_dotenv()'),
            ('Google Generative AI', 'import google.generativeai'),
        ]
        
        all_passed = True
        
        for test_name, test_code in tests:
            success = self.run_python_test(test_code)
            
            if success:
                print(self.fx.status('success', f'{test_name} - OPERATIONAL'))
            else:
                print(self.fx.status('error', f'{test_name} - MALFUNCTION'))
                all_passed = False
        
        print()
        
        if all_passed:
            print(self.fx.colors['neon_green'] + '>>> ALL SYSTEMS OPERATIONAL <<<' + self.fx.colors['reset'])
        else:
            print(self.fx.colors['neon_red'] + '>>> SYSTEM ERRORS DETECTED <<<' + self.fx.colors['reset'])
        
        print()
        return all_passed
    
    def setup_environment(self):
        """Setup .env file"""
        print()
        self.fx.type_writer(self.fx.matrix_prompt('CONFIGURING ENVIRONMENT...'), 0.04)
        print()
        print()
        
        env_file = Path('.env')
        
        if env_file.exists():
            print(self.fx.status('info', '.env file already exists - SKIPPING'))
        else:
            print(self.fx.colors['neon_cyan'] + '[?] Do you want to configure Google Gemini API? (optional)' + self.fx.colors['reset'])
            response = input(self.fx.colors['white'] + '    (y/N): ' + self.fx.colors['reset'])
            
            if response.lower() == 'y':
                api_key = input(self.fx.colors['neon_cyan'] + '[?] Enter Google API Key: ' + self.fx.colors['reset'])
                
                with open('.env', 'w') as f:
                    f.write(f'GOOGLE_API_KEY={api_key}\n')
                
                print(self.fx.status('success', '.env file created'))
            else:
                print(self.fx.status('info', 'Skipping Gemini API configuration'))
        print()
    
    def test_installation(self):
        """Test the installation"""
        self.fx.type_writer(self.fx.matrix_prompt('RUNNING FINAL DIAGNOSTICS...'), 0.04)
        print()
        print()
        
        # Use the new test_packages method
        all_passed = self.test_packages()
        
        return all_passed
    
    def show_completion(self):
        """Show completion message"""
        print()
        
        self.fx.type_writer(self.fx.matrix_prompt('NIGHTHAWK INSTALLATION COMPLETE'), 0.04)
        print()
        self.fx.type_writer(self.fx.matrix_prompt('ALL SYSTEMS OPERATIONAL'), 0.04)
        print()
        time.sleep(0.6)
        
        print(self.fx.colors['neon_green'] + '[' + '═' * 76 + ']' + self.fx.colors['reset'])
        self.fx.hack_animation(1.5)
        print(self.fx.colors['neon_green'] + '[' + '═' * 76 + ']' + self.fx.colors['reset'])
        print()
        
        final_text = """▓▓▓ NIGHTHAWK READY FOR DEPLOYMENT ▓▓▓
[+] AI-Powered Penetration Testing Active
[*] All security tools initialized
[!] Use responsibly and only on authorized targets

[*] TO LAUNCH NIGHTHAWK:
  ./start.sh

[+] System ready for engagement"""
        
        print(self.fx.colors['neon_green'] + self.fx.box(final_text, '< INSTALLATION COMPLETE - LINUX >') + self.fx.colors['reset'])
        print()
        
        self.fx.glitch_text('Stay in the shadows, hacker.', 4)
        print()
        print()
        
        print(self.fx.colors['neon_green'] + '[' + '═' * 38 + ']' + self.fx.colors['reset'])
        print(self.fx.colors['neon_cyan'] + '     [*] NIGHTHAWK INITIALIZED [*]' + self.fx.colors['reset'])
        print(self.fx.colors['neon_green'] + '[' + '═' * 38 + ']' + self.fx.colors['reset'])
        print()
    
    def run(self):
        """Main installation flow"""
        try:
            self.show_header()
            self.check_dependencies()
            self.check_ollama()
            
            # Load requirements.txt first
            self.load_requirements()
            
            # Create venv if needed
            self.create_venv()
            
            # Install packages
            self.install_packages()
            
            # Setup environment
            self.setup_environment()
            
            # Test installation
            self.test_installation()
            
            # Show completion
            self.show_completion()
            
        except KeyboardInterrupt:
            print()
            print(self.fx.status('warning', 'INSTALLATION INTERRUPTED'))
            print(self.fx.colors['neon_red'] + 'Installation aborted by user.' + self.fx.colors['reset'])
            sys.exit(1)
        except Exception as e:
            print()
            print(self.fx.status('error', f'CRITICAL ERROR: {str(e)}'))
            sys.exit(1)


if __name__ == '__main__':
    installer = NighthawkInstaller()
    installer.run()
