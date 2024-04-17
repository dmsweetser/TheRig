source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Unable to activate virtual environment."
    exit 1
fi

echo "Virtual environment activated successfully."

# Execute Python script
python -c rig_python39_linux.py

# Deactivate the virtual environment
deactivate
