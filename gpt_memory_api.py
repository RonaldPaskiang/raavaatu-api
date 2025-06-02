from flask import Flask, jsonify, request
from flask import Flask, send_from_directory
from notion_client import Client as NotionClient
import os
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]


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

def append_text_to_notion_page(page_id, text):
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
                            "text": {
                                "content": text
                            }
                        }
                    ]
                }
            }
        ]
    )

@app.route("/write_to_page", methods=["POST"])
def write_to_page():
    data = request.get_json()
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
    data = request.get_json()
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
    data = request.get_json()
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
    data = request.get_json()
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
        rich_text = action.get("rich_text", None)  # Use if you want to pass full rich text objects

        try:
            # 1. CREATE NEW BLOCK
            if op == "create":
                if not parent_id:
                    results.append({"status": "error", "reason": "Missing parent_id for create"})
                    continue
                block_payload = {
                    "object": "block",
                    "type": block_type,
                }
                # Fill in content type-specific
                if rich_text:
                    block_payload[block_type] = {"rich_text": rich_text}
                else:
                    block_payload[block_type] = {"rich_text": [{"type": "text", "text": {"content": text}}]}
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
            # 2. UPDATE EXISTING BLOCK
            elif op == "update":
                update_data = {}
                if rich_text:
                    update_data[block_type] = {"rich_text": rich_text}
                else:
                    update_data[block_type] = {"rich_text": [{"type": "text", "text": {"content": text}}]}
                if checked is not None and block_type == "to_do":
                    update_data[block_type]["checked"] = checked
                notion.blocks.update(
                    block_id=block_id,
                    **update_data
                )
                results.append({"op": op, "block_id": block_id, "status": "updated"})
            # 3. DELETE BLOCK
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
    data = request.get_json()
    page_id = data.get("page_id")
    if not page_id:
        return jsonify({"error": "Missing page_id"}), 400
    try:
        blocks = notion.blocks.children.list(block_id=page_id)["results"]
        block_list = []
        for block in blocks:
            block_type = block.get("type", "")
            text = ""
            # Try to get text for paragraphs and headings
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port)

# Serve plugin manifest
@app.route('/.well-known/ai-plugin.json')
def serve_manifest():
    return send_from_directory(os.path.join(app.root_path, '.well-known'), 'ai-plugin.json')
