# 🚀 Running the BIAS System on Google Colab (GPU T4 x1)

This guidebook explains how to run this complete project on **Google Colab** using their free **T4 GPU** runtime, mounting Google Drive, and opening the Flask web application in your local browser using a secure public HTTPS tunnel.

---

## 📅 Pre-flight Checks (One-time)
1. **Accept Gemma 3 License**: 
   Ensure you are logged into your Hugging Face account and have accepted the license terms for [google/gemma-3-1b-it](https://huggingface.co/google/gemma-3-1b-it).
2. **Hugging Face Token**:
   Ensure a valid read-only Hugging Face Token is present in your local `Code/config.ini` file. Your current `config.ini` already contains a valid token:
   ```ini
   [huggingface]
   token = YOUR_HUGGINGFACE_TOKEN
   ```
3. **Upload to Google Drive**:
   Upload the entire `BIAS` directory (containing `Code/`, `dataset/`, `COLAB_INSTRUCTIONS.md`, etc.) to your Google Drive root folder. The folder name on Drive should be `BIAS` (i.e. `/content/drive/MyDrive/BIAS`).

---

## 📓 Cell-by-Cell Google Colab Walkthrough

Open a new Jupyter Notebook in Google Colab (https://colab.research.google.com), change the runtime type to **T4 GPU** (`Runtime` ➔ `Change runtime type` ➔ `T4 GPU`), and paste the following cells in order:

### 📥 Cell 1: Mount Google Drive
This connects Colab to your Google Drive and allows reading the project files.
```python
from google.colab import drive
import os

print("Mounting Google Drive...")
drive.mount('/content/drive')

# Verify the project exists
project_path = "/content/drive/MyDrive/BIAS"
if os.path.exists(project_path):
    print("✅ Found project directory on Google Drive!")
else:
    print("❌ ERROR: Could not find 'BIAS' folder at the root of your Google Drive.")
    print("Please upload the project directory as 'BIAS' at your Drive's root.")
```

### ⚙️ Cell 2: Copy Files to Fast Local Storage & Install Dependencies
Google Drive file operations can be slow for AI models. We copy the project directory to Colab's local high-speed SSD (`/content/BIAS/`) and install all required python libraries.
```python
import shutil

print("Copying project to high-speed local Colab storage...")
local_path = "/content/BIAS"
if os.path.exists(local_path):
    shutil.rmtree(local_path)
shutil.copytree(project_path, local_path)

%cd /content/BIAS/Code

print("\nInstalling requirements (PyTorch, Transformers, SentenceTransformers)...")
!pip install -q -r requirements.txt
!pip install -q localtunnel  # For web server tunneling
print("✅ Environment setup and package installation complete!")
```

### 🧠 Cell 3: Pre-download AI Models to Fast Cache
This downloads both the **Sentence Transformer** (`all-mpnet-base-v2`) and the **Gemma 3 1B LLM** to Colab's local directory. Running this pre-downloads everything in about 1-2 minutes over Google's high-speed data-center connection.
```python
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
!pip install -q hf-transfer  # Install ultra-fast HF downloader

print("Running snapshot download for model cache...")
!python download_model.py
print("✅ Models successfully pre-cached on Colab GPU local SSD!")
```

### 📊 Cell 4: Preprocess Data & Rebuild Vector Store (Optional but Recommended)
Builds the scenario embeddings and saves the `bias_vector_store.pkl` along with the NetworkX knowledge graph.
```python
print("Rebuilding vector store and knowledge graph...")
# Automatically select yes to rebuild if prompted
!echo "y" | python preprocess_data.py
print("✅ Knowledge assets created successfully!")
```

### 🏆 Cell 5: Fine-Tune the Multi-Task Classifier (Takes ~3-5 minutes on GPU!)
Trains the high-accuracy DistilBERT classifier on the 30,000+ dataset dialogues to predict bias intensity and types.
```python
print("Fine-tuning the DistilBERT bias classifier on GPU T4...")
# Tweak training configs in config.py if you want to run faster or more epochs
!python train.py
print("✅ Model fine-tuning complete and saved!")
```

### 🌐 Cell 6: Launch and Tunnel the Flask Web App
We start the web application in the background and use **Localtunnel** to expose Flask's port `5001` to a secure public URL. Click on the generated link to open the beautiful glassmorphism BIAS interface in your web browser!
```python
import subprocess
import time

print("Starting Flask Web Application in the background...")
# Run Flask app
flask_process = subprocess.Popen(["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Wait a few seconds for Flask to initialize
time.sleep(5)

# Print IP to unlock localtunnel access page if prompted
import urllib.request
external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
print(f"🔑 Your localtunnel bypass password is: {external_ip}")
print("Use the password above to bypass the localtunnel security warning if it prompts you.\n")

print("Launching Localtunnel...")
# Expose port 5001
!npx localtunnel --port 5001
```

---

## 🛠️ Troubleshooting on Colab
* **Out of Memory (OOM)**:
  If Colab runs out of GPU memory, modify `Code/config.py` and reduce training batch sizes to `4` or `2`:
  ```python
  TRAIN_BATCH_SIZE = 4
  EVAL_BATCH_SIZE = 4
  ```
* **Localtunnel Connection Issues**:
  If Localtunnel fails to retrieve a link, stop the cell and run the alternative tunneling block:
  ```bash
  !pip install -q pyngrok
  # Sign up for a free Ngrok token at https://dashboard.ngrok.com
  !ngrok config add-authtoken <YOUR_NGROK_AUTH_TOKEN>
  from pyngrok import ngrok
  public_url = ngrok.connect(5001)
  print("Ngrok Tunnel URL:", public_url)
  ```
