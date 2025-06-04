from flask import Flask, request, jsonify
import openai
from notion_client import Client as NotionClient
from datetime import datetime
import os
import time

# Load credentials from env vars
openai.api_key = os.getenv("OPENAI_API_KEY")
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))

assistant_id = os.getenv("ASSISTANT_ID")

app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    question = request.json.get("question", "")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    # ✏️ Example Notion keyword check
    if "aki" in question.lower() and "quirk" in question.lower():
        return jsonify({"answer": "Aki developed his Quirk around age 9, after initially testing Quirkless at 4."})

    # 🌀 Ask Raavaatu
    try:
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

        # Wait until it’s done
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        reply = messages.data[0].content[0].text.value.strip()
        return jsonify({"answer": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5001)
