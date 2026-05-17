import streamlit as st
from huggingface_hub import InferenceClient
from PyPDF2 import PdfReader
import time

st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant (Stable HF Version)")

# =========================
# LOAD TOKEN SAFELY
# =========================
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except:
    st.error("❌ Hugging Face token missing. Add it in Streamlit Secrets.")
    st.stop()

# =========================
# LOAD CLIENT
# =========================
@st.cache_resource
def load_client():
    return InferenceClient(token=HF_TOKEN)

client = load_client()

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

# Limit size (important for stability)
text_data = text_data[:3000]

# =========================
# ACTION SELECTOR
# =========================
option = st.selectbox(
    "Choose Action",
    ["Ask Question", "Summarize", "Generate Quiz"]
)

# =========================
# STABLE GENERATION FUNCTION
# =========================
def generate_response(prompt):
    models = [
        "google/flan-t5-base",   # primary
        "google/flan-t5-small"   # fallback
    ]

    for model in models:
        for attempt in range(3):  # retry 3 times
            try:
                response = client.text_generation(
                    prompt,
                    model=model,
                    max_new_tokens=200,
                )
                return response

            except Exception as e:
                error_msg = str(e)

                # Retry on temporary errors
                if "503" in error_msg or "timeout" in error_msg.lower():
                    time.sleep(2)
                    continue

                # Try next model if failed
                break

    return "❌ Failed to generate response. Please try again."

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
            prompt = f"""Summarize the following content:

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
"""

            with st.spinner("Creating quiz..."):
                result = generate_response(prompt)

            st.subheader("🧠 Quiz")
            st.write(result)
