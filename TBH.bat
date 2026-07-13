@echo off
title tbh_bot
cd /d "%~dp0"
python tbh_panel.py
if errorlevel 1 pause
