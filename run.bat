@echo off
setlocal

echo Checking for Python 3.12...

REM Check if python exists and is version 3.12

py -0p | findstr "3.12" > nul
if %errorlevel% neq 0 (
    echo Python 3.12 not found. Installing via winget...
    winget install Python.Python.3.12 -h
    echo Waiting for Python installation to complete...
)

REM Ensure python3.12 is on PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found on PATH even after install.
    echo You may need to restart your terminal.
    pause
    exit /b
)

echo Python 3.12 is installed.

REM Check for venv folder
if not exist ".\venv\" (
    echo Creating Python 3.12 virtual environment...
    py -3.12 -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate
echo Checking for pygame...
python -c "import pygame" 2>nul
if %errorlevel% neq 0 (
    echo pygame not found. Installing pygame...
    pip install pygame
)

echo Running hex_rings_game.py...
python FamilyGame.py

endlocal
