@echo off

echo Creating virtual environment...
python -m venv .venv

if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing requirements...
pip install -r requirements.txt

if errorlevel 1 (
    echo Failed to install requirements.
    exit /b 1
)

echo Done.
cmd /k
