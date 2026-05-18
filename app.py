import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant")

# =========================
# LOAD API KEY
# =========================
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except:
    st.error("❌ Add GEMINI_API_KEY in Streamlit secrets")
    st.stop()

model = genai.GenerativeModel("models/gemini-1.5-flash")

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

# Limit size (important)
text_data = text_data[:15000]

if not text_data.strip():
    st.info("📄 Upload a PDF to begin")
    st.stop()

# =========================
# RAG FUNCTIONS
# =========================
def split_chunks(text, chunk_size=300):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def build_index(chunks):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(chunks)
    return vectorizer, vectors

def retrieve_chunks(query, chunks, vectorizer, vectors):
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, vectors).flatten()
    top_indices = scores.argsort()[-2:][::-1]  # fewer chunks = faster
    return " ".join([chunks[i] for i in top_indices])

# =========================
# CACHE RAG INDEX (FIX)
# =========================
@st.cache_data
def prepare_rag(text):
    chunks = split_chunks(text)
    vectorizer, vectors = build_index(chunks)
    return chunks, vectorizer, vectors

chunks, vectorizer, vectors = prepare_rag(text_data)

# =========================
# PARSE QUIZ
# =========================
def parse_quiz(text):
    questions = text.split("Q")[1:]
    quiz_data = []

    for q in questions:
        try:
            lines = q.strip().split("\n")
            question = "Q" + lines[0]

            options = []
            answer = ""

            for line in lines[1:]:
                if line.startswith(("A)", "B)", "C)", "D)")):
                    options.append(line)
                if "Answer" in line:
                    answer = line.split(":")[-1].strip()

            quiz_data.append({
                "question": question,
                "options": options,
                "answer": answer
            })
        except:
            continue

    return quiz_data

# =========================
# UI TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💬 Chat (RAG)", "📄 Summary", "🧠 Quiz"])

# =========================
# CHAT (FAST RAG)
# =========================
with tab1:
    query = st.text_input("Ask something from the document")

    if query:
        context = retrieve_chunks(query, chunks, vectorizer, vectors)[:1200]

        prompt = f"""
        Answer using this context:

        {context}

        Question:
        {query}
        """

        with st.spinner("Thinking..."):
            try:
                response = model.generate_content(prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"❌ API Error: {e}")

# =========================
# SUMMARY (LIGHT)
# =========================
with tab2:
    if st.button("Generate Summary"):
        prompt = f"Summarize this:\n{text_data[:6000]}"

        with st.spinner("Summarizing..."):
            try:
                response = model.generate_content(prompt)
                st.write(response.text)
            except Exception as e:
                st.error(f"❌ Error: {e}")

# =========================
# QUIZ + SCORING
# =========================
with tab3:

    if "quiz_data" not in st.session_state:
        st.session_state.quiz_data = None
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}

    if st.button("Generate Quiz"):
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
        {text_data[:6000]}
        """

        with st.spinner("Generating quiz..."):
            try:
                response = model.generate_content(prompt)
                st.session_state.quiz_data = parse_quiz(response.text)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.session_state.quiz_data:

        st.subheader("🧠 Quiz")

        for i, q in enumerate(st.session_state.quiz_data):
            st.write(q["question"])

            selected = st.radio(
                "Choose answer:",
                q["options"],
                key=f"q{i}"
            )

            st.session_state.user_answers[i] = selected

        if st.button("Submit Quiz"):
            score = 0

            for i, q in enumerate(st.session_state.quiz_data):
                selected = st.session_state.user_answers.get(i, "")
                correct = q["answer"]

                if selected.startswith(correct):
                    score += 1

            st.success(f"🏆 Score: {score} / {len(st.session_state.quiz_data)}")
