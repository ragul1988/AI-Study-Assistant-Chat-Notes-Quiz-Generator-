import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("💬 AI Study Assistant")

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
# LOAD MODEL
# =========================
available_models = [
    m.name for m in genai.list_models()
    if "generateContent" in m.supported_generation_methods
]

if not available_models:
    st.error("❌ No compatible models found.")
    st.stop()

model = genai.GenerativeModel(available_models[0])

# =========================
# SESSION STATE
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Clear chat
if st.button("🗑 Clear Chat"):
    st.session_state.chat_history = []

# =========================
# FILE INPUT
# =========================
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        content = page.extract_text()
        if content:
            text_data += content

# limit size
text_data = text_data[:20000]

# =========================
# MODE SELECTOR
# =========================
mode = st.radio(
    "Choose Mode",
    ["💬 Chat", "❓ Ask Question", "📄 Summarize", "🧠 Generate Quiz"]
)

# =========================
# UTIL FUNCTIONS
# =========================
def split_text(text, chunk_size=1500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def summarize_large_pdf(text):
    chunks = split_text(text)
    summaries = []

    for chunk in chunks[:8]:
        prompt = f"""
        Summarize in bullet points:

        {chunk}
        """
        try:
            response = model.generate_content(prompt)
            summaries.append(response.text)
        except:
            summaries.append("⚠️ Error")

    combined = "\n".join(summaries)

    final_prompt = f"""
    Combine into a clear summary:

    {combined}
    """

    try:
        final = model.generate_content(final_prompt)
        return final.text
    except:
        return "❌ Failed summary"

def generate_quiz(text):
    prompt = f"""
    Generate 5 quiz questions with answers.

    Format:
    Q1:
    A:

    Content:
    {text[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# =========================
# ASK QUESTION
# =========================
if mode == "❓ Ask Question":
    question = st.text_input("Ask a question")

    if question:
        prompt = f"""
        Answer based on document:

        {text_data[:8000]}

        Question:
        {question}
        """

        with st.spinner("Thinking..."):
            result = model.generate_content(prompt)

        st.subheader("📌 Answer")
        st.write(result.text)

# =========================
# SUMMARIZE
# =========================
elif mode == "📄 Summarize":
    if st.button("Summarize Document"):
        if not text_data.strip():
            st.warning("Upload PDF first.")
        else:
            with st.spinner("Summarizing..."):
                result = summarize_large_pdf(text_data)

            st.subheader("📄 Summary")
            st.write(result)

# =========================
# QUIZ
# =========================
elif mode == "🧠 Generate Quiz":
    if st.button("Generate Quiz"):
        if not text_data.strip():
            st.warning("Upload PDF first.")
        else:
            with st.spinner("Generating quiz..."):
                result = generate_quiz(text_data)

            st.subheader("🧠 Quiz")
            st.write(result)

# =========================
# CHAT MODE
# =========================
elif mode == "💬 Chat":

    # display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:

        st.session_state.chat_history.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.write(user_input)

        conversation = ""
        for msg in st.session_state.chat_history[-5:]:
            conversation += f"{msg['role']}: {msg['content']}\n"

        prompt = f"""
        Answer using document:

        {text_data}

        Conversation:
        {conversation}
        """

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(prompt)
                    reply = response.text
                except Exception as e:
                    reply = f"❌ Error: {str(e)}"

            st.write(reply)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": reply}
        )
