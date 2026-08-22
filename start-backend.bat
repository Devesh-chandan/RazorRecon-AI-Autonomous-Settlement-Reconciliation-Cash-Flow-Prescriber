@echo off
echo Starting RazorRecon Backend...
cd /d "%~dp0backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
