# combined_api.py

from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI
from notion_client import Client as NotionClient
from dotenv import load_dotenv
from datetime import datetime
import time
import os

# ──────────────────────────────────────────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv(override=True)

OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID       = os.getenv("ASSISTANT_ID")
NOTION_TOKEN       = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_PAGE_ID     = os.getenv("NOTION_PAGE_ID")    # (optional, only if you need page‐specific routes)

missing_vars = [
    name for name, val in [
        ("OPENAI_API_KEY", OPENAI_API_KEY),
        ("ASSISTANT_ID", ASSISTANT_ID),
        ("NOTION_TOKEN", NOTION_TOKEN),
        ("NOTION_DATABASE_ID", NOTION_DATABASE_ID),
    ] if not val
]
if missing_vars:
    raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

# ──────────────────────────────────────────────────────────────────────────────
# Initialize clients
# ──────────────────────────────────────────────────────────────────────────────
client = OpenAI(api_key=OPENAI_API_KEY)
notion = NotionClient(auth=NOTION_TOKEN)

# ──────────────────────────────────────────────────────────────────────────────
# Raavaatu “Ask” / Notion‐logging helpers
# ──────────────────────────────────────────────────────────────────────────────
def ask_raavaatu(prompt, category=None, tags=None):
    """
    Send a prompt to the Raavaatu Assistant (via OpenAI threads API),
    wait for the response, log it to Notion, and return the reply text.
    """
    if tags is None:
        tags = []

    print(f"\n🌀 Sending prompt to Raavaatu:\n{prompt}\n")

    try:
        # 1) Create a new Thread
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        # 2) Kick off an assistant run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # 3) Poll until completion
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(1)

        # 4) Fetch message history & extract reply
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value.strip()

        print(f"\n🔮 Raavaatu says:\n{reply}\n")
        save_to_notion(prompt, reply, category, tags)
        return reply

    except Exception as e:
        print("❌ Error talking to Raavaatu:", e)
        return None

def save_to_notion(prompt, reply, category="Uncategorized", tags=None):
    """
    Create a new Notion page in the configured database, with properties
    for Name (title), Prompt, Response, Category, Tags, and Date.
    Then break the reply into ~1800‐char chunks and append as paragraph blocks.
    """
    if tags is None:
        tags = []

    if not isinstance(category, str) or category.strip() == "":
        category = "Uncategorized"

    try:
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": prompt[:50] + ("..." if len(prompt) > 50 else "")
                            }
                        }
                    ]
                },
                "Prompt": {
                    "rich_text": [
                        {"text": {"content": prompt}}
                    ]
                },
                "Response": {
                    "rich_text": [
                        {"text": {"content": reply[:1999]}}
                    ]
                },
                "Category": {"select": {"name": category}},
                "Tags": {
                    "multi_select": [{"name": tag} for tag in tags]
                },
                "Date": {"date": {"start": datetime.utcnow().isoformat()}}
            }
        )

        print(f"✅ Created page: {new_page['url']}")
        page_id = new_page["id"]

        # Break the reply into chunks of ~1800 chars to avoid Notion block limits
        chunks = [reply[i:i+1800] for i in range(0, len(reply), 1800)]
        for chunk in chunks:
            notion.blocks.children.append(
                block_id=page_id,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": chunk}
                        }]
                    }
                }]
            )

        print("✅ Full response saved in Notion (as paragraph blocks).")

    except Exception as e:
        print("❌ Error saving to Notion:", e)

def append_to_page(page_id, content):
    """
    Append a simple paragraph block of `content` to an existing Notion page.
    """
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": content}
                        }]
                    }
                }
            ]
        )
        print("📝 Appended response to existing page.")
    except Exception as e:
        print("❌ Failed to append to page:", e)

def append_toggle_block(page_id, prompt, reply):
    """
    Append a toggle block to a Notion page, where the toggle's
    summary is `prompt` and its child paragraph is `reply`.
    """
    try:
        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [{"type": "text", "text": {"content": prompt}}],
                        "children": [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": reply}
                                    }]
                                }
                            }
                        ]
                    }
                }
            ]
        )
        print("📂 Toggle block with response added.")
    except Exception as e:
        print("❌ Failed to create toggle block:", e)

# ──────────────────────────────────────────────────────────────────────────────
# Flask App + Notion “Memory” Endpoints
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)

def fetch_memory_entries():
    """
    Query the entire Notion database (paginated) for pages,
    extract Name(title), Response(summary), and Tags for each entry,
    and return as a list of dicts.
    """
    try:
        entries = []
        cursor = None

        while True:
            response = notion.databases.query(
                database_id=NOTION_DATABASE_ID,
                start_cursor=cursor
            )
            for result in response.get("results", []):
                props = result.get("properties", {})
                title_prop = props.get("Name", {}).get("title", [])
                summary_prop = props.get("Response", {}).get("rich_text", [])
                tags_prop = props.get("Tags", {}).get("multi_select", [])

                title_text = title_prop[0]["text"]["content"] if title_prop else "Untitled"
                summary_text = summary_prop[0]["text"]["content"] if summary_prop else "No summary available."
                tag_list = [t["name"] for t in tags_prop]

                entries.append({
                    "title": title_text,
                    "summary": summary_text,
                    "tags": tag_list
                })

            cursor = response.get("next_cursor")
            if not cursor:
                break

        return entries

    except Exception as e:
        return [{"title": "Error", "summary": str(e), "tags": []}]

@app.route("/", methods=["GET"])
def get_memory():
    """
    GET / → Return JSON containing all memory entries from Notion.
    """
    memory_entries = fetch_memory_entries()
    return jsonify({"memory": memory_entries})

@app.route("/ask", methods=["POST"])
def ask_route():
    """
    POST /ask with JSON {"prompt": "..."} → Ask Raavaatu, return {"reply": "..."}.
    """
    data = request.get_json() or {}
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    reply = ask_raavaatu(prompt)
    return jsonify({"reply": reply})

def append_text_to_notion_page(page_id, text):
    """
    Helper for writing a paragraph of text to a Notion page by page_id.
    """
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": text}
                        }
                    ]
                }
            }
        ]
    )

@app.route("/write_to_page", methods=["POST"])
def write_to_page():
    """
    POST /write_to_page with JSON {"page_id": "...", "text": "..."} → append paragraph.
    """
    data = request.get_json() or {}
    page_id = data.get("page_id")
    text = data.get("text")
    if not page_id or not text:
        return jsonify({"error": "Missing page_id or text"}), 400

    try:
        append_text_to_notion_page(page_id, text)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/update_block", methods=["POST"])
def update_block():
    """
    POST /update_block with JSON {"block_id": "...", "text": "..."} → replace paragraph text.
    """
    data = request.get_json() or {}
    block_id = data.get("block_id")
    new_text = data.get("text")
    if not block_id or not new_text:
        return jsonify({"error": "Missing block_id or text"}), 400

    try:
        notion.blocks.update(
            block_id=block_id,
            paragraph={
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": new_text}
                    }
                ]
            }
        )
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/delete_block", methods=["POST"])
def delete_block():
    """
    POST /delete_block with JSON {"block_id": "..."} → delete that block.
    """
    data = request.get_json() or {}
    block_id = data.get("block_id")
    if not block_id:
        return jsonify({"error": "Missing block_id"}), 400

    try:
        notion.blocks.delete(block_id=block_id)
        return jsonify({"status": "deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/bulk_edit_blocks", methods=["POST"])
def bulk_edit_blocks():
    """
    POST /bulk_edit_blocks with JSON {"actions": [...]}
    where each action is a dict with keys: op, block_id, parent_id, type, text, checked, children, rich_text.
    Supports create/update/delete in batch.
    """
    data = request.get_json() or {}
    actions = data.get("actions", [])
    if not actions or not isinstance(actions, list):
        return jsonify({"error": "Missing or invalid 'actions' list"}), 400

    results = []
    for action in actions:
        op = action.get("op")
        block_id = action.get("block_id")
        parent_id = action.get("parent_id")
        block_type = action.get("type", "paragraph")
        text = action.get("text", "")
        checked = action.get("checked", None)
        children = action.get("children", None)
        rich_text = action.get("rich_text", None)

        try:
            if op == "create":
                if not parent_id:
                    results.append({"status": "error", "reason": "Missing parent_id for create"})
                    continue

                block_payload = {
                    "object": "block",
                    "type": block_type,
                }
                if rich_text:
                    block_payload[block_type] = {"rich_text": rich_text}
                else:
                    block_payload[block_type] = {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                if checked is not None and block_type == "to_do":
                    block_payload[block_type]["checked"] = checked
                if children:
                    block_payload["has_children"] = True
                    block_payload["children"] = children

                notion.blocks.children.append(
                    block_id=parent_id,
                    children=[block_payload]
                )
                results.append({"op": op, "parent_id": parent_id, "type": block_type, "status": "created"})

            elif op == "update":
                update_data = {}
                if rich_text:
                    update_data[block_type] = {"rich_text": rich_text}
                else:
                    update_data[block_type] = {
                        "rich_text": [{"type": "text", "text": {"content": text}}]
                    }
                if checked is not None and block_type == "to_do":
                    update_data[block_type]["checked"] = checked

                notion.blocks.update(
                    block_id=block_id,
                    **update_data
                )
                results.append({"op": op, "block_id": block_id, "status": "updated"})

            elif op == "delete":
                notion.blocks.delete(block_id=block_id)
                results.append({"op": op, "block_id": block_id, "status": "deleted"})

            else:
                results.append({"op": op, "block_id": block_id, "status": "skipped", "reason": "Unknown op"})

        except Exception as e:
            results.append({"op": op, "block_id": block_id, "status": "error", "reason": str(e)})

    return jsonify(results), 200

@app.route("/list_blocks", methods=["POST"])
def list_blocks():
    """
    POST /list_blocks with JSON {"page_id": "..."} → list immediate child blocks of that page.
    """
    data = request.get_json() or {}
    page_id = data.get("page_id")
    if not page_id:
        return jsonify({"error": "Missing page_id"}), 400

    try:
        blocks = notion.blocks.children.list(block_id=page_id).get("results", [])
        block_list = []
        for block in blocks:
            block_type = block.get("type", "")
            text = ""
            if block_type in ("paragraph", "heading_1", "heading_2", "heading_3"):
                rich_text = block.get(block_type, {}).get("rich_text", [])
                if rich_text and "text" in rich_text[0]:
                    text = rich_text[0]["text"].get("content", "")
            block_list.append({
                "id": block.get("id"),
                "type": block_type,
                "text": text
            })
        return jsonify(block_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────────
# Static / Manifest Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/.well-known/ai-plugin.json')
def serve_manifest():
    return send_from_directory(os.path.join(app.root_path, '.well-known'), 'ai-plugin.json')

@app.route('/schema.json')
def serve_schema():
    return send_from_directory(app.root_path, 'schema.json')

# ──────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
