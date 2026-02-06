import streamlit as st
from google import genai
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
import re
import json

# =============================
# Load ENV
# =============================
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.stop()

# =============================
# Configure Gemini (NEW SDK)
# =============================
client = genai.Client(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"  # ✅ supported model

# =============================
# Helper Functions
# =============================
def extract_text(file):
    """Extract text from PDF or TXT"""
    if file.type == "application/pdf":
        reader = PdfReader(file)
        return "".join(page.extract_text() or "" for page in reader.pages)
    else:
        return file.read().decode("utf-8", errors="ignore")

def limit_text(text, max_chars=5000):
    """Prevent token overflow"""
    return text[:max_chars]

def clean_json(text):
    """Remove markdown fences like ```json"""
    text = re.sub(r"```json|```", "", text)
    return text.strip()

def evaluate(original, student):
    prompt = f"""
You are an academic exam evaluator.

STRICT RULES:
- Respond with RAW JSON ONLY
- No markdown
- No explanations
- No backticks

Marking Scheme:
- Content accuracy: 50
- Coverage of key points: 30
- Language & clarity: 20
- Total: 100

JSON FORMAT:
{{
  "content_accuracy": number,
  "coverage": number,
  "language_clarity": number,
  "total_marks": number,
  "missing_points": [list],
  "feedback": "text"
}}

ORIGINAL ANSWER:
{original}

STUDENT ANSWER:
{student}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    return response.text

# =============================
# Streamlit UI (SPA)
# =============================
st.set_page_config(
    page_title="AI Document Examiner",
    layout="centered"
)

st.title("📄 AI Document Examiner (Gemini)")
st.write(
    "Upload the **Original / Reference Answer** and the **Student Written Answer** "
    "to automatically evaluate and assign marks."
)

st.divider()

original_file = st.file_uploader(
    "📘 Upload Original / Reference Document",
    type=["pdf", "txt"]
)

student_file = st.file_uploader(
    "✍️ Upload Student Written Document",
    type=["pdf", "txt"]
)

st.divider()

if st.button("🧠 Evaluate Answer", use_container_width=True):

    if not original_file or not student_file:
        st.warning("⚠️ Please upload BOTH documents.")
    else:
        with st.spinner("Evaluating with Gemini AI..."):
            try:
                original_text = limit_text(extract_text(original_file))
                student_text = limit_text(extract_text(student_file))

                raw_result = evaluate(original_text, student_text)
                cleaned_result = clean_json(raw_result)

                # Validate JSON
                parsed = json.loads(cleaned_result)

                st.subheader("📊 Evaluation Result")
                st.json(parsed)

            except json.JSONDecodeError:
                st.error("❌ Invalid JSON returned by Gemini")
                st.code(raw_result)

            except Exception as e:
                st.error("❌ Gemini API Error")
                st.code(str(e))

st.divider()

st.caption("Built with ❤️ using Streamlit + Google Gemini")
