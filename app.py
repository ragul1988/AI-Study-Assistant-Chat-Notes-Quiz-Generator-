import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="AI Study Assistant", layout="centered")

st.title("📚 AI Study Assistant")

# =========================
# LOAD API KEY
# =========================
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("❌ Gemini API key missing.")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash-latest")

# =========================
# PDF INPUT
# =========================
uploaded_file = st.file_uploader(
    "Upload PDF (optional)",
    type=["pdf"]
)

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

# limit size
text_data = text_data[:10000]

# =========================
# ACTIONS
# =========================
option = st.selectbox(
    "Choose Action",
    ["Ask Question", "Summarize", "Generate Quiz"]
)

# =========================
# RESPONSE FUNCTION
# =========================
def generate_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# =========================
# ASK QUESTION
# =========================
if option == "Ask Question":

    query = st.text_input("Ask your question")

    if query:
        prompt = f"""
        Context:
        {text_data}

        Question:
        {query}

        Answer clearly.
        """

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
            st.warning("Please upload or enter text.")

        else:
            prompt = f"""
            Summarize this content clearly:

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
            st.warning("Please upload or enter text.")

        else:
            prompt = f"""
            From this content:

            {text_data}

            Generate 5 quiz questions with answers.
            """

            with st.spinner("Creating quiz..."):
                result = generate_response(prompt)

            st.subheader("🧠 Quiz")
            st.write(result)
