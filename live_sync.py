import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

WATCH_DIR = os.path.abspath("D:\\notion_gpt_sync")
TARGET_SCRIPT = os.path.join(WATCH_DIR, "sync_to_openai.py")

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        print(f"\n📂 Change detected in: {event.src_path}")
        print("🔁 Running sync_to_openai.py...\n")
        subprocess.run(["python", TARGET_SCRIPT], check=False)

if __name__ == "__main__":
    print(f"📡 Watching for changes in: {WATCH_DIR}")
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

