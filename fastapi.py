from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, json
from dotenv import load_dotenv
from groq import Groq

# ================== ENV + GROQ ==================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY is required")

client = Groq(api_key=api_key)

# ================== FASTAPI APP ==================
app = FastAPI(title="Persistent GenAI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== STORAGE ==================
CONVERSATION_FILE = "conversation.json"

if not os.path.exists(CONVERSATION_FILE):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump([], f)

def load_conversation():
    with open(CONVERSATION_FILE, "r") as f:
        return json.load(f)

def save_conversation(conv):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump(conv, f, indent=2)

# ================== HTML UI ==================
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Persistent Chatbot with Summary</title>
    <style>
        body {
            font-family: Arial;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            padding-top: 20px;
        }
        .chat-container {
            background: white;
            padding: 20px;
            width: 650px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        #chat-box {
            height: 520px;
            overflow-y: auto;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            background: #fafafa;
        }
        .user-msg { text-align: right; margin-bottom: 8px; }
        .bot-msg { text-align: left; margin-bottom: 8px; }
        .summary-msg {
            text-align: center;
            font-style: italic;
            color: #333;
            margin-top: 10px;
        }
        input {
            width: 75%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        button {
            width: 23%;
            padding: 10px;
            border: none;
            background: #4CAF50;
            color: white;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 5px;
        }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
<div class="chat-container">
    <h2>Persistent GenAI Chatbot</h2>
    <div id="chat-box"></div>
    <input id="user-input" placeholder="Type your message..." autocomplete="off"/>
    <button onclick="sendMessage()">Send</button>
    <button onclick="summarizeConversation()">Summarize</button>
</div>

<script>
async function sendMessage() {
    const input = document.getElementById("user-input");
    const msg = input.value.trim();
    if (!msg) return;

    const chat = document.getElementById("chat-box");
    chat.innerHTML += `<div class="user-msg"><b>You:</b> ${msg}</div>`;
    input.value = "";

    const res = await fetch("/chat", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    });

    const data = await res.json();
    chat.innerHTML += `<div class="bot-msg"><b>Bot:</b> ${data.reply}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

async function summarizeConversation() {
    const chat = document.getElementById("chat-box");
    const res = await fetch("/summary");
    const data = await res.json();
    chat.innerHTML += `<div class="summary-msg"><b>Summary:</b> ${data.summary}</div>`;
    chat.scrollTop = chat.scrollHeight;
}

window.onload = async () => {
    const res = await fetch("/load");
    const data = await res.json();
    const chat = document.getElementById("chat-box");

    data.conversation.forEach(m => {
        const cls = m.role === "user" ? "user-msg" : "bot-msg";
        const name = m.role === "user" ? "You" : "Bot";
        chat.innerHTML += `<div class="${cls}"><b>${name}:</b> ${m.content}</div>`;
    });
    chat.scrollTop = chat.scrollHeight;
};

document.getElementById("user-input")
    .addEventListener("keydown", e => {
        if (e.key === "Enter") sendMessage();
    });
</script>
</body>
</html>
"""

# ================== ROUTES ==================
@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.get("/load")
async def load():
    return {"conversation": load_conversation()}

@app.post("/chat")
async def chat(req: Request):
    data = await req.json()
    user_message = data.get("message")

    if not user_message:
        return JSONResponse({"error": "No message provided"}, status_code=400)

    conversation = load_conversation()
    conversation.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation
        )
        bot_reply = response.choices[0].message.content
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    conversation.append({"role": "assistant", "content": bot_reply})
    save_conversation(conversation)

    return {"reply": bot_reply}

@app.get("/summary")
async def summary():
    conversation = load_conversation()
    if not conversation:
        return {"summary": "No conversation yet."}

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": "Summarize the following conversation briefly:\n" +
                           "\n".join(f"{m['role']}: {m['content']}" for m in conversation)
            }]
        )
        summary_text = response.choices[0].message.content
    except Exception as e:
        summary_text = f"Error: {str(e)}"

    return {"summary": summary_text}
