@echo off
echo Checking for stale processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 "') do (
    if not "%%a"=="0" (
        echo Killing PID %%a...
        taskkill /F /PID %%a >nul 2>&1
    )
)
echo Starting Django dev server...
call venv\Scripts\activate.bat
python manage.py runserver
