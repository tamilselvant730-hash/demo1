import streamlit as st
import pandas as pd
import json
from textblob import TextBlob

st.set_page_config(page_title="Movie Review Sentiment Analyzer", layout="centered")

st.title("🎬 Movie Review Sentiment Analysis")
st.write("Upload a CSV file containing movie review comments")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])


def analyze_sentiment(text):
    polarity = TextBlob(str(text)).sentiment.polarity
    return "Positive" if polarity >= 0 else "Negative"

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Detect first text column automatically
    text_column = df.select_dtypes(include="object").columns[0]

    st.success(f"Detected review column: **{text_column}**")

    df["Sentiment"] = df[text_column].apply(analyze_sentiment)

    total = len(df)
    positive = (df["Sentiment"] == "Positive").sum()
    negative = (df["Sentiment"] == "Negative").sum()

    pos_percent = round((positive / total) * 100, 2)
    neg_percent = round((negative / total) * 100, 2)

    st.subheader("📊 Sentiment Results")
    st.write(f"**Total Reviews:** {total}")
    st.write(f"✅ Positive: {positive} ({pos_percent}%)")
    st.write(f"❌ Negative: {negative} ({neg_percent}%)")

    st.subheader("📄 Analyzed Reviews")
    st.dataframe(df)

    overall_review = (
        "Overall reviews are Positive 👍"
        if positive >= negative
        else "Overall reviews are Negative 👎"
    )

    summary = {
        "total_reviews": total,
        "positive_reviews": positive,
        "negative_reviews": negative,
        "positive_percentage": pos_percent,
        "negative_percentage": neg_percent,
        "overall_review": overall_review
    }

    st.subheader("🧾 JSON Summary")
    st.json(summary)

    # Download JSON
    st.download_button(
        label="Download Summary JSON",
        data=json.dumps(summary, indent=4),
        file_name="sentiment_summary.json",
        mime="application/json"
    )
