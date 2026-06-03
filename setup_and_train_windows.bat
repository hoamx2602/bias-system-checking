@echo off
echo ===================================================
echo Bias Detection System - Windows Setup ^& Train
echo ===================================================
echo.

echo [1/5] Checking Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python (check "Add to PATH" during installation^).
    pause
    exit /b
)

echo.
echo [2/5] Creating Virtual Environment (venv)...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo [3/5] Activating venv and Installing Dependencies...
call venv\Scripts\activate
cd Code
pip install -r requirements.txt
:: Install any extra packages used in colab
pip install pyngrok accelerate openpyxl pandas

echo.
echo ===================================================
echo ACTION REQUIRED: Hugging Face Token
echo ===================================================
echo Make sure you have opened "Code\config.ini" and replaced
echo "YOUR_HUGGINGFACE_TOKEN" with your actual Hugging Face token.
echo If you haven't done this yet, press Ctrl+C to stop, edit the file, and run this script again.
echo.
pause

echo.
echo [4/5] Downloading Models...
python download_model.py

echo.
echo [5/5] Training Models (This might take a while)...
python train.py

echo.
echo ===================================================
echo Setup and Training Complete!
echo You can now use "start_app_windows.bat" to launch the app.
echo ===================================================
cd ..
pause
