@echo off
cd /d "%~dp0"
call venv\Scripts\activate
start python manage.py runserver
timeout /t 4 /nobreak
start http://127.0.0.1:8000
pause