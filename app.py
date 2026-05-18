import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="AI Study Assistant", layout="centered")

st.title("💬 AI Study Assistant (Chat Mode)")

# =========================
# LOAD API KEY
# =========================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ Gemini API key missing.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

# =========================
# LOAD MODEL (AUTO)
# =========================
available_models = [
    m.name for m in genai.list_models()
    if "generateContent" in m.supported_generation_methods
]

model = genai.GenerativeModel(available_models[0])

# =========================
# SESSION STATE (MEMORY)
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# PDF INPUT
# =========================
uploaded_file = st.file_uploader("Upload PDF (optional)", type=["pdf"])

text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text_data += content

text_data = text_data[:8000]

# =========================
# DISPLAY CHAT HISTORY
# =========================
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# =========================
# USER INPUT
# =========================
user_input = st.chat_input("Ask something about your notes...")

if user_input:

    # Show user message
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.write(user_input)

    # Build conversation context
    conversation = ""

    for msg in st.session_state.chat_history[-5:]:
        conversation += f"{msg['role']}: {msg['content']}\n"

    prompt = f"""
    You are a helpful AI study assistant.

    Context (from PDF):
    {text_data}

    Conversation:
    {conversation}

    Answer clearly and helpfully:
    """

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = model.generate_content(prompt)
                reply = response.text
            except Exception as e:
                reply = f"❌ Error: {str(e)}"

        st.write(reply)

    # Save assistant response
    st.session_state.chat_history.append(
        {"role": "assistant", "content": reply}
    )
