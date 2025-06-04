from notion_client import Client
import os
import time

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_PAGE_ID = os.environ["NOTION_PAGE_ID"]

notion = Client(auth=NOTION_TOKEN)

def get_page_blocks(page_id):
    blocks = []
    cursor = None

    while True:
        response = notion.blocks.children.list(block_id=page_id, start_cursor=cursor)
        blocks.extend(response.get("results"))
        cursor = response.get("next_cursor")
        if not cursor:
            break

    return blocks

def extract_text_from_block(block):
    block_type = block["type"]
    if block_type in ("paragraph", "heading_1", "heading_2", "heading_3", "quote", "bulleted_list_item"):
        text_array = block[block_type]["rich_text"]
        return "".join([t["plain_text"] for t in text_array])
    elif block_type == "code":
        return block["code"]["rich_text"][0]["plain_text"]
    else:
        return f"[{block_type} block — no printable text]"

def main():
    print("🧾 Printable Page Content:\n")
    blocks = get_page_blocks(NOTION_PAGE_ID)

    for block in blocks:
        block_type = block["type"]
        content = extract_text_from_block(block)
        print(f"{block_type.capitalize()}: {content.strip()}\n")
        time.sleep(0.05)  # tiny pause for readability

if __name__ == "__main__":
    main()
