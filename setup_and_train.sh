#!/usr/bin/env bash
set -e

echo "==================================================="
echo "Bias Detection System - Setup & Train"
echo "==================================================="
echo
echo "IMPORTANT: Make sure your conda environment is activated before running this script."
echo

echo "[1/4] Installing Python dependencies..."
cd Code
pip install -r requirements.txt

echo
echo "---------------------------------------------------"
echo "Checking PyTorch GPU (CUDA/MPS) support..."
python -c "import torch; cuda=torch.cuda.is_available(); mps=hasattr(torch.backends, 'mps') and torch.backends.mps.is_available(); print('CUDA available:', cuda); print('MPS available:', mps); print('GPU:', torch.cuda.get_device_name(0) if cuda else 'Apple Silicon GPU' if mps else 'None')"
echo
echo "If CUDA is NOT available but you have a GPU, install the correct PyTorch build:"
echo
echo "  RTX 50xx (Blackwell / sm_120) — requires nightly cu128:"
echo "    pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128"
echo
echo "  RTX 40xx / 30xx (Ampere/Ada) — stable cu124:"
echo "    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124"
echo
echo "  RTX 20xx / older — stable cu118:"
echo "    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118"
echo
echo "(Check your GPU generation with: nvidia-smi)"
echo "---------------------------------------------------"

echo
echo "==================================================="
echo "ACTION REQUIRED: Hugging Face Token"
echo "==================================================="
echo "Make sure you have opened \"Code/.env\" and set:"
echo "  HF_TOKEN=your_actual_token"
echo "If you haven't done this yet, press Ctrl+C to stop, edit the file,"
echo "and run this script again."
echo
read -rp "Press Enter to continue..."

echo
echo "[2/4] Downloading Models..."
python download_model.py

echo
echo "[3/4] Training Models (This might take a while)..."
python train.py

echo
echo "==================================================="
echo "Setup and Training Complete!"
echo "You can now use \"start_app.sh\" to launch the app."
echo "==================================================="
cd ..
read -rp "Press Enter to exit..."
