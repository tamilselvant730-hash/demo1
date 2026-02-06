import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    # Prompt for the key so the script can be run interactively without a .env
    api_key = input("GROQ_API_KEY not set. Enter your GROQ API key (or set GROQ_API_KEY in .env): ").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set. Create a .env file with GROQ_API_KEY=your_key or set the variable in your environment.")

client = Groq(api_key=api_key)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain in detail about GenAI and its application.",
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)