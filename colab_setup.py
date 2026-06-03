"""
BIAS Detection System - Google Colab Setup & Launch Tool
This script automates environment configuration, Hugging Face validation,
and secure port forwarding (via localtunnel or ngrok) for one-click deployment on Colab.
"""

import os
import sys
import subprocess
import time
import urllib.request
import configparser

def print_banner():
    banner = """
======================================================================
               BIAS DETECTION SYSTEM - COLAB SETUP ENGINE             
======================================================================
    This interactive launcher will:
    1. Confirm installation of critical ML & server dependencies.
    2. Verify and configure your Hugging Face Authentication Token.
    3. Expose port 5001 to the internet using localtunnel or ngrok.
    4. Launch the Flask application in production/dev mode.
======================================================================
"""
    print(banner)

def run_command(command, description):
    print(f"\n[INFO] {description}...")
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Stream output in real time
        for line in process.stdout:
            print(f"  {line.strip()}")
        process.wait()
        if process.returncode != 0:
            print(f"[WARNING] Task completed with code {process.returncode}")
        else:
            print(f"[SUCCESS] {description} completed.")
    except Exception as e:
        print(f"[ERROR] Failed to run '{command}': {e}")

def check_dependencies():
    print("[1/5] Checking environment dependencies...")
    
    # In Colab, we should make sure transformers, sentencepiece, accelerate, pyngrok are present.
    packages = [
        "transformers>=4.40.0",
        "sentence-transformers",
        "accelerate",
        "pyngrok",
        "scikit-learn",
        "networkx",
        "pandas",
        "openpyxl"
    ]
    
    # If running inside Google Colab
    try:
        import google.colab
        is_colab = True
        print("  Running in Google Colab environment.")
    except ImportError:
        is_colab = False
        print("  Running in standard local environment.")
    
    if is_colab:
        print("  Installing missing dependencies for Colab...")
        cmd = f"pip install -q " + " ".join(packages)
        run_command(cmd, "Installing required pip packages")
    else:
        print("  Skipping automatic library installs on local runtime. (Use requirements.txt to configure locally).")

def configure_huggingface():
    print("\n[2/5] Checking Hugging Face token authentication...")
    config_file = 'config.ini'
    parser = configparser.ConfigParser()
    
    existing_token = None
    if os.path.exists(config_file):
        parser.read(config_file)
        existing_token = parser.get('huggingface', 'token', fallback=None)
        if existing_token and "YOUR_HUGGING_FACE_TOKEN_HERE" in existing_token:
            existing_token = None
            
    if existing_token:
        print("  -> Found active Hugging Face token in config.ini.")
        use_existing = input("  Would you like to keep using this existing token? (y/n) [y]: ").strip().lower() or 'y'
        if use_existing == 'y':
            return
            
    # Prompt for Hugging Face Token
    print("\n  ==================================================================")
    print("  HUGGING FACE TOKEN REQUIRED:")
    print("  To load and run google/gemma-3-1b-it, you must provide a Hugging Face")
    print("  User Access Token with read/write permissions.")
    print("  Create a token here: https://huggingface.co/settings/tokens")
    print("  ==================================================================")
    
    token = ""
    while not token:
        token = input("  Please enter your Hugging Face Token: ").strip()
        if not token:
            print("  [ERROR] Token cannot be empty. Please enter a valid token.")
            
    # Write to config.ini
    if not parser.has_section('huggingface'):
        parser.add_section('huggingface')
    parser.set('huggingface', 'token', token)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        parser.write(f)
        
    print("  [SUCCESS] Hugging Face token saved to config.ini.")

def check_models_download():
    print("\n[3/5] Checking AI models downloads...")
    # Run the model pre-downloader script to pull Google Gemma and DistilBERT models locally
    if os.path.exists("download_model.py"):
        run_command("python download_model.py", "Downloading/Verifying local model caches")
    else:
        print("  -> download_model.py not found in current directory. Skipping pre-caching stage.")

def get_external_ip():
    try:
        ip = urllib.request.urlopen('https://ipv4.icanhazip.com', timeout=5).read().decode('utf8').strip()
        return ip
    except Exception:
        return "Unknown"

def launch_port_tunneling(tunnel_pref, ngrok_token=None):
    print(f"\n[4/5] Activating port forwarding (Selected: {tunnel_pref.upper()})...")
    
    if tunnel_pref == 'localtunnel':
        external_ip = get_external_ip()
        print("\n  ==================================================================")
        print("  LOCALTUNNEL IS STARTING:")
        print(f"  Your Google Colab runtime external IP is: {external_ip}")
        print("  IMPORTANT: Click the tunnel link below when it loads and enter this IP")
        print("  value in the 'Endpoint IP' box to bypass the localtunnel warning screen.")
        print("  ==================================================================")
        
        # Install localtunnel globally using npm if it's not present
        try:
            print("  Confirming localtunnel npm package is active...")
            # Run localtunnel in the background
            cmd = "npx localtunnel --port 5001"
            tunnel_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            # Print the localtunnel output in a separate background thread or poll it
            time.sleep(4)
            print("\n  --- Localtunnel Tunnel Links ---")
            for _ in range(5):
                line = tunnel_process.stdout.readline()
                if "url is" in line.lower() or "https://" in line:
                    print(f"  [TUNNEL ACTIVE] -> {line.strip()}")
                    break
                time.sleep(1)
            print("  --------------------------------\n")
        except Exception as e:
            print(f"  [ERROR] Failed to start localtunnel: {e}")
            print("  Switching to ngrok fallback...")
            tunnel_pref = 'ngrok'
            
    if tunnel_pref == 'ngrok':
        if not ngrok_token:
            print("\n  ==================================================================")
            print("  NGROK AUTHENTICATION TOKEN REQUIRED:")
            print("  To use the ngrok tunnel fallback, please enter your ngrok Authtoken.")
            print("  Get a free token here: https://dashboard.ngrok.com/get-started/your-authtoken")
            print("  ==================================================================")
            while not ngrok_token:
                ngrok_token = input("  Please enter your ngrok Authtoken: ").strip()
                if not ngrok_token:
                    print("  [ERROR] Token cannot be empty.")
        
        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(ngrok_token)
            public_url = ngrok.connect(5001).public_url
            print("\n  ==================================================================")
            print(f"  [NGROK TUNNEL ACTIVE] -> {public_url}")
            print("  Click this link to access your BIAS Detection Web Application.")
            print("  ==================================================================\n")
        except Exception as e:
            print(f"  [ERROR] Failed to launch ngrok tunnel: {e}")
            print("  Please make sure your token is valid.")

def start_server():
    print("\n[5/5] Launching Flask Server on port 5001...")
    if not os.path.exists("app.py"):
        print("[ERROR] app.py not found in the current directory! Cannot start server.")
        sys.exit(1)
        
    print("  Executing app.py... Models will be loaded into memory.")
    print("  Server initialization will take 1-2 minutes on Colab GPU T4. Keep this cell active.")
    print("======================================================================\n")
    
    # Run server
    subprocess.run("python app.py", shell=True)

def main():
    print_banner()
    
    # Confirm working directory contains the files
    # If colab_setup.py is run from the workspace root directory, check if Code folder exists
    # and change cwd to Code folder so relative imports and file loads execute perfectly
    if os.path.isdir("Code"):
        print("Moving execution directory into 'Code' folder...")
        os.chdir("Code")
        
    check_dependencies()
    configure_huggingface()
    check_models_download()
    
    # Expose options for Tunnel Preference
    print("\n======================================================================")
    print("PORT FORWARDING PREFERENCE:")
    print("1. localtunnel (Recommended - No account required, immediate tunnel)")
    print("2. ngrok (Requires a free ngrok account authtoken)")
    print("======================================================================")
    
    choice = input("Enter choice (1 or 2) [1]: ").strip() or "1"
    
    if choice == "2":
        launch_port_tunneling('ngrok')
    else:
        launch_port_tunneling('localtunnel')
        
    start_server()

if __name__ == "__main__":
    main()
