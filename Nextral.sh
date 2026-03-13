#!/bin/bash

# Nextral Terminal Linux Launcher
# Requirements: python3, pip

echo "--- NEXTRAL TERMINAL LINUX LAUNCHER ---"

# Check for python3
if ! command -v python3 &> /dev/null
then
    echo "ERROR: python3 not found. Please install it."
    exit 1
fi

# Run the launcher (auto-installs dependencies)
python3 launcher.py
