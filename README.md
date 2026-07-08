# 📄 Smart Resume Analyzer & RAG Chatbot

An aesthetic, full-stack web application designed for resume analysis and semantic querying. The project features a deterministic ATS scoring engine alongside a local Retrieval-Augmented Generation (RAG) conversational assistant. 

The interface features a **cute, handdrawn notebook-style pastel UI** complete with decorative post-it notes, background blobs, and playful doodle outlines.
---

## ✨ Features

### 1. 📊 Resume Analyzer Dashboard
* **Score matching**: Compares resumes against specific job roles (Backend, Data Analyst, HR, Sales, etc.) using a weighted checklist matching algorithm.
* **Custom Job Descriptions**: Automatically extracts key keywords from any pasted Job Description to evaluate candidate fit.
* **ATS Improvement Engine**: Evaluates CV length, scans for strong action verbs, and verifies if achievements are quantified with metrics.
* **Persistent History**: Saves matching statistics in a local SQLite database and plots historical scores in the dashboard.

### 2. 💬 Chat with Resume (RAG Chatbot)
* **Local Embeddings**: Generates 384-dimensional dense vectors using a local CPU-efficient embedding model (`all-MiniLM-L6-v2`).
* **Vector Store**: Indexes and runs cosine similarity queries using an embedded, persistent **ChromaDB** collection.
* **Optimized Chunker**: Features a custom line-aware chunker (`RAG_CHUNK_SIZE=120`, `RAG_CHUNK_OVERLAP=25`) designed specifically for list-heavy, line-oriented resumes.
* **Fast LLM Responses**: Leverages the **Groq Llama-3.1-8b** model for lightning-fast, grounded responses.
* **Factual Grounding**: Implements a strict similarity filter (`similarity >= 0.15`). Out-of-scope or irrelevant queries automatically trigger a clean refusal, eliminating hallucinations.

### 🎨 The UI Aesthetic
* Handdrawn outlines, pencil textures, and playful doodles.
* Light notebook grid backgrounds decorated with colorful motivational sticky notes (*"trust the process"*, *"progress over perfection"*).
* Beautiful pastel-colored cards, animated match score progress bars, and neat tab-switching transitions.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI (Python), PyPDF2 (PDF parsing), SentenceTransformers (Embeddings), ChromaDB (Vector DB), SQLite (History storage)
* **Frontend**: Semantic HTML5, CSS3 Custom Variables (Aesthetic styling), Vanilla JavaScript (DOM manipulation & Fetch API)
* **LLM Provider**: Groq API (Llama-3.1-8b-instant)

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/intelligent-resume-rag-analyzer.git
cd intelligent-resume-rag-analyzer
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root folder:
```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Local Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Database configuration
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=resume_collection

# RAG Chunker Configuration
RAG_CHUNK_SIZE=120
RAG_CHUNK_OVERLAP=25

# RAG Security & Retrieval Configuration
RAG_MAX_FILE_SIZE_MB=5.0
RAG_SIMILARITY_THRESHOLD=0.15
RAG_MAX_RETRIEVED_CHUNKS=5
RAG_MAX_HISTORY_TURNS=5
```

### 5. Run the Application
```bash
uvicorn app:app --port 5000 --reload
```
Open **`http://localhost:5000`** in your browser and try it out!

---

## 📁 Project Structure
```text
├── backend/
│   └── rag.py          # RAG endpoints (ChromaDB + SentenceTransformers + Groq API)
├── static/
│   ├── bg.png          # Aesthetic UI background grid asset
│   ├── script.js       # UI Event handler, Fetch routing, and Markdown parser
│   └── style.css       # Pastel theme, handdrawn variables, sticky note positioning
├── templates/
│   └── index.html      # Responsive Single Page dashboard layout
├── analyzer.py         # Keyword extracting and ATS suggestions engine
├── app.py              # Main FastAPI application & routers
├── database.py         # SQLite connection and historical records management
├── requirements.txt    # Project dependencies list
└── .gitignore          # Git exclusion definitions
```

---

## 📄 Documentation
For detailed explanations of files, functions, vector embeddings, and an extensive list of 100+ interview questions, check out our [Comprehensive Interview Mentor Guide](comprehensive_interview_mentor_guide.md).
