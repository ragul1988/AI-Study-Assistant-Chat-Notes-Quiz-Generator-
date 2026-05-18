import streamlit as st
from PyPDF2 import PdfReader
import numpy as np
import random

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant")

# =========================
# TOGGLE AI MODE
# =========================
use_ai = st.toggle("⚡ Use AI (better answers, uses API)", value=False)

# =========================
# LOAD AI MODEL (OPTIONAL)
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
        st.warning("⚠️ AI unavailable → using offline mode")
        use_ai = False

# =========================
# LOAD EMBEDDING MODEL (OFFLINE AI)
# =========================
from sentence_transformers import SentenceTransformer

@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

embedder = load_embedder()

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

text_data = text_data[:12000]

if not text_data.strip():
    st.info("📄 Upload a PDF to start")
    st.stop()

# =========================
# BUILD SEMANTIC INDEX
# =========================
@st.cache_data
def build_index(text):
    sentences = [s.strip() for s in text.split(".") if len(s) > 20]
    embeddings = embedder.encode(sentences)
    return sentences, embeddings

sentences, embeddings = build_index(text_data)

# =========================
# OFFLINE AI FUNCTIONS
# =========================
def semantic_qa(query):
    query_vec = embedder.encode([query])[0]
    scores = np.dot(embeddings, query_vec)
    best_idx = np.argmax(scores)
    return sentences[best_idx]

def semantic_summary():
    scores = np.mean(embeddings, axis=1)
    top_idx = np.argsort(scores)[-5:]
    return ". ".join([sentences[i] for i in top_idx])

def semantic_quiz():
    quiz = []

    for i, s in enumerate(sentences[:5]):
        words = s.split()
        if len(words) > 6:
            answer = words[len(words)//2]

            options = [answer]
            while len(options) < 4:
                rand_sent = random.choice(sentences)
                rand_words = rand_sent.split()
                if rand_words:
                    w = random.choice(rand_words)
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
            context = semantic_qa(query)

            prompt = f"""
            Answer using this context:

            {context}

            Question:
            {query}
            """

            with st.spinner("Thinking..."):
                result = safe_ai(prompt)

            if result:
                st.write(result)
            else:
                st.warning("⚠️ AI failed → using offline answer")
                st.write(context)

        else:
            st.write(semantic_qa(query))

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
                st.write(semantic_summary())

        else:
            st.write(semantic_summary())

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
                st.session_state.quiz = semantic_quiz()
            else:
                st.warning("⚠️ AI failed → offline quiz")
                st.session_state.quiz = semantic_quiz()

        else:
            st.session_state.quiz = semantic_quiz()

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
