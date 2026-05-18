sudo apt install python3
sudo apt install python3-pip -y
apt install python3-venv python3-full -y
sudo apt install python-is-python3
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3
curl -fsSL https://ollama.com/install.sh | sh
python3 -m venv ollama
source ollama/bin/activate
pip3 install -r ollama_requirements.txt
