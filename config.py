from dotenv import load_dotenv
import os
print("Working dir:", os.getcwd())
print(".env exists?", os.path.exists(".env"))

# Load .env file
load_dotenv()

# Grab secrets from environment
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
CUSTOM_GPT_NAME = os.getenv("CUSTOM_GPT_NAME")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if __name__ == "__main__":
    print("🔐 NOTION_TOKEN:", NOTION_TOKEN[:10] + "...")
    print("🔐 OPENAI_API_KEY:", OPENAI_API_KEY[:10] + "...")
    print("📄 PAGE ID:", NOTION_PAGE_ID)
    print("🤖 Custom GPT:", CUSTOM_GPT_NAME)
    print("🧑‍💼 Assistant ID:", ASSISTANT_ID)