#!/bin/bash
# Kill any existing Django server processes on port 8000
echo "Checking for stale processes on port 8000..."
PIDS=$(netstat -ano 2>/dev/null | grep " :8000 " | awk '{print $5}' | sort -u)
for PID in $PIDS; do
    if [ -n "$PID" ] && [ "$PID" != "0" ]; then
        echo "Killing PID $PID..."
        cmd //c "taskkill /F /PID $PID" 2>/dev/null
    fi
done

# Activate virtualenv and start server
source venv/Scripts/activate
echo "Starting Django dev server..."
python manage.py runserver
