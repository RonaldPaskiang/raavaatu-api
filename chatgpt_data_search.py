import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from collections import defaultdict
import re

# Global variables for shared state
data = None
file_path = None
results = {}
convo_keys = []

def highlight_keyword(text, keyword):
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(lambda m: f"[{m.group(0).upper()}]", text)

def load_json_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f), file_path

def parse_conversations(data, keyword, speaker="All", start_date=None, end_date=None):
    keyword = keyword.lower()
    results_by_convo = defaultdict(list)

    for convo in data:
        convo_id = convo.get("id", "unknown_id")
        mapping = convo.get("mapping", {})
        if not isinstance(mapping, dict):
            continue

        for msg_obj in mapping.values():
            message = msg_obj.get("message")
            if not message or not isinstance(message, dict):
                continue  # skip bad or missing messages

            author = message.get("author", {}).get("role", "unknown")
            timestamp = message.get("create_time")
            parts = message.get("content", {}).get("parts", [])

            if not parts or not isinstance(parts[0], str):
                continue

            content = parts[0]
            if keyword not in content.lower():
                continue

            # 🧍‍♂️ Speaker filter
            if speaker != "All" and author.lower() != speaker.lower():
                continue

            # 🛡️ Safe timestamp handling
            dt_obj = None
            try:
                if isinstance(timestamp, (int, float)):
                    dt_obj = datetime.fromtimestamp(timestamp)
            except (OSError, OverflowError, ValueError):
                print(f"⚠️ Skipping invalid timestamp: {timestamp}")
                dt_obj = None

            # 🧭 Filter by date if applicable
            if start_date and dt_obj and dt_obj < start_date:
                continue
            if end_date and dt_obj and dt_obj > end_date:
                continue

            results_by_convo[convo_id].append({
                "timestamp": dt_obj.strftime("%Y-%m-%d %H:%M:%S") if dt_obj else "Unknown",
                "author": author.title(),
                "text": content
            })

    return results_by_convo

def export_to_file(convo_id, messages, keyword):
    filename = f"conversation_{convo_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Conversation ID: {convo_id}\n\n")
        for msg in messages:
            f.write(f"### {msg['author']} — {msg['timestamp']}\n")
            text = msg["text"].replace(keyword, f"**{keyword}**")
            f.write(f"{text}\n\n")
    messagebox.showinfo("Export Complete", f"Exported to {filename}")

def on_convo_select(event):
    selected = convo_listbox.curselection()
    if not selected:
        return
    convo_id = convo_keys[selected[0]]
    messages = results[convo_id]

    display_text.delete("1.0", tk.END)
    for msg in messages:
        line = f"[{msg['timestamp']}] {msg['author']}: {highlight_keyword(msg['text'], keyword_entry.get())}\n\n"
        display_text.insert(tk.END, line)

    export_button.config(state=tk.NORMAL, command=lambda: export_to_file(convo_id, messages, keyword_entry.get()))

def load_and_enable():
    global data, file_path
    result = load_json_file()
    if result:
        data, file_path = result
        load_button.config(text="✅ Loaded JSON")

def run_search():
    global results, convo_keys, data
    if data is None:
        messagebox.showwarning("No File", "Please load a JSON file before searching.")
        return

    keyword = keyword_entry.get().strip()
    if not keyword:
        messagebox.showwarning("Input Error", "Please enter a keyword.")
        return

    start = start_entry.get().strip()
    end = end_entry.get().strip()
    try:
        start_date = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_date = datetime.strptime(end, "%Y-%m-%d") if end else None
    except ValueError:
        messagebox.showerror("Date Error", "Dates must be in YYYY-MM-DD format.")
        return

    speaker = speaker_var.get()
    results = parse_conversations(data, keyword, speaker, start_date, end_date)
    convo_keys = list(results.keys())

    convo_listbox.delete(0, tk.END)
    for idx, cid in enumerate(convo_keys):
        preview = results[cid][0]["text"][:80].replace("\n", " ")
        convo_listbox.insert(tk.END, f"{idx+1}. {preview}...")

    display_text.delete("1.0", tk.END)
    export_button.config(state=tk.DISABLED)

# ----- GUI Setup -----
root = tk.Tk()
root.title("ChatGPT Conversation Explorer")
root.geometry("1050x700")

top_frame = tk.Frame(root)
top_frame.pack(pady=10)

load_button = tk.Button(top_frame, text="📂 Load JSON File", command=lambda: load_and_enable())
load_button.grid(row=0, column=0, padx=5)

keyword_label = tk.Label(top_frame, text="Keyword:")
keyword_label.grid(row=0, column=1)
keyword_entry = tk.Entry(top_frame, width=20)
keyword_entry.grid(row=0, column=2, padx=5)

speaker_label = tk.Label(top_frame, text="Speaker:")
speaker_label.grid(row=0, column=3)
speaker_var = tk.StringVar(value="All")
speaker_menu = tk.OptionMenu(top_frame, speaker_var, "All", "User", "Assistant")
speaker_menu.grid(row=0, column=4, padx=5)

start_label = tk.Label(top_frame, text="Start Date (YYYY-MM-DD):")
start_label.grid(row=0, column=5)
start_entry = tk.Entry(top_frame, width=15)
start_entry.grid(row=0, column=6, padx=5)

end_label = tk.Label(top_frame, text="End Date (YYYY-MM-DD):")
end_label.grid(row=0, column=7)
end_entry = tk.Entry(top_frame, width=15)
end_entry.grid(row=0, column=8, padx=5)

search_button = tk.Button(top_frame, text="🔍 Search", command=run_search)
search_button.grid(row=0, column=9, padx=10)

mid_frame = tk.Frame(root)
mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

convo_listbox = tk.Listbox(mid_frame, width=50, height=25)
convo_listbox.pack(side=tk.LEFT, fill=tk.Y)
convo_listbox.bind('<<ListboxSelect>>', on_convo_select)

scrollbar = tk.Scrollbar(mid_frame, orient="vertical", command=convo_listbox.yview)
scrollbar.pack(side=tk.LEFT, fill=tk.Y)
convo_listbox.config(yscrollcommand=scrollbar.set)

display_text = tk.Text(mid_frame, wrap="word")
display_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=10)
export_button = tk.Button(bottom_frame, text="💾 Export This Conversation", state=tk.DISABLED)
export_button.pack()

root.mainloop()
