# notion_utils.py
from notion_client import Client
from config import NOTION_PAGE_ID, NOTION_TOKEN

notion = Client(auth=NOTION_TOKEN)

def get_page_content(page_id=NOTION_PAGE_ID):
    try:
        # 🧠 Step 1: Fetch page metadata
        page = notion.pages.retrieve(page_id=page_id)
        props = page.get("properties", {})

        prompt_field = props.get("Prompt", {}).get("rich_text", [])
        title_field = props.get("Name", {}).get("title", [])

        prompt_text = (
            "".join([chunk["text"]["content"] for chunk in prompt_field])
            if prompt_field else "No prompt content found."
        )

        title_text = (
            "".join([chunk["text"]["content"] for chunk in title_field])
            if title_field else "Untitled"
        )

        tags = [tag["name"] for tag in props.get("Tags", {}).get("multi_select", [])]
        category = props.get("Category", {}).get("select", {}).get("name", "Uncategorized")

        print(f"📝 Title: {title_text}")
        print(f"🏷️ Category: {category}")
        print(f"🔖 Tags: {tags}")

        # 📦 Step 2: Grab content blocks
        blocks = notion.blocks.children.list(block_id=page_id)
        block_texts = []

        for block in blocks.get("results", []):
            block_type = block.get("type")
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "quote", "callout", "bulleted_list_item", "numbered_list_item"]:
                text_obj = block.get(block_type, {}).get("rich_text", [])
                block_text = "".join([chunk["text"]["content"] for chunk in text_obj])
                if block_text:
                    block_texts.append(block_text)

        full_text = "\n".join(block_texts)

        # 🤝 Merge property prompt + block content (optional)
        merged_prompt = f"{prompt_text}\n\n{full_text}" if full_text else prompt_text

        return merged_prompt

    except Exception as e:
        print("❌ Error reading Notion page content:", e)
        return None

from config import NOTION_PAGE_ID, NOTION_TOKEN
from notion_client import Client

notion = Client(auth=NOTION_TOKEN)

def get_last_edited_time(page_id=NOTION_PAGE_ID):
    try:
        page = notion.pages.retrieve(page_id=page_id)
        return page.get("last_edited_time", "")
    except Exception as e:
        print("❌ Error retrieving last edited time:", e)
        return ""

