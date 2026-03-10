#!/bin/bash

# 1. Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "[!] Python3 not found. Please install it from python.org"
    exit
else
    echo "[+] Python3 detected."
fi

# 2. Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[!] Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate and Install Dependencies
echo "[!] Updating libraries..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the application
echo "[+] Starting ADC Visualizer..."
python3 src/main.py