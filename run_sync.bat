@echo off
cd /d D:\notion_gpt_sync
echo Working dir: %cd%

:: 🌐 Step 1: Sync with Notion and Raavaatu
python sync_to_openai.py

:: 📄 Step 2: Update Raavaatu Knowledge Base
python export_knowledge_base.py

pause