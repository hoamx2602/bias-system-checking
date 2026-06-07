#!/usr/bin/env bash
set -e

echo "==================================================="
echo "Starting Bias Detection System..."
echo "==================================================="

if ! python -c "import flask" &>/dev/null; then
    echo "[ERROR] Python dependencies not found. Please run setup_and_train.sh first."
    read -rp "Press Enter to exit..."
    exit 1
fi

cd Code
python app.py

read -rp "Press Enter to exit..."
