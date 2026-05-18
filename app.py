import streamlit as st
import requests
from PyPDF2 import PdfReader

st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant (Stable API Version)")

# =========================
# LOAD API KEY
# =========================
try:
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
except:
    st.error("❌ API key missing. Add it in Streamlit Secrets.")
    st.stop()

# =========================
# FILE INPUT
# =========================
uploaded_file = st.file_uploader("Upload PDF (optional)", type=["pdf"])
text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text_data += content

manual_text = st.text_area("Or paste your notes here:")

if manual_text:
    text_data = manual_text

text_data = text_data[:3000]

# =========================
# ACTION SELECTOR
# =========================
option = st.selectbox(
    "Choose Action",
    ["Ask Question", "Summarize", "Generate Quiz"]
)

# =========================
# API CALL FUNCTION
# =========================
def generate_response(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3-8b-instruct",  # stable free model
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        # 🔍 DEBUG (keep temporarily)
        st.write("API Response:", result)

        # ✅ Correct extraction
        if "choices" in result:
            return result["choices"][0]["message"]["content"]

        elif "error" in result:
            return f"❌ API Error: {result['error']['message']}"

        else:
            return "❌ Unexpected response format."

    except Exception as e:
        return f"❌ Exception: {str(e)}"
# =========================
# ASK QUESTION
# =========================
if option == "Ask Question":
    query = st.text_input("Ask your question")

    if query:
        prompt = f"""Context:
{text_data}

Question: {query}

Answer clearly:"""

        with st.spinner("Thinking..."):
            result = generate_response(prompt)

        st.subheader("📌 Answer")
        st.write(result)

# =========================
# SUMMARIZE
# =========================
elif option == "Summarize":
    if st.button("Generate Summary"):
        if not text_data.strip():
            st.warning("Please upload or enter some text.")
        else:
            prompt = f"""Summarize this content clearly:

{text_data}
"""

            with st.spinner("Generating summary..."):
                result = generate_response(prompt)

            st.subheader("📄 Summary")
            st.write(result)
# =========================
# QUIZ
# =========================
elif option == "Generate Quiz":
    if st.button("Create Quiz"):
        if not text_data.strip():
            st.warning("Please enter text.")
        else:
            prompt = f"""From this content:

{text_data}

Generate 5 quiz questions with answers.
"""

            with st.spinner("Creating quiz..."):
                result = generate_response(prompt)

            st.subheader("🧠 Quiz")
            st.write(result)
