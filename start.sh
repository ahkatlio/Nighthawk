# Start Ollama service
echo "Starting Ollama service..."
sudo systemctl start ollama

cd /home/ahkatlio/Documents/Nighthawk
source .venv/bin/activate
python main.py
