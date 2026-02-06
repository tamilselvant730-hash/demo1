import streamlit as st
import easyocr
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import numpy as np

st.write("🔄 App is loading... please wait")

# ------------------ LOAD MODELS ------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

@st.cache_resource
def load_nlp():
    return SentenceTransformer("all-MiniLM-L6-v2")

ocr = load_ocr()
nlp = load_nlp()

st.write("✅ Models loaded successfully")

# ------------------ FUNCTIONS ------------------
def extract_text(img):
    img_np = np.array(img)
    result = ocr.readtext(img_np)
    return " ".join([r[1] for r in result])

def score_answer(student, model, max_marks):
    e1 = nlp.encode(student, convert_to_tensor=True)
    e2 = nlp.encode(model, convert_to_tensor=True)
    sim = util.cos_sim(e1, e2).item()
    return sim, round(sim * max_marks, 2)

# ------------------ UI ------------------
st.title("🧠 AI Exam Mark Allocation")

model_img = st.file_uploader("Upload Model Answer", ["jpg", "png", "jpeg"])
student_img = st.file_uploader("Upload Student Answer", ["jpg", "png", "jpeg"])
max_marks = st.number_input("Max Marks", 1, 100, 10)

if st.button("Analyze"):
    if model_img and student_img:
        img1 = Image.open(model_img)
        img2 = Image.open(student_img)

        text1 = extract_text(img1)
        text2 = extract_text(img2)

        st.subheader("Extracted Text")
        st.text_area("Model Answer", text1, height=150)
        st.text_area("Student Answer", text2, height=150)

        sim, marks = score_answer(text2, text1, max_marks)

        st.success(f"Similarity: {sim:.2f}")
        st.success(f"Marks: {marks} / {max_marks}")
    else:
        st.warning("Upload both images")
