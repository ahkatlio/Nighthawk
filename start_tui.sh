# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

clear
echo -e "${CYAN}"
cat banner.txt
echo -e "${NC}"
echo -e "${MAGENTA}${BOLD}       🦅 AI-Powered Security Assessment Platform 🦅${NC}"
echo -e "${WHITE}            Terminal User Interface (TUI) Mode${NC}"
echo -e ""

echo -e "${BOLD}${WHITE}Initializing Nighthawk TUI...${NC}\n"

# Check if we're in the right directory
if [ ! -f "main_TUI.py" ]; then
    echo -e "${RED}✗ Error: main_TUI.py not found!${NC}"
    echo -e "${YELLOW}Please run this script from the Nighthawk directory.${NC}"
    exit 1
fi

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Start Ollama service if available
if command_exists systemctl && command_exists ollama; then
    echo -e "${CYAN}${BOLD}[0/5]${NC} ${WHITE}Starting Ollama service...${NC}"
    if systemctl is-active --quiet ollama; then
        print_status 0 "Ollama service already running"
    else
        sudo systemctl start ollama 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status 0 "Ollama service started"
        else
            echo -e "${YELLOW}⚠ Could not start Ollama service (may need manual start)${NC}"
        fi
    fi
    echo ""
fi

echo -e "${CYAN}${BOLD}[1/5]${NC} ${WHITE}Setting up Python environment...${NC}"

PYTHON_CMD="python3"

if [ -d ".venv" ]; then
    print_status 0 "Virtual environment found"
    source .venv/bin/activate 2>/dev/null
    if [ $? -eq 0 ]; then
        print_status 0 "Virtual environment activated"
        PYTHON_CMD=".venv/bin/python"
    else
        echo -e "${YELLOW}⚠ Could not activate venv, using system Python${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
    echo -e "${DIM}  Tip: Create one with 'python3 -m venv .venv'${NC}"
fi

echo -e "\n${CYAN}${BOLD}[2/5]${NC} ${WHITE}Performing system checks...${NC}"

if command_exists $PYTHON_CMD || [ -x "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_status 0 "Python ${PYTHON_VERSION} detected"
else
    print_status 1 "Python 3 not found"
    exit 1
fi

echo -e "\n${CYAN}${BOLD}[3/5]${NC} ${WHITE}Verifying dependencies...${NC}"

if $PYTHON_CMD -c "import textual" 2>/dev/null; then
    TEXTUAL_VERSION=$($PYTHON_CMD -c "import textual; print(textual.__version__)" 2>/dev/null)
    print_status 0 "Textual ${TEXTUAL_VERSION} installed"
else
    print_status 1 "Textual not found"
    echo -e "${YELLOW}Installing Textual...${NC}"
    $PYTHON_CMD -m pip install textual -q
    if [ $? -eq 0 ]; then
        print_status 0 "Textual installed successfully"
    else
        echo -e "${RED}Failed to install Textual. Please run: pip install textual${NC}"
        exit 1
    fi
fi

# Check for Kali tools (optional)
echo -e "\n${CYAN}${BOLD}[4/5]${NC} ${WHITE}Checking security tools availability...${NC}"

if command_exists nmap; then
    NMAP_VERSION=$(nmap --version | head -n1 | cut -d' ' -f3)
    print_status 0 "Nmap ${NMAP_VERSION}"
else
    print_status 1 "Nmap not found (optional)"
fi

if command_exists msfconsole; then
    print_status 0 "Metasploit Framework"
else
    print_status 1 "Metasploit not found (optional)"
fi

if command_exists sqlmap; then
    print_status 0 "SQLMap"
else
    print_status 1 "SQLMap not found (optional)"
fi

echo -e "\n${CYAN}${BOLD}[5/5]${NC} ${WHITE}Checking AI model configuration...${NC}"

if [ -f ".env" ]; then
    print_status 0 ".env file found"
    if grep -q "GOOGLE_API_KEY" .env 2>/dev/null; then
        print_status 0 "Gemini API key configured"
    else
        echo -e "${YELLOW}⚠ Gemini API key not found in .env${NC}"
        echo -e "${DIM}  Set GOOGLE_API_KEY in .env for AI features${NC}"
    fi
else
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    echo -e "${DIM}  Create .env with your API keys for full functionality${NC}"
fi

if command_exists ollama; then
    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "\n${YELLOW}Starting Ollama service...${NC}"
        ollama serve > /dev/null 2>&1 &
        sleep 2
        if pgrep -x "ollama" > /dev/null; then
            print_status 0 "Ollama service started"
        fi
    else
        print_status 0 "Ollama already running"
    fi
fi

# Final launch
echo -e "\n${MAGENTA}${BOLD}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}✓ All checks complete!${NC}"
echo -e "${MAGENTA}${BOLD}════════════════════════════════════════════════════════${NC}\n"

sleep 1

if [ -f "animations/intro.sh" ]; then
    bash animations/intro.sh
else
    clear
fi

echo -e "${CYAN}${BOLD}Launching Nighthawk TUI...${NC}"
echo -e "${DIM}Press Ctrl+C to exit the TUI${NC}\n"

sleep 1

$PYTHON_CMD main_TUI.py

EXIT_CODE=$?

if [ -f "animations/outro.sh" ]; then
    bash animations/outro.sh $EXIT_CODE
else
    echo -e "\n${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}"
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Nighthawk TUI exited normally${NC}"
    else
        echo -e "${YELLOW}⚠ TUI exited with code: ${EXIT_CODE}${NC}"
    fi
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}\n"
    echo -e "\n${DIM}Thank you for using Nighthawk! 🦅${NC}"
fi

echo -e "${CYAN}Cleaning up services...${NC}"
if command_exists systemctl && command_exists ollama; then
    if systemctl is-active --quiet ollama; then
        echo -e "${YELLOW}Stopping Ollama service...${NC}"
        sudo systemctl stop ollama 2>/dev/null
        if [ $? -eq 0 ]; then
            print_status 0 "Ollama service stopped"
        else
            echo -e "${YELLOW}⚠ Could not stop Ollama service${NC}"
        fi
    fi
fi
