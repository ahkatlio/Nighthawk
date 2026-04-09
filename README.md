# 🦅 Nighthawk

**Nighthawk** is an advanced, AI-powered internal orchestration assistant for penetration testers. By bridging modern Large Language Models with the **Model Context Protocol (MCP)**, Nighthawk functions as an intelligent interface over your local Kali Linux tools, allowing you to dynamically scan, enumerate, and exploit targets using plain English.

## ✨ Key Features

- **Model Context Protocol (MCP) Integration**: Nighthawk utilizes an independent, dynamically generated MCP server (`mcp-kali-server`) that exposes schemas to LLMs. This completely decouples tool definitions from AI orchestration.
- **Dual AI Engine**: Choose between the blazing-fast, cloud-based **Google Gemini (2.5 Flash)** or a localized, privacy-first **Ollama** model (`dolphin-llama3:8b`).
- **Secure Structured Execution**: LLM outputs are securely routed and parsed as JSON dictionaries—eliminating untrusted prompt evaluation loopholes.
- **TUI Interface**: A modern terminal user interface crafted with [Textual](https://textual.textualize.io/), featuring asynchronous execution, live background process logs, and split-pane chat.
- **Out-of-the-box Kali Support**: Natively binds to standard tools like Nmap, Nikto, Metasploit, Gobuster, SQLmap, Dirb, WPScan, and Hydra.

---

## 🏗 System Architecture

Nighthawk has shifted from hardcoded Python wrappers to a fully dynamic MCP pipeline:

1. **Textual UI (`tui/tabs/chat.py`)**: Runs the async front-end interface. Tasks are sandboxed securely with independent `asyncio` events to avoid cross-thread locking.
2. **AI Director (`main.py`)**: Parses your inputs, fetches the current `tools_schema` from the MCP client, and securely orchestrates Gemini/Ollama.
3. **MCP Client (`tools/mcp_client.py`)**: Uses Python's `anyio` to spin up a persistent background Flask server. The client connects to the server using standard `stdio` pipes.
4. **Local Subcommands (`tools/mcp_server/server.py`)**: Maps rigid tool logic gracefully (e.g., forcing Nmap `-T4 -Pn` to bypass ICMP drops, extending timeout blocks to 10 minutes) securely into the OS via `subprocess.Popen`.

---

## 🚀 Installation & Setup

1. **Prerequisites**:
   Ensure you are running inside a Kali Linux environment or have the core tools (`nmap`, `metasploit-framework`, etc.) installed. You also need [Ollama](https://ollama.com) installed and running locally for the local AI mode.

2. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Nighthawk.git
   cd Nighthawk
   ```

3. **Install Dependencies**:
   You can use the provided setup scripts to prep your virtual environment:
   ```bash
   ./setup.sh
   # OR manually:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **API Keys**:
   If using Google Gemini, export your API key:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

5. **Start Ollama Engine (Optional but Recommended)**:
   ```bash
   ollama pull dolphin-llama3:8b
   ```

---

## 💻 Usage

Launch the Nighthawk Textual UI using the provided start script:

```bash
./start_tui.sh
```

**Inside the application**:
- Provide targets natively in conversational format, e.g., `Scan the host at 192.168.1.10`.
- Nighthawk decides internally whether to utilize Nmap or another tool based on the capabilities advertised by the local MCP server.
- View real-time parsing schemas, AI rationale, and raw subprocess output (like `stdout` pipes from Nikto or Enum4Linux) displayed gracefully in the live console panel.

---

## 🛠 Tool Support

The MCP Kali server currently advertises the following tools natively to the orchestrator:

- **nmap_scan**: Network mapping, service discovery.
- **gobuster_scan**: Web directory, DNS, and virtual host enumeration.
- **nikto_scan**: Web server vulnerability profiling.
- **sqlmap_scan**: Automated SQL injection detection.
- **dirb_scan**: Web content brute-forcing.
- **hydra_bruteforce / john_crack**: Password attacks.
- **wpscan_analyze**: Native WordPress CMS scanning.
- **enum4linux_scan**: Windows/Samba enumeration.

---

## 🤝 Contributing

Contributions to the new MCP architecture are welcome! 
If adding a new Kali tool, implement its specific executor endpoint inside `tools/mcp_server/server.py` and register its schema block with the `@mcp.tool()` decorator inside `tools/mcp_server/client.py`. Nighthawk's AI engine will dynamically detect the new tool on its next boot and seamlessly inform LLMs that it exists!

## 📄 License
MIT License
