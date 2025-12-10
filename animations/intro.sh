SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

# Color codes
GREEN='\033[0;32m'
NEON_GREEN='\033[92m'
NC='\033[0m'

clear
tput civis  

cols=$(tput cols)
rows=$(tput lines)

if [ ! -f "$SCRIPT_DIR/banner.txt" ]; then
    echo "Error: banner.txt not found"
    exit 1
fi

mapfile -t nighthawk_art < "$SCRIPT_DIR/banner.txt"

art_height=${#nighthawk_art[@]}
art_width=${#nighthawk_art[0]}
start_row=$(((rows - art_height) / 2))
start_col=$(((cols - art_width) / 2))

chars=(0 1 2 3 4 5 6 7 8 9 A B C D E F G H I J K L M N O P Q R S T U V W X Y Z a b c d e f g h i j k l m n o p q r s t u v w x y z @ '#' $ % '&' '*')

for ((line=0; line<art_height; line++)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        if [ "$char" = " " ]; then
            continue
        fi
        random_char=${chars[$((RANDOM % ${#chars[@]}))]}
        tput cup $target_row $target_col
        echo -ne "\033[32m$random_char\033[0m"
    done
done

sleep 0.5

for ((line=$((art_height-1)); line>=0; line--)); do
    text="${nighthawk_art[$line]}"
    target_row=$((start_row + line))
    for ((col_offset=0; col_offset<${#text}; col_offset++)); do
        final_char="${text:$col_offset:1}"
        target_col=$((start_col + col_offset))
        if [ "$final_char" = " " ]; then
            continue
        fi
        tput cup $target_row $target_col
        echo -ne "\033[92m$final_char\033[0m"
    done
    sleep 0.1
done

sleep 1

tput cnorm  
clear  