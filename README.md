# 🦅 Nighthawk Security Assistant

> **AI-powered modular security tool orchestrator leveraging Ollama and professional penetration testing frameworks**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Arch Linux](https://img.shields.io/badge/Arch-Linux-1793D1?logo=arch-linux)](https://archlinux.org/)

An intelligent security assistant that translates natural language requests into professional penetration testing workflows. Built with a modular architecture for extensibility and powered by Ollama for intelligent command generation and result analysis.

---

## 🚀 Features

### Core Capabilities

- **🤖 Natural Language Interface**: Translate conversational requests into precise security commands
- **🔧 Modular Architecture**: Plugin-based tool system for easy extensibility
- **🎯 Intelligent Execution**: Context-aware command generation with automatic error correction
- **🧠 Memory System**: Session-based scan result caching for multi-stage assessments
- **📊 AI-Powered Analysis**: Automated vulnerability assessment and actionable recommendations
- **🔒 Privacy-First**: All data stored in-memory only, auto-deleted on exit

### Integrated Tools

#### ✅ Nmap - Network Intelligence
- Service enumeration and version detection
- OS fingerprinting with auto-privilege escalation
- Smart hostname extraction from URLs
- Automatic `-Pn` flag injection for filtered hosts
- Structured data parsing for downstream tool integration

#### ✅ Metasploit Framework - Exploitation Engine
- Context-aware exploit matching using previous scan data
- Automated resource script generation
- Multi-stage attack orchestration
- Real-time exploit execution with AI guidance

---

## 📋 Prerequisites

### System Requirements
- **OS**: Arch Linux (or Arch-based distributions)
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended for Ollama)
- **Disk**: 5GB free space for models and tools

### Required Packages

The following tools must be installed on your system:

1. **Ollama** - AI inference engine
2. **Nmap** - Network scanner
3. **Metasploit Framework** - Exploitation framework (optional but recommended)
4. **Python 3** - Runtime environment

---

## 🔧 Installation

### For Arch Linux / Manjaro / EndeavourOS

#### 1. Install System Dependencies

```bash
# Update system
sudo pacman -Syu

# Install Python and pip
sudo pacman -S python python-pip

# Install Nmap
sudo pacman -S nmap

# Install Metasploit Framework (from BlackArch or AUR)
# Option A: Using BlackArch repository (recommended)
curl -O https://blackarch.org/strap.sh
chmod +x strap.sh
sudo ./strap.sh
sudo pacman -S metasploit

# Option B: Using AUR (alternative)
yay -S metasploit
# or
paru -S metasploit
```

#### 2. Install Ollama

```bash
# Install Ollama (official method)
curl -fsSL https://ollama.com/install.sh | sh

# Alternative: Install from AUR
yay -S ollama
# or
paru -S ollama

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull the AI model
ollama pull dolphin-llama3:8b
```

#### 3. Setup Nighthawk

```bash
# Clone or navigate to Nighthawk directory
cd ~/Documents/Nighthawk

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### 4. Verify Installation

```bash
# Check Ollama is running
systemctl status ollama

# Test Ollama
ollama list

# Verify Nmap
nmap --version

# Verify Metasploit (optional)
msfconsole --version

# Check Python environment
python --version
```

---

## 🎯 Quick Start

### Launch Nighthawk

```bash
# Make sure you're in the Nighthawk directory
cd ~/Documents/Nighthawk

# Run the launcher script
./start.sh
```

### First Commands

```
You: scan scanme.nmap.org
→ Performs network reconnaissance

You: exploit that target
→ Searches for applicable exploits based on scan results

You: tools
→ Lists all integrated security tools

You: quit
→ Exits and clears all session data
```

---

## 💡 Usage Examples

### Basic Reconnaissance

```
You: scan https://example.com for open ports
→ Extracts hostname: example.com
→ Executes: nmap -Pn -sV example.com
→ Displays results with AI-powered vulnerability analysis
```

### Fast Local Network Scan

```
You: quick scan of 192.168.1.0/24
→ Executes: nmap -Pn -F 192.168.1.0/24
→ Identifies active hosts and common services
```

### Multi-Stage Attack Workflow

```bash
# Stage 1: Reconnaissance
You: scan target.com
→ 🔍 Nmap discovers: SSH (22/OpenSSH 7.4), HTTP (80/Apache 2.4.6), MySQL (3306/5.7.33)
→ Results cached in session memory

# Stage 2: Exploit Discovery
You: find exploits for mysql
→ 💥 Metasploit searches CVE database using cached MySQL version
→ Identifies applicable exploits: mysql_login, mysql_enum, etc.

# Stage 3: Execution (with proper authorization)
You: exploit that target
→ 🎯 Attempts exploitation using discovered vulnerabilities
→ Real-time progress monitoring

# Stage 4: Exit
You: quit
→ 🧹 All session data securely wiped from memory
```

### Conversational Interface

Nighthawk intelligently distinguishes between security operations and casual conversation:

```
You: hey, my name is Alice
→ 💬 Chat mode: "Hello Alice! How can I help with security testing today?"

You: scan example.com
→ 🔍 Scan mode: Initiates nmap reconnaissance

You: what tools do you have?
→ 💬 Chat mode: Lists available tools with descriptions

You: exploit that website
→ 🔍 Scan mode: Begins exploitation workflow
```

---

## 📁 Project Architecture

```
Nighthawk/
├── main.py                    # Core orchestrator and AI controller
├── tools/                     # Modular tool implementations
│   ├── __init__.py
│   ├── base_tool.py          # Abstract base class for all tools
│   ├── nmap_tool.py          # Nmap integration ✅
│   ├── metasploit_tool.py    # Metasploit Framework integration ✅
│   └── nikto_tool.py         # Nikto template (coming soon)
├── start.sh                   # Launcher script
├── requirements.txt           # Python dependencies
├── .venv/                     # Virtual environment (auto-generated)
└── README.md                  # This file
```

### Tool Status

| Tool | Status | Features |
|------|--------|----------|
| **Nmap** | ✅ Production | Network scanning, service detection, OS fingerprinting, auto-sudo, smart flags |
| **Metasploit** | ✅ Production | Context-aware exploits, resource scripts, automated targeting |
| **Nikto** | 🚧 Planned | Web server vulnerability scanning |
| **SQLmap** | 🚧 Planned | SQL injection detection and exploitation |
| **Gobuster** | 🚧 Planned | Directory/file enumeration |
| **Hydra** | 🚧 Planned | Network authentication cracking |

---

## 🛠️ Development

### Adding Custom Tools

Nighthawk's modular architecture makes it simple to integrate new security tools:

#### 1. Create Tool Module

Create a new file in `tools/your_tool.py`:

```python
from .base_tool import BaseTool
import subprocess
import re

class YourTool(BaseTool):
    """Your security tool integration"""
    
    def __init__(self):
        super().__init__(
            name="yourtool",
            command="yourtool"
        )
    
    def check_installed(self) -> bool:
        """Verify tool is installed"""
        try:
            subprocess.run([self.command, "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_ai_prompt(self) -> str:
        """AI instruction for command generation"""
        return """You are an expert with YourTool.
Generate appropriate YourTool commands based on user requests.
Return ONLY the command, no explanations."""
    
    def generate_command(self, user_request: str, ai_context: str = None) -> str:
        """Generate tool command from user request"""
        # Your command generation logic
        return f"{self.command} -flag target"
    
    def execute(self, command: str) -> dict:
        """Execute the tool command"""
        return self.run_command(command)
    
    def format_output(self, result: dict, command: str):
        """Format and display results"""
        # Custom output formatting
        pass
```

#### 2. Register Tool

Add to `main.py` in the `_register_tools()` method:

```python
def _register_tools(self):
    # ... existing tools ...
    
    # Add your tool
    from tools.your_tool import YourTool
    yourtool = YourTool()
    self.tools['yourtool'] = yourtool
```

#### 3. Test Integration

```bash
./start.sh
You: yourtool scan example.com
```

---

## 🐛 Troubleshooting

### Ollama Not Running

```bash
# Check service status
systemctl status ollama

# Start service
sudo systemctl start ollama

# Enable auto-start
sudo systemctl enable ollama
```

### Model Not Found

```bash
# List installed models
ollama list

# Pull required model
ollama pull dolphin-llama3:8b
```

### Permission Denied for Nmap

Some nmap scans require root privileges. Nighthawk automatically adds `sudo` when needed:

```
You: scan example.com with OS detection
→ Executes: sudo nmap -Pn -O example.com
→ Prompts for password if required
```

### Metasploit Database Issues

```bash
# Initialize Metasploit database
sudo msfdb init

# Check database status
sudo msfdb status

# Reinitialize if needed
sudo msfdb reinit
```

### Python Dependencies

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## ⚠️ Security & Legal Notice

### Responsible Use

**Nighthawk is a penetration testing tool designed for security professionals and authorized security assessments.**

⚠️ **IMPORTANT**:
- Only use on systems you **own** or have **explicit written permission** to test
- Unauthorized access to computer systems is **illegal** in most jurisdictions
- The developers assume **no liability** for misuse of this tool
- Always follow responsible disclosure practices

### Data Privacy

- All scan results and conversation history are stored **in-memory only**
- Data is **automatically deleted** when you exit Nighthawk
- No persistent logs or data files are created (unless explicitly configured)
- Session data is not transmitted externally (except to local Ollama instance)

### Compliance

Ensure compliance with:
- Computer Fraud and Abuse Act (CFAA) - United States
- Computer Misuse Act - United Kingdom  
- Local cybersecurity and data protection regulations
- Your organization's security policies

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-tool`)
3. **Commit** your changes (`git commit -m 'Add YourTool integration'`)
4. **Push** to the branch (`git push origin feature/amazing-tool`)
5. Open a **Pull Request**

### Development Setup

```bash
# Clone repository
git clone https://github.com/ahkatlio/Nighthawk.git
cd Nighthawk

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests (when available)
pytest tests/
```

---

## 📝 License

This project is licensed under the **MIT License** - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ollama** - Local AI inference engine
- **Nmap Project** - Network scanning framework
- **Metasploit Framework** - Exploitation platform
- **Rich** - Terminal formatting library
- **Arch Linux Community** - Package management and support

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/ahkatlio/Nighthawk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ahkatlio/Nighthawk/discussions)
- **Author**: ahkatlio

---

**🚀 Ready to begin? Run: `./start.sh`**

*Stay ethical. Stay legal. Stay curious.* 🦅
