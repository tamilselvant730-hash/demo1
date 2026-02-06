import streamlit as st
import os, json
from dotenv import load_dotenv
from groq import Groq

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Persistent GenAI Chatbot", layout="centered")

CONVERSATION_FILE = "conversation.json"

# ------------------ LOAD API KEY ------------------
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("GROQ_API_KEY not found. Set it in .env file")
    st.stop()

client = Groq(api_key=api_key)

# ------------------ CONVERSATION STORAGE ------------------
def load_conversation():
    if not os.path.exists(CONVERSATION_FILE):
        return []
    with open(CONVERSATION_FILE, "r") as f:
        return json.load(f)

def save_conversation(conv):
    with open(CONVERSATION_FILE, "w") as f:
        json.dump(conv, f, indent=2)

# ------------------ SESSION STATE ------------------
if "conversation" not in st.session_state:
    st.session_state.conversation = load_conversation()

# ------------------ UI ------------------
st.title("🤖 Persistent GenAI Chatbot")

for msg in st.session_state.conversation:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# ------------------ INPUT ------------------
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.conversation.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.conversation
                )
                bot_reply = response.choices[0].message.content
            except Exception as e:
                bot_reply = f"Error: {e}"

            st.write(bot_reply)

    st.session_state.conversation.append(
        {"role": "assistant", "content": bot_reply}
    )

    save_conversation(st.session_state.conversation)
    st.rerun()

# ------------------ SUMMARY ------------------
st.divider()

if st.button("📝 Summarize Conversation"):
    if not st.session_state.conversation:
        st.info("No conversation yet.")
    else:
        with st.spinner("Generating summary..."):
            summary_prompt = "Summarize the following conversation briefly:\n\n"
            summary_prompt += "\n".join(
                f"{m['role']}: {m['content']}"
                for m in st.session_state.conversation
            )

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": summary_prompt}]
            )

            st.success(response.choices[0].message.content)

# ------------------ CLEAR ------------------
if st.button("🗑️ Clear Conversation"):
    st.session_state.conversation = []
    save_conversation([])
    st.rerun()
