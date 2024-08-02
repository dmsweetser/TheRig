#!/bin/bash

echo "Setting up Python virtual environment..."

# Check if Python is installed
if ! command -v python3.12 &>/dev/null; then
    echo "Error: Python is not installed. Please install Python before running this script."
    exit 1
fi

# Create a virtual environment
python3.12 -m venv venv
if [ $? -ne 0 ]; then
    echo "Error: Unable to create virtual environment."
    exit 1
fi

echo "Virtual environment created successfully."

# Activate the virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Unable to activate virtual environment."
    exit 1
fi

echo "Virtual environment activated successfully."

# Upgrade pip
python -m pip install --upgrade pip

python -m pip install -r requirements.txt

# Execute Python script
timeout -s KILL 20 python source.py

# Deactivate the virtual environment
deactivate
