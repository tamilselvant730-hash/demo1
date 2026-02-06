from flask import Flask, request, render_template_string, jsonify
import os, json
from dotenv import load_dotenv
from groq import Groq

# Load API key
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    api_key = input("GROQ_API_KEY not set. Enter your GROQ API key: ").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required")

client = Groq(api_key=api_key)
app = Flask(__name__)

# Conversation file to store all chats
CONVERSATION_FILE = "conversation.json"

# Initialize conversation file if not exists
if not os.path.exists(CONVERSATION_FILE):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump([], f)

# HTML template
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Persistent Chatbot with Summary</title>
    <style>
        body { font-family: Arial; background: #f0f2f5; display: flex; justify-content: center; align-items: flex-start; padding-top: 30px; }
        .chat-container { background: white; padding: 20px; width: 500px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        #chat-box { height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 5px; background: #fafafa; }
        .user-msg { text-align: right; margin-bottom: 10px; }
        .bot-msg { text-align: left; margin-bottom: 10px; }
        .summary-msg { text-align: center; margin-top: 10px; font-style: italic; color: #333; }
        input { width: 70%; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { width: 25%; padding: 10px; border: none; background: #4CAF50; color: white; border-radius: 5px; cursor: pointer; margin-top: 5px; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Persistent GenAI Chatbot</h2>
        <div id="chat-box"></div>
        <input type="text" id="user-input" placeholder="Type your message..." autocomplete="off">
        <button onclick="sendMessage()">Send</button>
        <button onclick="summarizeConversation()">Summarize Conversation</button>
    </div>

<script>
    async function sendMessage() {
        const input = document.getElementById("user-input");
        const message = input.value.trim();
        if (!message) return;

        const chatBox = document.getElementById("chat-box");
        chatBox.innerHTML += `<div class="user-msg"><b>You:</b> ${message}</div>`;
        input.value = "";

        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message})
        });

        const data = await response.json();
        chatBox.innerHTML += `<div class="bot-msg"><b>Bot:</b> ${data.reply || data.error}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function summarizeConversation() {
        const chatBox = document.getElementById("chat-box");
        const response = await fetch("/summary");
        const data = await response.json();
        chatBox.innerHTML += `<div class="summary-msg"><b>Summary:</b> ${data.summary}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Load previous conversation on page load
    window.onload = async function() {
        const response = await fetch("/load");
        const data = await response.json();
        const chatBox = document.getElementById("chat-box");
        data.conversation.forEach(m => {
            const cls = m.role === "user" ? "user-msg" : "bot-msg";
            chatBox.innerHTML += `<div class="${cls}"><b>${m.role === 'user' ? 'You' : 'Bot'}:</b> ${m.content}</div>`;
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    document.getElementById("user-input").addEventListener("keydown", function(e) {
        if (e.key === "Enter") sendMessage();
    });
</script>
</body>
</html>
"""

# Load conversation from file
def load_conversation():
    with open(CONVERSATION_FILE, "r") as f:
        return json.load(f)

# Save conversation to file
def save_conversation(conv):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump(conv, f, indent=2)

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/load")
def load():
    conv = load_conversation()
    return jsonify({"conversation": conv})

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    conversation = load_conversation()
    conversation.append({"role": "user", "content": user_message})

    try:
        chat_completion = client.chat.completions.create(
            messages=conversation,
            model="llama-3.3-70b-versatile"
        )
        bot_reply = chat_completion.choices[0].message.content
    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    conversation.append({"role": "assistant", "content": bot_reply})
    save_conversation(conversation)

    return jsonify({"reply": bot_reply})

@app.route("/summary")
def summary():
    conversation = load_conversation()
    if not conversation:
        return jsonify({"summary": "No conversation yet."})

    try:
        summary_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": "Summarize the following conversation briefly:\n" +
                           "\n".join([f"{m['role']}: {m['content']}" for m in conversation])
            }],
            model="llama-3.3-70b-versatile"
        )
        summary_text = summary_completion.choices[0].message.content
    except Exception as e:
        summary_text = f"Error generating summary: {str(e)}"

    return jsonify({"summary": summary_text})

if __name__ == "__main__":
    app.run(debug=True)
