SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

# Color codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NEON_GREEN='\033[92m'
DIM_GREEN='\033[2;32m'
WHITE='\033[1;37m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

EXIT_CODE=${1:-0}

clear

echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Nighthawk TUI exited normally${NC}"
else
    echo -e "${YELLOW}⚠ TUI exited with code: ${EXIT_CODE}${NC}"
fi
echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════${NC}\n"

sleep 1

clear
tput civis 

cols=$(tput cols)
rows=$(tput lines)

if [ ! -f "$SCRIPT_DIR/banner.txt" ]; then
    echo -e "${WHITE}Thank you for using Nighthawk! 🦅${NC}\n"
    tput cnorm
    exit 0
fi

mapfile -t nighthawk_art < "$SCRIPT_DIR/banner.txt"

art_height=${#nighthawk_art[@]}
art_width=${#nighthawk_art[0]}
start_row=$(((rows - art_height) / 2))
start_col=$(((cols - art_width) / 2))

nums=(0 1 2 3 4 5 6 7 8 9)

for ((line=0; line<art_height; line++)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    tput cup $target_row $start_col
    echo -ne "${NEON_GREEN}${text}${NC}"
done

sleep 0.8

for ((line=0; line<art_height; line++)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        if [ "$char" = " " ]; then
            continue
        fi
        random_num=${nums[$((RANDOM % ${#nums[@]}))]}
        tput cup $target_row $target_col
        echo -ne "${DIM_GREEN}${random_num}${NC}"
    done
    sleep 0.08
done

sleep 0.5

for ((line=$((art_height-1)); line>=0; line--)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        if [ "$char" = " " ]; then
            continue
        fi
        tput cup $target_row $target_col
        echo -ne " "
    done
    sleep 0.05
done

sleep 0.5

clear
tput cnorm

echo -e "\n${WHITE}Thank you for using Nighthawk! 🦅${NC}\n"
