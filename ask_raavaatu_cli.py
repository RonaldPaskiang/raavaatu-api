# ask_raavaatu_cli.py

import sys
from Raavaatu_Link import ask_raavaatu  # This uses your existing Raavaatu code

# Grab whatever you typed when running the file
if __name__ == "__main__":
    user_prompt = " ".join(sys.argv[1:])  # turns your words into a full sentence
    response = ask_raavaatu(user_prompt)
    print(response)
