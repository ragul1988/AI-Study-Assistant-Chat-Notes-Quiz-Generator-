import streamlit as st
from PyPDF2 import PdfReader
import re
import random

# =========================
# PAGE SETUP
# =========================
st.set_page_config(page_title="AI Study Assistant", layout="centered")
st.title("📚 AI Study Assistant")

# =========================
# AI TOGGLE
# =========================
use_ai = st.toggle("⚡ Use AI (better answers, uses API)", value=False)

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
        st.warning("⚠️ AI unavailable → using offline mode")
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
# TEXT PROCESSING
# =========================
def preprocess(text):
    return re.findall(r'\b\w+\b', text.lower())

sentences = [s.strip() for s in text_data.split(".") if len(s) > 20]

# =========================
# SMART OFFLINE ANSWER
# =========================
def smart_answer(query):
    query_words = set(preprocess(query))

    scored_sentences = []

    for sentence in sentences:
        words = set(preprocess(sentence))

        overlap = len(query_words & words)
        density = overlap / (len(words) + 1)
        score = overlap + density

        # filter junk
        if len(sentence) < 20:
            continue
        if sentence.isupper():
            continue

        scored_sentences.append((score, sentence.strip()))

    # sort by relevance
    scored_sentences.sort(reverse=True)

    # take top 3 sentences
    top_sentences = [s for _, s in scored_sentences[:3]]

    if not top_sentences:
        return "❌ No relevant answer found."

    combined = " ".join(top_sentences)

    return f"""
### 📌 Answer
{combined}

---

### 📌 Answer
{best_sentence.strip()}

---

### 💡 Explanation
This answer is based on relevant content related to: **{keywords}**.

---

### 🧠 Insight
The document highlights this concept as important and directly relevant to your question.
"""

# =========================
# SUMMARY
# =========================
def smart_summary():
    scored = []

    for s in sentences:
        words = preprocess(s)
        score = len(set(words))
        scored.append((score, s))

    scored.sort(reverse=True)

    top = [s for _, s in scored[:5]]

    result = "### 📄 Summary\n\n"
    for s in top:
        result += f"- {s.strip()}\n"

    result += "\n---\n### 🧠 Key Takeaway\nThis document emphasizes the main concepts listed above."

    return result

# =========================
# QUIZ
# =========================
def generate_quiz():
    quiz = []

    stop_words = {"the", "of", "in", "and", "to", "a", "is", "for"}

    for i, s in enumerate(sentences[:5]):
        words = s.split()

        # filter meaningful words
        keywords = [
            w for w in words
            if len(w) > 4 and w.lower() not in stop_words
        ]

        if len(keywords) < 1:
            continue

        # pick a meaningful keyword
        answer = keywords[0]

        # generate better distractors
        distractors = []
        for other in sentences:
            for w in other.split():
                if len(w) > 4 and w.lower() not in stop_words and w != answer:
                    distractors.append(w)

        options = list(set([answer] + distractors[:10]))[:4]

        if len(options) < 4:
            continue

        random.shuffle(options)

        question = s.replace(answer, "_____")

        quiz.append({
            "question": f"Q{i+1}: {question}",
            "options": options,
            "answer": answer
        })

    return quiz

# =========================
# SAFE AI
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
            context = smart_answer(query)

            prompt = f"""
            Improve this answer:

            {context}
            """

            with st.spinner("Thinking..."):
                result = safe_ai(prompt)

            if result:
                st.markdown(result)
            else:
                st.warning("⚠️ AI failed → showing offline answer")
                st.markdown(context)

        else:
            st.markdown(smart_answer(query))

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
                st.markdown(result)
            else:
                st.warning("⚠️ AI failed → offline summary")
                st.markdown(smart_summary())

        else:
            st.markdown(smart_summary())

# =========================
# QUIZ + SCORING
# =========================
with tab3:

    if "quiz" not in st.session_state:
        st.session_state.quiz = None
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if st.button("Generate Quiz"):
        st.session_state.quiz = generate_quiz()

    if st.session_state.quiz:
        st.subheader("🧠 Quiz")

        for i, q in enumerate(st.session_state.quiz):
            st.markdown(f"### {q['question']}")

            selected = st.radio(
                "Select one:",
                q["options"],
                key=f"q{i}"
            )

            st.session_state.answers[i] = selected

        if st.button("Submit Quiz"):
            score = 0

            for i, q in enumerate(st.session_state.quiz):
                if st.session_state.answers.get(i) == q["answer"]:
                    score += 1

            total = len(st.session_state.quiz)
            percent = (score / total) * 100

            st.success(f"🏆 Score: {score} / {total} ({percent:.0f}%)")

            if percent >= 80:
                st.markdown("🔥 **Excellent understanding!**")
            elif percent >= 50:
                st.markdown("👍 **Good job, keep improving.**")
            else:
                st.markdown("📚 **Review the material again.**")
