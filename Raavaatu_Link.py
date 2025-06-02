from openai import OpenAI
from notion_client import Client as NotionClient
from datetime import datetime
from config import OPENAI_API_KEY, ASSISTANT_ID, NOTION_TOKEN, NOTION_DATABASE_ID

# ✅ Initialize OpenAI + Notion clients
client = OpenAI(api_key=OPENAI_API_KEY)
notion = NotionClient(auth=NOTION_TOKEN)

# 🎤 Ask Raavaatu, get wisdom
def ask_raavaatu(prompt, category=None, tags=None):
    if tags is None:
        tags = []

    print(f"\n🌀 Sending prompt to Raavaatu:\n{prompt}\n")

    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=ASSISTANT_ID
        )

        # Wait for completion (blocking call)
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value.strip()

        print(f"\n🔮 Raavaatu says:\n{reply}\n")
        save_to_notion(prompt, reply, category, tags)
        return reply

    except Exception as e:
        print("❌ Error talking to Raavaatu:", e)
        return None

# 🗃️ Log to Notion as a new page
def save_to_notion(prompt, reply, category="Uncategorized", tags=None):
    if tags is None:
        tags = []

    if not isinstance(category, str) or category.strip() == "":
        category = "Uncategorized"

    try:
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": prompt[:50] + ("..." if len(prompt) > 50 else "")}}]},
                "Prompt": {"rich_text": [{"text": {"content": prompt}}]},
                "Response": {"rich_text": [{"text": {"content": reply[:1999]}}]},
                "Category": {"select": {"name": category}},
                "Tags": {"multi_select": [{"name": tag} for tag in tags]},
                "Date": {"date": {"start": datetime.utcnow().isoformat()}}
            }
        )

        print(f"✅ Created page: {new_page['url']}")
        page_id = new_page["id"]

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

# 📎 Append to existing page (simple text)
def append_to_page(page_id, content):
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

# 📂 Append as toggle block
def append_toggle_block(page_id, prompt, reply):
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
