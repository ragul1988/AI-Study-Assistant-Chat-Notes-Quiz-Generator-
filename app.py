import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant (Groq AI)")

# =========================
# LOAD GROQ
# =========================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("❌ Add GROQ_API_KEY in Streamlit secrets")
    st.stop()

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

text_data = ""

if uploaded_file:
    with st.spinner("Reading PDF..."):
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_data += text

text_data = text_data[:8000]

if not text_data.strip():
    st.info("📄 Upload a PDF to start")
    st.stop()

# =========================
# AI FUNCTION
# =========================
def ask_ai(prompt):
    models = [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768"
    ]

    for m in models:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": "You are a helpful AI study assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content

        except Exception as e:
            continue

    return "❌ All models failed. Try again later."

# =========================
# UI TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Summary", "🧠 Quiz"])

# =========================
# CHAT
# =========================
with tab1:
    query = st.text_input("Ask something from the document")

    if query:
        prompt = f"""
        Answer clearly based on the document.

        DOCUMENT:
        {text_data}

        QUESTION:
        {query}

        Give:
        - Clear answer
        - Short explanation
        """

        with st.spinner("Thinking..."):
            result = ask_ai(prompt)

        st.markdown(result)

# =========================
# SUMMARY
# =========================
with tab2:
    if st.button("Generate Summary"):
        prompt = f"""
        Summarize the following document in clear bullet points:

        {text_data}
        """

        with st.spinner("Summarizing..."):
            result = ask_ai(prompt)

        st.markdown(result)

# =========================
# QUIZ + SCORING
# =========================
with tab3:

    if "quiz_text" not in st.session_state:
        st.session_state.quiz_text = None

    if st.button("Generate Quiz"):
        prompt = f"""
        Create 5 multiple choice questions.

        Format strictly:
        Q1:
        A)
        B)
        C)
        D)
        Answer: A

        Based on:
        {text_data}
        """

        with st.spinner("Generating quiz..."):
            st.session_state.quiz_text = ask_ai(prompt)

    if st.session_state.quiz_text:
        st.subheader("🧠 Quiz")

        quiz_lines = st.session_state.quiz_text.split("\n")

        questions = []
        current_q = {}

        for line in quiz_lines:
            if line.startswith("Q"):
                if current_q:
                    questions.append(current_q)
                current_q = {"question": line, "options": [], "answer": ""}
            elif line.startswith(("A)", "B)", "C)", "D)")):
                current_q["options"].append(line)
            elif "Answer" in line:
                current_q["answer"] = line.split(":")[-1].strip()

        if current_q:
            questions.append(current_q)

        user_answers = {}

        for i, q in enumerate(questions):
            st.markdown(f"### {q['question']}")

            selected = st.radio(
                "Select one:",
                q["options"],
                key=f"q{i}"
            )

            user_answers[i] = selected

        if st.button("Submit Quiz"):
            score = 0

            for i, q in enumerate(questions):
                if user_answers[i].startswith(q["answer"]):
                    score += 1

            total = len(questions)
            percent = (score / total) * 100

            st.success(f"🏆 Score: {score}/{total} ({percent:.0f}%)")

            if percent >= 80:
                st.markdown("🔥 Excellent!")
            elif percent >= 50:
                st.markdown("👍 Good job!")
            else:
                st.markdown("📚 Review the material again.")
