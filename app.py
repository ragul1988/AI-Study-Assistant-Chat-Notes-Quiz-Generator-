import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq

# =========================
# PAGE
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 Doc Mind")
st.subheader("Your Personal AI Study Assistant")
st.caption("Upload a PDF to get instant answers, summaries, and interactive quizzes powered by AI.")
# =========================
# LOAD GROQ
# =========================
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("❌ Add GROQ_API_KEY in Streamlit secrets")
    st.stop()

# =========================
# FILE UPLOADER (ONLY ONE)
# =========================
uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"],
    key="main_pdf_uploader"
)

text_data = ""

if uploaded_file:
    with st.spinner("Reading PDF..."):
        pdf = PdfReader(uploaded_file)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_data += text

# limit size
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
                    {"role": "system", "content": "You are a helpful AI study assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            text = response.choices[0].message.content

            if text and len(text.strip()) > 20:
                return text

        except:
            continue

    return None

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
            if current_q:
                current_q["options"].append(line)

        elif line.lower().startswith("answer"):
            if current_q:
                current_q["answer"] = line.split(":")[-1].strip()

    if current_q:
        questions.append(current_q)

    return questions
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Summary", "🧠 Quiz"])

# =========================
# CHAT
# =========================
with tab1:
    st.subheader("💬 Chat with your document")

    # display chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content']}")

    query = st.text_input("Ask something...", key="chat_input")

    if query:
        # add user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": query
        })

        prompt = f"""
        Answer clearly based on the document.

        DOCUMENT:
        {text_data}

        QUESTION:
        {query}

        Give:
        - Direct answer
        - Short explanation
        """

        with st.spinner("Thinking..."):
            result = ask_ai(prompt)

        if result:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "❌ Failed to generate answer"
            })

        st.rerun()
    if st.button("🗑 Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()
# =========================
# SUMMARY
# =========================
with tab2:
    if st.button("Generate Summary"):
        prompt = f"""
        Summarize the document in bullet points:

        {text_data}
        """

        with st.spinner("Summarizing..."):
            result = ask_ai(prompt)

        if result:
            st.markdown(result)
        else:
            st.error("❌ Failed to generate summary")

# =========================
# QUIZ
# =========================
with tab3:

    if "quiz_text" not in st.session_state:
        st.session_state.quiz_text = None

    if st.button("Generate Quiz"):

        quiz_context = text_data[:3000]

        for _ in range(2):  # retry logic
            prompt = f"""
            You are an exam generator.

            Create EXACTLY 5 multiple choice questions.

            STRICT FORMAT:

            Q1: Question text
            A) Option
            B) Option
            C) Option
            D) Option
            Answer: A

            Repeat for Q2 to Q5.

            CONTENT:
            {quiz_context}
            """

            result = ask_ai(prompt)

            if result and "A)" in result and "Q1" in result:
                st.session_state.quiz_text = result
                break

        if not st.session_state.quiz_text:
            st.error("❌ Quiz generation failed. Try again.")

    # DISPLAY QUIZ
    if st.session_state.quiz_text:

        questions = parse_quiz(st.session_state.quiz_text)

        if not questions:
            st.error("❌ Quiz parsing failed.")
        else:
            st.subheader("🧠 Quiz")

            user_answers = {}

            for i, q in enumerate(questions):
                st.markdown(f"### {q['question']}")

                if not q["options"]:
                    st.warning("⚠️ No options found")
                    continue

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
                percent = (score / total) * 100

                st.success(f"🏆 Score: {score}/{total} ({percent:.0f}%)")

                if percent >= 80:
                    st.markdown("🔥 Excellent!")
                elif percent >= 50:
                    st.markdown("👍 Good job!")
                else:
                    st.markdown("📚 Review the material again.")
