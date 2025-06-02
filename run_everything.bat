@echo off
title Raavaatu Background Sync

REM Navigate to the working directory
cd /d D:\notion_gpt_sync

REM Start Flask server
start "" python gpt_memory_api.py

REM Start ngrok tunnel
start "" ngrok http 5002

REM Start watchdog
start "" python watchdog.py

REM Optional: sync with OpenAI (on boot or after a delay)
REM start "" python sync_to_openai.py

exit
