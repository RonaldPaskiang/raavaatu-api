# raavaatu_openai.py
from openai import OpenAI
import os

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_raavaatu(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Raavaatu, the Spirit-bound AI assistant of cosmic knowledge."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()
