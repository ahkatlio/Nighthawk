# Nighthawk Command Installation Script
# Makes 'nighthawk' command available system-wide

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NIGHTHAWK_BIN="$SCRIPT_DIR/nighthawk"
INSTALL_PATH="/usr/local/bin/nighthawk"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  🦅 Nighthawk Command Installation${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

if [ ! -f "$NIGHTHAWK_BIN" ]; then
    echo -e "${RED}✗ Error: nighthawk entry script not found!${NC}"
    echo -e "${YELLOW}Please run this script from the Nighthawk directory.${NC}"
    exit 1
fi

echo -e "${BLUE}[1/3]${NC} ${CYAN}Making nighthawk script executable...${NC}"
chmod +x "$NIGHTHAWK_BIN"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} nighthawk script is executable\n"
else
    echo -e "${RED}✗ Failed to make nighthawk executable${NC}"
    exit 1
fi

echo -e "${BLUE}[2/3]${NC} ${CYAN}Installing to /usr/local/bin...${NC}"

if [ -f "$INSTALL_PATH" ]; then
    echo -e "${YELLOW}⚠ nighthawk command already exists at $INSTALL_PATH${NC}"
    read -p "  Overwrite? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled${NC}"
        exit 1
    fi
fi

if sudo ln -sf "$NIGHTHAWK_BIN" "$INSTALL_PATH" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Created symlink: $INSTALL_PATH -> $NIGHTHAWK_BIN\n"
else
    echo -e "${YELLOW}⚠ Could not create symlink (trying direct copy)${NC}"
    if sudo cp "$NIGHTHAWK_BIN" "$INSTALL_PATH"; then
        echo -e "${GREEN}✓${NC} Copied to $INSTALL_PATH\n"
    else
        echo -e "${RED}✗ Failed to install nighthawk command${NC}"
        echo -e "${YELLOW}Try running with sudo: sudo bash setup.sh${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}[3/3]${NC} ${CYAN}Verifying installation...${NC}"

if command -v nighthawk >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} nighthawk command is available\n"
else
    export PATH="/usr/local/bin:$PATH"
    if command -v nighthawk >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} nighthawk command is available\n"
        echo -e "${YELLOW}⚠ Please restart your terminal or run: source ~/.bashrc${NC}\n"
    else
        echo -e "${RED}✗ nighthawk command not found in PATH${NC}"
        echo -e "${YELLOW}Try restarting your terminal${NC}"
        exit 1
    fi
fi

echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Usage:${NC}"
echo -e "  ${GREEN}nighthawk${NC}  - Start Nighthawk TUI from anywhere\n"

echo -e "${CYAN}To uninstall:${NC}"
echo -e "  ${YELLOW}sudo rm /usr/local/bin/nighthawk${NC}\n"

echo -e "${CYAN}Next steps:${NC}"
if ! pgrep -x "ollama" > /dev/null 2>&1; then
    echo -e "  1. ${YELLOW}Start Ollama: ${NC}ollama serve${NC}"
    echo -e "  2. ${YELLOW}In another terminal, run: ${NC}nighthawk${NC}"
else
    echo -e "  ${YELLOW}Try it now: ${NC}nighthawk${NC}"
fi
echo ""
