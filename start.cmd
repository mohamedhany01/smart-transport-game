@echo off
setlocal

REM -----------------------------
REM 1. Create venv if not exists
REM -----------------------------
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM -----------------------------
REM 2. Activate the venv
REM -----------------------------
call .venv\Scripts\activate

REM -----------------------------
REM 3. Install dependencies
REM -----------------------------
if exist requirements.txt (
    echo Installing requirements...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found!
)

REM -----------------------------
REM 4. Change directory into src
REM -----------------------------
cd src

REM -----------------------------
REM 5. Run main.py
REM -----------------------------
echo Running main.py...
python main.py

endlocal
