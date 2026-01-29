#!/bin/bash

# Change to the project directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Start the server
python run.py "$@"
