import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq

# =========================
# PAGE UI (CENTERED)
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 Doc Mind")
st.subheader("Your Personal AI Study Assistant")
st.caption("Upload a PDF to get instant answers, summaries, and interactive quizzes powered by AI.")
st.markdown("""
## AIDocMind – AI PDF Assistant

AIDocMind is an AI-powered tool to:
- Chat with PDF documents
- Generate summaries
- Create quizzes with scoring

Built using Groq API and Streamlit.
""")
st.markdown(
    '<meta name="google-site-verification" content="abc123" />',
    unsafe_allow_html=True
)
# =========================
# LOAD GROQ
# =========================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("❌ Add GROQ_API_KEY in Streamlit secrets")
    st.stop()

# =========================
# CHAT MEMORY
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# FILE UPLOAD (ONLY ONE)
# =========================
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_main")

text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            text_data += text

text_data = text_data[:6000]

if not text_data.strip():
    st.info("📄 Upload a PDF to start")
    st.stop()

# =========================
# AI FUNCTION
# =========================
def ask_ai(prompt):
    models = [
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    for m in models:
        try:
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            text = response.choices[0].message.content
            if text and len(text.strip()) > 20:
                return text

        except:
            continue

    return "❌ AI failed. Try again."

# =========================
# QUIZ PARSER
# =========================
def parse_quiz(text):
    questions = []
    current_q = None

    for line in text.split("\n"):
        line = line.strip()

        if line.startswith("Q"):
            if current_q:
                questions.append(current_q)
            current_q = {"question": line, "options": [], "answer": ""}

        elif line.startswith(("A)", "B)", "C)", "D)")):
            current_q["options"].append(line)

        elif line.lower().startswith("answer"):
            current_q["answer"] = line.split(":")[-1].strip()

    if current_q:
        questions.append(current_q)

    return questions

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Summary", "🧠 Quiz"])

# =========================
# CHAT TAB (CHATGPT STYLE)
# =========================
with tab1:

    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🗑"):
            st.session_state.chat_history = []
            st.rerun()

    # show history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Ask something about the document...")

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})

        prompt = f"""
        Answer based on this document:

        {text_data}

        Question:
        {query}
        """

        with st.spinner("Thinking..."):
            response = ask_ai(prompt)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": response}
        )

        st.rerun()

# =========================
# SUMMARY TAB
# =========================
with tab2:
    if st.button("Generate Summary"):
        prompt = f"Summarize in bullet points:\n{text_data}"

        with st.spinner("Summarizing..."):
            result = ask_ai(prompt)

        st.markdown(result)

# =========================
# QUIZ TAB
# =========================
with tab3:

    if "quiz_text" not in st.session_state:
        st.session_state.quiz_text = None

    if st.button("Generate Quiz"):

        quiz_context = text_data[:3000]

        for _ in range(2):
            prompt = f"""
            Create EXACTLY 5 MCQs.

            FORMAT:

            Q1: Question
            A) Option
            B) Option
            C) Option
            D) Option
            Answer: A

            CONTENT:
            {quiz_context}
            """

            result = ask_ai(prompt)

            if result and "A)" in result:
                st.session_state.quiz_text = result
                break

        if not st.session_state.quiz_text:
            st.error("❌ Quiz failed")

    if st.session_state.quiz_text:
        questions = parse_quiz(st.session_state.quiz_text)

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
                if user_answers.get(i, "").startswith(q["answer"]):
                    score += 1

            total = len(questions)
            st.success(f"🏆 Score: {score}/{total}")
