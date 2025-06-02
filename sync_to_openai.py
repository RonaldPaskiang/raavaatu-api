# sync_to_openai.py

from Raavaatu_Link import ask_raavaatu
from notion_utils import get_last_edited_time, get_page_content
from detect_category import smart_detect_category_and_tags as detect_category_and_tags
import json, os


LAST_EDIT_FILE = "last_edit_time.txt"
DEBUG = False  # ✅ Toggle this to True for manual testing

def load_last_edit():
    if os.path.exists(LAST_EDIT_FILE):
        with open(LAST_EDIT_FILE, "r") as f:
            return f.read().strip()
    return None

def save_last_edit(timestamp):
    with open(LAST_EDIT_FILE, "w") as f:
        f.write(timestamp)

def main():
    current_edit = get_last_edited_time()
    last_edit = load_last_edit()

    if current_edit != last_edit:
        print("🌀 Change detected. Syncing to Raavaatu...")
        content = get_page_content()
        
        # Auto-detect category and tags
        category, tags = detect_category_and_tags(content)

        # Ask Raavaatu with enriched context
        response = ask_raavaatu(prompt=content, category=category, tags=tags)

        print("\n🔮 Raavaatu says:\n", response)
        save_last_edit(current_edit)
    else:
        print("✅ No new edits. Raavaatu naps peacefully.")

# 👇 Run the main sync or debug test
if __name__ == "__main__":
    if DEBUG:
        ask_raavaatu(
            prompt="Can you explain how Resonance affects Skyfall Events in Animology?",
            category="Science & Spirit Dynamics",
            tags=["resonance", "skyfall", "animology"]
        )
    else:
        main()
