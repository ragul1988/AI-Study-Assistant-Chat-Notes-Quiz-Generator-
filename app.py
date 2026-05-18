import streamlit as st
from PyPDF2 import PdfReader
import random

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant")

# =========================
# MODE SWITCH
# =========================
use_ai = st.toggle("⚡ Use AI (better answers, uses quota)", value=False)

# =========================
# LOAD AI (OPTIONAL)
# =========================
model = None
if use_ai:
    try:
        import google.generativeai as genai
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        @st.cache_resource
        def load_model():
            return genai.GenerativeModel("models/gemini-1.5-flash")

        model = load_model()

    except:
        st.warning("⚠️ AI not available. Switching to offline mode.")
        use_ai = False

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            text_data += text

text_data = text_data[:10000]

if not text_data.strip():
    st.info("📄 Upload a PDF to start")
    st.stop()

# =========================
# OFFLINE FUNCTIONS
# =========================
def simple_qa(query, text):
    sentences = text.split(".")
    best = ""
    max_score = 0

    q_words = set(query.lower().split())

    for sentence in sentences:
        s_words = set(sentence.lower().split())
        score = len(q_words & s_words)

        if score > max_score:
            max_score = score
            best = sentence

    return best if best else "❌ Answer not found"

def simple_summary(text):
    sentences = text.split(".")
    return ". ".join(sentences[:8])

def generate_quiz(text):
    sentences = text.split(".")
    quiz = []

    for i, s in enumerate(sentences[:5]):
        words = s.split()
        if len(words) > 6:
            answer = words[len(words)//2]

            options = [answer]
            while len(options) < 4:
                w = random.choice(words)
                if w not in options:
                    options.append(w)

            random.shuffle(options)

            quiz.append({
                "question": f"Q{i+1}: {s.replace(answer, '_____')}",
                "options": options,
                "answer": answer
            })

    return quiz

# =========================
# SAFE AI CALL
# =========================
def safe_ai(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return None

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
        if use_ai:
            prompt = f"""
            Answer based on this document:

            {text_data[:4000]}

            Question:
            {query}
            """

            with st.spinner("Thinking..."):
                result = safe_ai(prompt)

            if result:
                st.write(result)
            else:
                st.warning("⚠️ AI failed → showing offline result")
                st.write(simple_qa(query, text_data))

        else:
            st.write(simple_qa(query, text_data))

# =========================
# SUMMARY
# =========================
with tab2:
    if st.button("Generate Summary"):

        if use_ai:
            prompt = f"Summarize:\n{text_data[:4000]}"

            with st.spinner("Summarizing..."):
                result = safe_ai(prompt)

            if result:
                st.write(result)
            else:
                st.warning("⚠️ AI failed → offline summary")
                st.write(simple_summary(text_data))

        else:
            st.write(simple_summary(text_data))

# =========================
# QUIZ + SCORING
# =========================
with tab3:

    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if st.button("Generate Quiz"):

        if use_ai:
            prompt = f"""
            Create 5 MCQ questions.

            Format:
            Q1:
            A)
            B)
            C)
            D)
            Answer: A

            Content:
            {text_data[:4000]}
            """

            with st.spinner("Generating quiz..."):
                result = safe_ai(prompt)

            if result:
                st.session_state.quiz = generate_quiz(text_data)  # fallback structure
            else:
                st.warning("⚠️ AI failed → offline quiz")
                st.session_state.quiz = generate_quiz(text_data)

        else:
            st.session_state.quiz = generate_quiz(text_data)

    if st.session_state.quiz:
        st.subheader("🧠 Quiz")

        for i, q in enumerate(st.session_state.quiz):
            st.write(q["question"])

            selected = st.radio(
                "Choose answer:",
                q["options"],
                key=f"q{i}"
            )

            st.session_state.answers[i] = selected

        if st.button("Submit Quiz"):
            score = 0

            for i, q in enumerate(st.session_state.quiz):
                if st.session_state.answers.get(i) == q["answer"]:
                    score += 1

            st.success(f"🏆 Score: {score} / {len(st.session_state.quiz)}")
