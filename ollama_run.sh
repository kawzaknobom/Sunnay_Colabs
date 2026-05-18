sudo apt update -y
sudo apt-get install zstd
sudo apt install python3
sudo apt install python3-pip -y
apt install python3-venv python3-full -y
sudo apt install python-is-python3
sudo update-alternatives --install /usr/bin/pip pip /usr/bin/pip3
curl -fsSL https://ollama.com/install.sh | sh
python3 -m venv '/content/Sunnay_Colabs/ollama'
source /content/Sunnay_Colabs/ollama/bin/activate
pip3 install -r '/content/Sunnay_Colabs/ollama_requirements.txt' 
