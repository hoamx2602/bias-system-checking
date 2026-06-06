@echo off
echo ===================================================
echo Starting Bias Detection System...
echo ===================================================

if not exist "venv\Scripts\activate" (
    echo [ERROR] Virtual environment not found. Please run setup_and_train_windows.bat first.
    pause
    exit /b
)

call venv\Scripts\activate
cd Code
python app.py

pause
