# Metasploit Integration 💥

Nighthawk now integrates **Metasploit Framework** with **context awareness** - it remembers your nmap scans and uses that data to find relevant exploits!

## Key Features

### 🧠 Memory-Powered Exploit Search
- Remembers nmap scan results from earlier in the session
- Automatically targets discovered services and versions
- No need to manually specify ports or services

### 🎯 Context-Aware Commands
- Parses nmap output to extract:
  - Open ports
  - Service names
  - Service versions
  - Operating system
  - IP addresses
- Generates Metasploit commands based on this data

### 🤖 AI-Driven Exploit Suggestions
- AI analyzes scan results
- Suggests appropriate search queries
- Recommends specific exploit modules
- Sets RHOSTS, RPORT automatically

## How It Works

### Step 1: Scan with Nmap
```bash
You: scan target.com
```

Nighthawk runs nmap and **stores the results**:
- Target: target.com
- IP: 192.168.1.100
- Open Ports:
  - 22: SSH (OpenSSH 7.4)
  - 80: HTTP (nginx 1.14.0)
  - 3306: MySQL (5.5.60)

### Step 2: Find Exploits
```bash
You: find exploits
# or
You: find exploits for mysql
# or
You: check for vulnerabilities
```

Nighthawk:
1. ✅ Retrieves previous scan data
2. 🤖 AI generates Metasploit commands targeting discovered services
3. 💥 Executes msfconsole with resource script
4. 📊 Shows results and analysis

### Example AI-Generated Commands
```ruby
search mysql 5.5
use exploit/linux/mysql/mysql_yassl_hello
set RHOSTS target.com
set RPORT 3306
info
```

## Usage Examples

### Basic Exploit Search
```
You: scan example.com
[Finds SSH, HTTP, MySQL]

You: find exploits
→ Searches for exploits for all discovered services
→ Prioritizes based on versions
```

### Targeted Exploit Search
```
You: scan target.com
[Finds multiple services]

You: find mysql exploits
→ Focuses only on MySQL
→ Uses detected MySQL version (5.5.60)
```

### Follow-Up Analysis
```
You: scan website.com
[Finds Apache 2.4.10 on port 80]

You: what vulnerabilities exist for apache?
→ AI remembers Apache 2.4.10
→ Searches Metasploit database
→ Suggests relevant exploits
```

## Architecture

### Data Flow
```
┌──────────┐
│   Nmap   │ → Scans target
└────┬─────┘
     │
     ├─ Raw output stored in scan_results{}
     │
     └─ Parsed data stored in scan_results{}_parsed
            ↓
┌────────────────┐
│  Metasploit    │ → Uses parsed data
│  Tool          │    - Target IP
│                │    - Open ports
│                │    - Service versions
│                │    - OS info
└────────────────┘
```

### Memory Structure
```python
scan_results = {
    'target.com': '<raw nmap output>',
    'target.com_parsed': {
        'target': 'target.com',
        'ip': '192.168.1.100',
        'open_ports': [
            {'port': '22', 'service': 'ssh', 'version': 'OpenSSH 7.4'},
            {'port': '3306', 'service': 'mysql', 'version': '5.5.60'}
        ],
        'services': ['ssh', 'mysql'],
        'os': 'Linux 3.x'
    },
    'target.com_metasploit': '<metasploit results>'
}
```

## AI Prompt Engineering

### Context Provided to AI
When generating Metasploit commands, the AI receives:

```
=== PREVIOUS SCAN DATA ===
Target: target.com
IP Address: 192.168.1.100

Open Ports Found:
  - Port 22: ssh (OpenSSH 7.4)
  - Port 3306: mysql (5.5.60)

Operating System: Linux 3.x
=== END SCAN DATA ===
```

### AI Instructions
- Generate actual executable msfconsole commands
- Use scan data to target specific services/versions
- Start with `search` commands for relevant exploits
- Include `use`, `set RHOSTS`, `set RPORT` commands
- Suggest `info` commands to learn about exploits

## Technical Details

### Resource Script Generation
Nighthawk creates temporary Metasploit resource scripts:
```ruby
# Nighthawk Metasploit Resource Script
search mysql 5.5
use exploit/linux/mysql/mysql_yassl_hello
set RHOSTS target.com
set RPORT 3306
info
exit
```

### Execution
```bash
msfconsole -q -r /tmp/nighthawk_XXXXX.rc
```

### Cleanup
- Resource scripts are deleted after execution
- All scan data cleared on exit (privacy protection)

## Keywords That Trigger Metasploit

Any of these words in your request will activate Metasploit mode:
- `exploit`
- `metasploit`
- `msfconsole`
- `vulnerability`
- `vuln`
- `hack`

## Requirements

### Install Metasploit (Kali Linux)
```bash
# Usually pre-installed on Kali
sudo apt update
sudo apt install metasploit-framework

# Initialize database
sudo msfdb init
```

### Verify Installation
```bash
msfconsole --version
```

## Privacy & Security

### Temporary Storage Only
- All scan results stored **only in RAM**
- No disk persistence
- Auto-deleted on exit

### No Actual Exploitation
- Nighthawk only **searches** for exploits by default
- Does not automatically run exploits
- User must explicitly ask to `run` or `exploit`

## Limitations

### Current Implementation
- Searches for exploits but doesn't auto-execute them
- Requires manual intervention for actual exploitation
- Best for reconnaissance and vulnerability assessment

### Future Enhancements
- Interactive exploit execution
- Session management
- Post-exploitation automation
- Integration with other Metasploit features (auxiliary, payloads)

## Example Workflow

### Complete Penetration Testing Flow
```
# 1. Reconnaissance
You: scan target.com
→ Discovers services

# 2. Vulnerability Assessment  
You: find exploits
→ Searches Metasploit database
→ Shows matching exploits

# 3. Analysis
You: what are the most critical vulnerabilities?
→ AI analyzes findings
→ Prioritizes risks

# 4. Next Steps
You: how do I test the mysql vulnerability?
→ AI provides guidance
→ Suggests specific commands

# 5. Cleanup
You: quit
→ All data deleted
```

## Troubleshooting

### "Metasploit not found"
```bash
# Check installation
which msfconsole

# Install if missing (Kali)
sudo apt install metasploit-framework
```

### "No scan data available"
- Run an nmap scan first
- Make sure it completes successfully
- Check that ports were found

### "Could not generate commands"
- Check Ollama is running: `ollama serve`
- Verify model is available: `ollama list`
- Try more specific requests

## Best Practices

1. **Always scan first** with nmap to gather target info
2. **Be specific** in exploit requests ("find mysql exploits" vs "find exploits")
3. **Review results** before taking action
4. **Legal use only** - only test systems you own or have permission to test
5. **Clean up** - type `quit` to clear all data when done

## See Also

- [Auto-Sudo Documentation](AUTO_SUDO.md)
- [Conversation Memory](CONVERSATION_MEMORY.md)
- [Project Structure](RESTRUCTURE_COMPLETE.md)
- [Metasploit Official Docs](https://docs.metasploit.com/)

---

**Remember**: Nighthawk is for **authorized security testing only**. Always get explicit permission before testing any system you don't own.
