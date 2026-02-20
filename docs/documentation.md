# RAG Code Navigator Documentation

## 1. Overview

RAG Code Navigator is a Streamlit-based application that allows users to:

- Analyze GitHub repositories
- Extract Python files
- Detect functions and classes
- Identify entry points
- Perform semantic search over code using FAISS
- Ask natural language queries about the codebase

---

## 2. Architecture

### Components:

1. Streamlit UI (app.py)
2. Repository Cloner
3. Code Parser
4. Text Splitter (LangChain)
5. Embedding Model (Sentence Transformers)
6. Vector Store (FAISS)
7. Query Engine

---

## 3. Workflow

1. User enters GitHub repository URL
2. Repository is cloned locally
3. Python files are extracted
4. Code is chunked into documents
5. Embeddings are created
6. FAISS index is built
7. User asks questions about the code
8. Similar chunks are retrieved
9. Response is generated

---

## 4. Technologies Used

- Streamlit
- LangChain
- FAISS
- Sentence Transformers
- Git
- Python

---

## 5. Folder Structure

rag-code-navigator/
│
├── app.py
├── requirements.txt
├── screenshots/
├── docs/
│   └── documentation.md
├── .gitignore

---

## 6. Future Improvements

- Multi-language support
- AST-based code analysis
- Code summarization
- Deploy on Streamlit Cloud