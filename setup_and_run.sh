#!/bin/bash

echo "Inductive ADC Helper Setup (Mac/Linux)"

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "[!] Python3 could not be found. Please install Python 3 to continue."
    exit 1
fi

# 2. Create Virtual Environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[!] Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate and Install Dependencies
echo "[!] Activating environment and updating libraries..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Run the application
echo "[+] Starting ADC Visualizer..."
python src/main.py