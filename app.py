# ----------------- Imports -----------------
import os
import re
import shutil
import subprocess
import stat
import streamlit as st

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# ----------------- Page Config -----------------
st.set_page_config(
    page_title="RAG Code Navigator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- Custom CSS -----------------
st.markdown("""
<style>

/* ================= GLOBAL BACKGROUND ================= */
.stApp {
    background: linear-gradient(135deg, #0f172a, #1e293b);
    color: #ffffff;
}

/* ================= HERO SECTION ================= */
.hero-container {
    background: linear-gradient(90deg, #1e3a8a, #312e81);
    padding: 45px 30px;
    border-radius: 20px;
    margin-bottom: 40px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(59,130,246,0.2);
}

.main-title {
    font-size: 48px;
    font-weight: 800;
    margin-bottom: 10px;
    background: linear-gradient(90deg, #38bdf8, #6366f1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    font-size: 18px;
    color: #ffffff;
}

/* ================= SIDEBAR FIX ================= */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a, #111827);
    border-right: 1px solid #1f2937;
}

/* Sidebar Headings */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #ffffff !important;
    font-weight: 700 !important;
}

/* Sidebar Labels */
section[data-testid="stSidebar"] label {
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Sidebar Text */
section[data-testid="stSidebar"] p {
    color: #ffffff !important;
}

/* Sidebar Inputs */
section[data-testid="stSidebar"] input {
    color: #ffffff !important;
}

/* ================= INPUT ================= */
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border: 1px solid #475569 !important;
    border-radius: 10px !important;
    padding: 10px;
}

/* ================= BUTTON ================= */
.stButton > button {
    background: linear-gradient(90deg, #3b82f6, #6366f1);
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 600;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(59,130,246,0.4);
}

/* ================= SPINNER ================= */
[data-testid="stSpinner"] {
    color: #ffffff !important;
    font-size: 18px !important;
}

/* ================= INFO BOX ================= */
div[data-testid="stInfo"] {
    background: linear-gradient(90deg, #1e3a8a, #1e40af) !important;
    border: 1px solid #3b82f6 !important;
    border-radius: 12px !important;
    padding: 18px !important;
}

div[data-testid="stInfo"] p {
    color: #ffffff !important;
    font-weight: 500;
}

/* ================= METRICS FIX ================= */
[data-testid="metric-container"] {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    padding: 22px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}

/* Metric LABEL (Python Files, Functions etc) */
[data-testid="metric-container"] label {
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}

/* Metric NUMBER */
[data-testid="metric-container"] div {
    color: #ffffff !important;
    font-size: 32px !important;
    font-weight: 800 !important;
}

/* ================= CODE BLOCK ================= */
.stCodeBlock {
    border-radius: 12px !important;
    border: 1px solid #334155 !important;
}

h3 {
    color: #ffffff !important;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)

# ----------------- Config -----------------
DB_PATH = "data/faiss_db"
REPO_DIR = "repos/temp_repo"

# ----------------- Session State -----------------
if "repo_indexed" not in st.session_state:
    st.session_state.repo_indexed = False

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

# ----------------- Helper Functions -----------------
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_repo(repo_url):
    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR, onerror=remove_readonly)
    subprocess.run(["git", "clone", repo_url, REPO_DIR], check=True)

def load_code_files():
    docs = []
    for root, _, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    docs.append({
                        "content": f.read(),
                        "metadata": {"source": path}
                    })
    return docs

def analyze_repository():
    total_files = total_functions = total_classes = entry_points = 0
    for root, _, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    total_functions += len(re.findall(r"def\s+\w+\(", content))
                    total_classes += len(re.findall(r"class\s+\w+", content))
                    entry_points += content.count('if __name__ == "__main__":')
    return total_files, total_functions, total_classes, entry_points

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("## 🔧 Repository Setup")

    repo_url = st.text_input("GitHub Repository URL")

    if st.button("Clone & Index Repo"):
        if repo_url.strip():
            try:
                with st.spinner("Cloning and indexing repository..."):
                    clone_repo(repo_url)

                    documents = load_code_files()
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=800,
                        chunk_overlap=100
                    )

                    chunks = splitter.create_documents(
                        [doc["content"] for doc in documents],
                        metadatas=[doc["metadata"] for doc in documents]
                    )

                    embeddings = HuggingFaceEmbeddings(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )

                    vectorstore = FAISS.from_documents(chunks, embeddings)
                    vectorstore.save_local(DB_PATH)

                    st.session_state.vectorstore = vectorstore
                    st.session_state.repo_indexed = True

                st.success("Repository Indexed Successfully ✅")

            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Enter a valid repository URL")

    if st.session_state.repo_indexed:
        st.markdown("---")
        st.markdown("## 🔍 Query Repository")
        query = st.text_input("Enter your query")

        if st.button("Run Query"):
            st.session_state.current_query = query

# ================= MAIN =================
st.markdown("""
<div class='hero-container'>
    <div class='main-title'>🧠 RAG-based Code Navigator</div>
    <div class='subtitle'>Semantic + Structural Code Intelligence Dashboard</div>
</div>
""", unsafe_allow_html=True)

if not st.session_state.repo_indexed:
    st.info("Use the sidebar to clone and index a repository.")
else:
    query = st.session_state.get("current_query", "")

    if query:
        if "analyze" in query.lower():
            files, functions, classes, entries = analyze_repository()

            st.markdown("### 📊 Repository Overview")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Python Files", files)
            col2.metric("Functions", functions)
            col3.metric("Classes", classes)
            col4.metric("Entry Points", entries)

        else:
            retriever = st.session_state.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            )
            docs = retriever.invoke(query)

            st.markdown("### 📁 Relevant Files")
            files = list(set(doc.metadata.get("source", "Unknown") for doc in docs))
            for f in files:
                st.write(f)

            st.markdown("### 💻 Code Preview")

            combined = ""
            for doc in docs:
                combined += doc.page_content + "\n\n"
                if len(combined) > 1500:
                    break

            st.code(combined[:1500], language="python")