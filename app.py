import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================
# PAGE UI (CENTERED)
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 Doc Mind")
st.subheader("Your Personal AI Study Assistant")
st.caption("Upload a PDF to get instant answers, summaries, and interactive quizzes powered by AI.")
st.markdown("""
## DocMind is an AI-powered tool to:
- Chat with PDF documents
- Generate summaries
- Create quizzes with scoring

Built using Groq API and Streamlit.
""")
st.markdown(
    '<meta name="google-site-verification" content="Mu8rC5XZL81f9FC9zeef-Mx3hYHJPskC1s8ojYtAr2I" />',
    unsafe_allow_html=True
)

# =========================
# GROQ
# =========================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================
# SESSION STATE
# =========================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf")

text_data = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        t = page.extract_text()
        if t:
            text_data += t

text_data = text_data[:8000]

if not text_data.strip():
    st.info("Upload a PDF to begin")
    st.stop()

# =========================
# CHUNKING
# =========================
def chunk_text(text, chunk_size=300):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

chunks = chunk_text(text_data)

# =========================
# TF-IDF RAG
# =========================
@st.cache_resource
def build_vectorizer(chunks):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(chunks)
    return vectorizer, vectors

vectorizer, chunk_vectors = build_vectorizer(chunks)

def retrieve(query, top_k=3):
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, chunk_vectors)[0]

    top_indices = scores.argsort()[-top_k:][::-1]
    return " ".join([chunks[i] for i in top_indices])

# =========================
# GROQ CALL
# =========================
def ask_ai(prompt):
    models = ["llama-3.1-8b-instant", "mixtral-8x7b-32768"]

    for m in models:
        try:
            res = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": "You are an AI study assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return res.choices[0].message.content
        except:
            continue

    return "❌ AI failed."

# =========================
# QUIZ PARSER
# =========================
def parse_quiz(text):
    questions, current = [], None

    for line in text.split("\n"):
        line = line.strip()

        if line.startswith("Q"):
            if current:
                questions.append(current)
            current = {"question": line, "options": [], "answer": ""}

        elif line.startswith(("A)", "B)", "C)", "D)")):
            current["options"].append(line)

        elif line.lower().startswith("answer"):
            current["answer"] = line.split(":")[-1].strip()

    if current:
        questions.append(current)

    return questions

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📄 Summary", "🧠 Quiz"])

# =========================
# CHAT
# =========================
with tab1:

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Ask about the document...")

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})

        context = retrieve(query)

        prompt = f"""
        Answer ONLY from this context:

        {context}

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
# SUMMARY
# =========================
with tab2:
    if st.button("Generate Summary"):
        context = retrieve("summary of document")

        prompt = f"Summarize clearly:\n{context}"

        with st.spinner("Summarizing..."):
            result = ask_ai(prompt)

        st.write(result)

# =========================
# QUIZ
# =========================
with tab3:

    if "quiz_text" not in st.session_state:
        st.session_state.quiz_text = None

    if st.button("Generate Quiz"):
        context = retrieve("important concepts")

        prompt = f"""
        Create 5 MCQs.

        FORMAT:
        Q1:
        A)
        B)
        C)
        D)
        Answer: A

        Content:
        {context}
        """

        result = ask_ai(prompt)

        if result and "A)" in result:
            st.session_state.quiz_text = result
        else:
            st.error("Quiz failed")

    if st.session_state.quiz_text:
        questions = parse_quiz(st.session_state.quiz_text)

        user_answers = {}

        for i, q in enumerate(questions):
            st.write(q["question"])

            selected = st.radio("Select one:", q["options"], key=f"q{i}")
            user_answers[i] = selected

        if st.button("Submit Quiz"):
            score = 0
            for i, q in enumerate(questions):
                if user_answers.get(i, "").startswith(q["answer"]):
                    score += 1

            st.success(f"Score: {score}/{len(questions)}")
