@echo off
cd /d "%~dp0"

rem Wenn der Server im Productivity-Modus gestartet wird:
rem start "" venv\Scripts\python.exe manage.py runserver --settings=rechnungssystem.settings_prod

rem Wenn der Server im Developer-Modus gestartet wird:
start "" venv\Scripts\python.exe manage.py runserver

timeout /t 4 /nobreak
start http://127.0.0.1:8000
pause
