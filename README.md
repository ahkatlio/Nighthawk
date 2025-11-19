# Nighthawk Security Assistant 🦅

**AI-powered modular security tool orchestrator** using Ollama and Kali Linux tools.

## What's New ✨

### 🚀 Metasploit Integration
Nighthawk now **remembers nmap scans** and uses that data to **find exploits automatically**! Just scan a target, then ask "find exploits" and it will use Metasploit with the discovered services!

### Smart Conversation Mode
Nighthawk now **distinguishes between chatting and scanning**! Say "hey my name is Galib" and it won't try to scan galib.com. Only scans when you explicitly ask!

### Conversation Memory (Temporary)
AI **remembers previous scans** within the session - perfect for follow-up questions like "find exploits for those services". All data **auto-deletes on exit** for privacy!

### Auto-Sudo for Root Privileges
When scans need root (like OS detection with `-O`), Nighthawk **automatically adds `sudo`** and prompts for your password. No more errors!

### Fixed: "Host Seems Down" Issue
Nighthawk now **automatically adds `-Pn` flag** to skip host discovery when nmap reports hosts as down.

### Modular Architecture
- Each security tool is a separate Python module in `tools/`
- Easy to add new tools
- Clean, maintainable code structure

## Quick Start

```bash
./start.sh
```

## Features

- 🤖 **AI-Powered**: Natural language → security commands
- 🔧 **Modular**: Easy to add new tools
- 🎯 **Auto-Execute**: No confirmation prompts
- 🔍 **Smart**: Auto-fixes common issues (like `-Pn` for nmap)
- 📊 **Analysis**: AI interprets scan results

## Usage Examples

```
You: Scan https://example.com for open ports
→ Extracts: example.com
→ Runs: nmap -Pn -sV example.com
→ Shows results + AI analysis

You: Quick scan of localhost
→ Runs: nmap -Pn -F localhost
→ Shows results

You: find exploits
→ Uses previous nmap data
→ Runs: msfconsole with context-aware commands
→ Searches for exploits matching discovered services

You: tools
→ Shows all available security tools
```

### Complete Workflow Example 🔥

```
You: scan target.com
→ 🔍 Nmap finds: SSH (22), HTTP (80), MySQL (3306)

You: find exploits for mysql
→ 💥 Metasploit searches exploits for MySQL
→ Uses the version detected in previous scan
→ Suggests relevant exploits

You: quit
→ All data auto-deleted for privacy
```

## Project Structure

```
Nighthawk/
├── main.py              # 🦅 Main orchestrator
├── tools/               # 🔧 Security tool modules
│   ├── base_tool.py    # Base class
│   ├── nmap_tool.py    # Nmap (✅ integrated)
│   ├── metasploit_tool.py  # Metasploit (✅ integrated)
│   └── nikto_tool.py   # Nikto (template)
├── start.sh            # Quick launch
└── requirements.txt    # Dependencies
```

## Currently Integrated

### Nmap ✅
- Network scanning
- Service detection  
- OS detection
- Auto `-Pn` flag when needed
- URL → hostname extraction
- **Data parsing for other tools**

### Metasploit ✅
- **Context-aware exploit search**
- Uses previous nmap scan data
- Automatically targets discovered services
- Resource script generation
- Interactive exploit suggestions

### Coming Soon
- Nikto (web scanner)
- SQLmap (SQL injection)
- More tools...

## Adding New Tools

1. Create `tools/your_tool.py`:
```python
from .base_tool import BaseTool

class YourTool(BaseTool):
    def check_installed(self): ...
    def generate_command(self): ...
    def execute(self): ...
```

2. Register in `main.py`:
```python
self.tools['yourtool'] = YourTool()
```

3. Done!

## Commands

- Type your request in natural language
- `tools` - Show available tools
- `quit` / `exit` - Exit

## Requirements

- Ollama (with dolphin-llama3:8b model)
- Nmap  
- Python 3.8+

## Installation

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull dolphin-llama3:8b
ollama serve

# Install nmap
sudo apt install nmap

# Setup Nighthawk
cd Nighthawk
source .venv/bin/activate
pip install -r requirements.txt
```

## Security Notice

⚠️ Only scan networks/systems you own or have permission to test. Unauthorized scanning may be illegal.

---

**Ready? Run: `./start.sh`** 🚀
