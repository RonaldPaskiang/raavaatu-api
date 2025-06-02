from flask import Flask, jsonify, request
from notion_client import Client as NotionClient
from config import NOTION_TOKEN, NOTION_DATABASE_ID
import os

app = Flask(__name__)

# Initialize Notion client
notion = NotionClient(auth=NOTION_TOKEN)

# Helper function to fetch entries from Notion
def fetch_memory_entries():
    try:
        entries = []
        response = notion.databases.query(database_id=NOTION_DATABASE_ID)
        for result in response.get("results", []):
            props = result.get("properties", {})
            title = props.get("Name", {}).get("title", [])
            summary = props.get("Response", {}).get("rich_text", [])
            tags = props.get("Tags", {}).get("multi_select", [])

            title_text = title[0]["text"]["content"] if title else "Untitled"
            summary_text = summary[0]["text"]["content"] if summary else "No summary available."
            tag_list = [tag["name"] for tag in tags]

            entries.append({
                "title": title_text,
                "summary": summary_text,
                "tags": tag_list
            })
        return entries
    except Exception as e:
        return [{"title": "Error", "summary": str(e), "tags": []}]

@app.route("/", methods=["GET"])
def get_memory():
    memory_entries = fetch_memory_entries()
    return jsonify({"memory": memory_entries})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
