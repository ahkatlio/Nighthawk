# 🦅 Nighthawk Security Assistant

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-00ff00.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-00ff00.svg)](https://www.python.org/downloads/)
[![Arch Linux](https://img.shields.io/badge/Arch-Linux-00ff00?logo=arch-linux)](https://archlinux.org/)

**AI-Powered Penetration Testing Framework**

*Transform natural language into professional security assessments*

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage-guide) • [Tools](#-integrated-tools)

</div>

---

## ✨ What is Nighthawk?

Nighthawk is an intelligent security assistant that bridges the gap between conversational input and professional penetration testing. Simply describe what you want to accomplish, and Nighthawk translates your intent into precise security commands, executes them, and provides AI-powered analysis of the results.

**Powered by:**
- 🤖 **Ollama** - Local AI inference for intelligent command generation
- 🎯 **Google Gemini** - Advanced natural language understanding
- 🔧 **Modular Architecture** - Plugin-based tool system for extensibility

---

## 🚀 Features

### 🎨 Beautiful TUI Interface
- **Terminal User Interface** - Sleek, responsive design with real-time updates
- **Matrix Rain Animation** - Eye-catching startup sequence
- **Tabbed Navigation** - Switch between Chat, Scan, and Settings views
- **Syntax Highlighting** - Color-coded output for better readability

### 🧠 Intelligent Command Processing
- **Natural Language Interface** - Talk naturally, no need to memorize commands
- **Context-Aware** - Remembers previous scans and builds on them
- **Auto-Correction** - Smart error handling and command refinement
- **Intent Classification** - Automatically distinguishes between chat and security operations

### 🔒 Security & Privacy
- **In-Memory Processing** - All data stored temporarily, wiped on exit
- **Local AI** - Ollama runs entirely on your machine
- **No External Logging** - Your security assessments stay private

### 🛠️ Professional Tooling
- **Nmap Integration** - Network scanning with intelligent flag management
- **Metasploit Framework** - Context-aware exploit matching
- **More Tools Coming Soon** - SQLMap, Nikto, Gobuster, Hydra, and more!

---

## 📋 Prerequisites

### System Requirements
- **OS**: Arch Linux (or Arch-based: Manjaro, EndeavourOS, Garuda)
- **Python**: 3.8 or higher
- **RAM**: 8GB recommended (4GB minimum)
- **Disk**: 5GB free space

> 💡 **Note**: Ubuntu/Debian support is planned for future releases

---

## ⚡ Installation

### Quick Setup (Arch Linux)

```bash
# 1. Update system
sudo pacman -Syu

# 2. Install core dependencies
sudo pacman -S python python-pip nmap

# 3. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl enable ollama
sudo systemctl start ollama

# 4. Pull AI model
ollama pull dolphin-llama3:8b

# 5. Install Metasploit (optional but recommended)
# Using BlackArch repository
curl -O https://blackarch.org/strap.sh
chmod +x strap.sh && sudo ./strap.sh
sudo pacman -S metasploit

# Or using AUR
yay -S metasploit

# 6. Setup Nighthawk
cd ~/Documents/Nighthawk

# Run automated installer
python install.py

# Make launch scripts executable
chmod +x start_tui.sh start.sh

# 7. Configure Google Gemini (optional, for enhanced AI)
# Create .env file and add: GOOGLE_API_KEY=your_key_here
```

### Verify Installation

```bash
# Check Ollama
ollama list

# Test Nighthawk TUI
./start_tui.sh
```

---

## 🎯 Usage Guide

### Launching Nighthawk

```bash
# Terminal User Interface (Recommended)
./start_tui.sh

# Command-Line Interface
./start.sh
```

### 💬 Chat Tab - Conversational Interface

Ask questions, get help, or have casual conversations:

```
You: What tools do you have available?
Nighthawk: I have integrated Nmap for network scanning and Metasploit for exploitation...

You: How do I scan a website?
Nighthawk: Simply say "scan example.com" and I'll perform reconnaissance...

You: What vulnerabilities did you find?
Nighthawk: Based on the last scan, I found SSH running on port 22...
```

### 🔍 Scan Tab - Security Operations

Perform actual security assessments:

```bash
# Basic Network Scan
scan scanme.nmap.org

# Fast Local Network Discovery
quick scan 192.168.1.0/24

# Comprehensive Scan with Service Detection
scan example.com with version detection

# OS Fingerprinting (requires sudo)
scan target.com and detect OS

# Extract from URL
scan https://example.com/path
→ Automatically extracts hostname: example.com
```

### 💥 Multi-Stage Assessment Workflow

**Stage 1: Reconnaissance**
```
You: scan target.example.com
→ 🔍 Discovers: SSH (22), HTTP (80/Apache 2.4.6), MySQL (3306/5.7.33)
→ Results cached in session memory
```

**Stage 2: Analysis**
```
You: What vulnerabilities did you find?
→ 💬 AI analyzes results and identifies potential risks
→ Suggests next steps
```

**Stage 3: Exploitation (Authorized Only!)**
```
You: find exploits for mysql version 5.7.33
→ 💥 Searches Metasploit database
→ Lists applicable exploits with descriptions

You: exploit that target
→ 🎯 Launches exploitation workflow
→ Real-time progress updates
```

**Stage 4: Clean Exit**
```
You: quit
→ 🧹 All session data securely wiped from memory
```

### ⚙️ Settings Tab

- **View Configuration** - Check current AI models and API settings
- **Model Selection** - Switch between Ollama and Gemini
- **Theme Options** - Customize TUI appearance (coming soon)

---

## 🛠️ Integrated Tools

| Tool | Status | Description |
|------|--------|-------------|
| **Nmap** | ✅ Active | Network scanning, service detection, OS fingerprinting |
| **Metasploit** | ✅ Active | Vulnerability exploitation, payload generation |
| **SQLMap** | 🔜 Soon | SQL injection detection and exploitation |
| **Nikto** | 🔜 Soon | Web server vulnerability scanning |
| **Gobuster** | 🔜 Soon | Directory and file enumeration |
| **Hydra** | 🔜 Soon | Network authentication cracking |
| **WPScan** | 🔜 Soon | WordPress security scanner |
| **Burp Suite** | 🔜 Soon | Web application security testing |

> 💡 More tools are being integrated regularly. Check back for updates!

---

## 🎨 Interface Features

### TUI Navigation

- **Tab**: Switch between Chat, Scan, and Settings
- **Ctrl+Q**: Exit Nighthawk
- **Enter**: Send message/command
- **↑/↓**: Navigate command history

### Command Recognition

Nighthawk intelligently understands intent:

```bash
# These all trigger network scanning:
"scan example.com"
"check example.com for vulnerabilities"
"run nmap on example.com"
"do reconnaissance on example.com"

# These trigger chat mode:
"what is nmap?"
"how do I use this tool?"
"what did the scan find?"
```

---

## 🐛 Troubleshooting

### Ollama Not Responding

```bash
systemctl status ollama
sudo systemctl start ollama
ollama list
```

### Missing AI Model

```bash
ollama pull dolphin-llama3:8b
```

### Permission Issues with Nmap

Nighthawk automatically adds `sudo` for privileged scans:
```
You: scan example.com with OS detection
→ Executes: sudo nmap -O example.com
→ Prompts for password
```

### Python Dependencies

```bash
source .venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

## ⚠️ Legal & Ethical Use

<div align="center">

**🚨 IMPORTANT: Only use on systems you own or have explicit written permission to test 🚨**

</div>

### Responsible Security Testing

- ✅ Authorized penetration testing with signed agreements
- ✅ Personal lab environments and practice targets
- ✅ Bug bounty programs with defined scope
- ❌ Unauthorized network scanning
- ❌ Exploitation without permission
- ❌ Malicious activities

### Privacy Commitment

- 🔒 All scan results stored in-memory only
- 🔒 Data automatically deleted on exit
- 🔒 No persistent logs unless configured
- 🔒 Local AI processing (Ollama)

---

## 📦 Project Structure

```
Nighthawk/
├── main.py                    # Core AI orchestrator
├── main_TUI.py               # Terminal user interface
├── tui/                       # TUI components
│   ├── tabs/                  # Chat, Scan, Settings tabs
│   └── widgets/              # Custom UI elements
├── tools/                     # Security tool integrations
│   ├── nmap_tool.py          # Nmap wrapper
│   └── metasploit_tool.py    # Metasploit integration
├── start.sh                   # CLI launcher
├── start_tui.sh              # TUI launcher with animation
└── requirements.txt           # Python dependencies
```

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-tool`)
3. Commit changes (`git commit -m 'Add new security tool'`)
4. Push to branch (`git push origin feature/new-tool`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the **MIT License**.

---

## 🙏 Acknowledgments

- **Ollama Team** - Local AI inference engine
- **Google Gemini** - Advanced language models
- **Nmap Project** - Network reconnaissance framework
- **Metasploit Framework** - Exploitation platform
- **Textual** - Modern TUI framework
- **Arch Linux Community** - Best rolling release distro

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ahkatlio/Nighthawk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ahkatlio/Nighthawk/discussions)
- **Author**: ahkatlio

---

<div align="center">

**🚀 Ready to begin?**

```bash
./start_tui.sh
```

*Stay ethical. Stay legal. Stay curious.* 🦅

**Made with ❤️ for the Arch Linux community**

</div>

