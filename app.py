import streamlit as st
from huggingface_hub import InferenceClient
from PyPDF2 import PdfReader
import time

st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant (Production Version)")

# =========================
# LOAD TOKEN
# =========================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except:
    st.error("❌ Hugging Face token missing. Add it in Streamlit Secrets.")
    st.stop()

# =========================
# INIT CLIENT
# =========================
@st.cache_resource
def load_client():
    return InferenceClient(token=HF_TOKEN)

client = load_client()

# =========================
# INPUT HANDLING
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

# Limit input size (critical)
text_data = text_data[:3000]

# =========================
# ACTION SELECTOR
# =========================
option = st.selectbox(
    "Choose Action",
    ["Ask Question", "Summarize", "Generate Quiz"]
)

# =========================
# PRODUCTION GENERATOR
# =========================
def generate_response(prompt):
    models = [
        "google/flan-t5-small",              # fastest + stable
        "google/flan-t5-base",               # fallback
        "mistralai/Mistral-7B-Instruct-v0.1" # strong fallback
    ]

    for model in models:
        for attempt in range(3):  # retry loop
            try:
                response = client.text_generation(
                    prompt=prompt,
                    model=model,
                    max_new_tokens=200,
                )
                return response

            except Exception as e:
                error_msg = str(e)

                # Retry for temporary failures
                if "503" in error_msg or "timeout" in error_msg.lower():
                    time.sleep(2)
                    continue

                # Try next model
                break

    return "❌ All models failed. Please try again later."

# =========================
# ASK QUESTION
# =========================
if option == "Ask Question":
    query = st.text_input("Ask your question")

    if query:
        prompt = f"""Context:
{text_data}

Question: {query}

Answer clearly and concisely:"""

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
            prompt = f"""Summarize the following content clearly:

{text_data}
"""

            with st.spinner("Generating summary..."):
                result = generate_response(prompt)

            st.subheader("📄 Summary")
            st.write(result)

# =========================
# QUIZ GENERATOR
# =========================
elif option == "Generate Quiz":
    if st.button("Create Quiz"):
        if not text_data.strip():
            st.warning("Please upload or enter some text.")
        else:
            prompt = f"""From the following content:

{text_data}

Generate 5 quiz questions with answers.
Make them clear and useful for learning.
"""

            with st.spinner("Creating quiz..."):
                result = generate_response(prompt)

            st.subheader("🧠 Quiz")
            st.write(result)
