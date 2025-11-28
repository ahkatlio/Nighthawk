#!/bin/bash

# Nighthawk TUI Launcher
# Advanced Terminal User Interface for Nighthawk Security Assistant

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

# ASCII Art Banner
clear
echo -e "${CYAN}"
cat << "EOF"
    ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗ █████╗ ██╗    ██╗██╗  ██╗
    ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝██║  ██║██╔══██╗██║    ██║██║ ██╔╝
    ██╔██╗ ██║██║██║  ███╗███████║   ██║   ███████║███████║██║ █╗ ██║█████╔╝ 
    ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██╔══██║██╔══██║██║███╗██║██╔═██╗ 
    ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║  ██║██║  ██║╚███╔███╔╝██║  ██╗
    ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝
EOF
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
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

# Check virtual environment first
echo -e "${CYAN}${BOLD}[1/5]${NC} ${WHITE}Setting up Python environment...${NC}"

# Set Python command
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

# Check Python version (now using venv Python if available)
echo -e "\n${CYAN}${BOLD}[2/5]${NC} ${WHITE}Performing system checks...${NC}"

if command_exists $PYTHON_CMD || [ -x "$PYTHON_CMD" ]; then
    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_status 0 "Python ${PYTHON_VERSION} detected"
else
    print_status 1 "Python 3 not found"
    exit 1
fi

# Check dependencies
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

# Check API configuration
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

# Start Ollama service (if available)
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

# Clear screen for matrix effect
clear
tput civis  # Hide cursor

cols=$(tput cols)
rows=$(tput lines)

# NIGHTHAWK ASCII art
declare -a nighthawk_art=(
"███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗██╗  ██╗ █████╗ ██╗    ██╗██╗  ██╗"
"████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝██║  ██║██╔══██╗██║    ██║██║ ██╔╝"
"██╔██╗ ██║██║██║  ███╗███████║   ██║   ███████║███████║██║ █╗ ██║█████╔╝ "
"██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██╔══██║██╔══██║██║███╗██║██╔═██╗ "
"██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║  ██║██║  ██║╚███╔███╔╝██║  ██╗"
"╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝"
)

# Calculate centered position
art_height=${#nighthawk_art[@]}
art_width=${#nighthawk_art[0]}
start_row=$(((rows - art_height) / 2))
start_col=$(((cols - art_width) / 2))

# Matrix characters
chars=(0 1 2 3 4 5 6 7 8 9 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z @ '#' $ % '&' '*')

# First, draw the entire art shape with random characters
for ((line=0; line<art_height; line++)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        
        # Skip spaces
        if [ "$char" = " " ]; then
            continue
        fi
        
        # Place random character
        random_char=${chars[$((RANDOM % ${#chars[@]}))]}
        tput cup $target_row $target_col
        echo -ne "\033[32m$random_char\033[0m"
    done
done

# Small delay to show the random character art
sleep 0.5

# Now transform from bottom to top, layer by layer
for ((line=$((art_height-1)); line>=0; line--)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    
    # Process each character position in this line
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        final_char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        
        # Skip spaces
        if [ "$final_char" = " " ]; then
            continue
        fi
        
        # Transform to actual character
        tput cup $target_row $target_col
        echo -ne "\033[92m$final_char\033[0m"
    done
    
    # Small delay between layers
    sleep 0.1
done

# Hold for 1 second
sleep 1

# Cleanup
tput cnorm
clear

echo -e "${CYAN}${BOLD}Launching Nighthawk TUI...${NC}"
echo -e "${DIM}Press Ctrl+C to exit the TUI${NC}\n"

sleep 1

# Launch the TUI
$PYTHON_CMD main_TUI.py

# Cleanup message
EXIT_CODE=$?
echo -e "\n${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Nighthawk TUI exited normally${NC}"
else
    echo -e "${YELLOW}⚠ TUI exited with code: ${EXIT_CODE}${NC}"
fi
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}\n"

echo -e "${DIM}Thank you for using Nighthawk! 🦅${NC}"
