@echo off
title Smart Lead Scraper GUI
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo An error occurred while running the application.
    pause
)
