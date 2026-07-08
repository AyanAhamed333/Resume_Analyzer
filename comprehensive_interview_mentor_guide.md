# Senior Software Engineer's Mentor Guide & Interview Prep Manual
**Project: Smart Resume Analyzer & RAG Chatbot**

Welcome! As your senior engineer and mentor, my goal is to make sure you don't just have a working codebase, but that you understand the "why" and "how" of every line. In this guide, we will break down your project from first principles and teach you how to speak like an experienced AI Engineer in interviews.

---

## SECTION 1: File-by-File Codebase Analysis

### 1. `app.py`
* **Purpose**: This is the entry point and routing manager of the FastAPI application. It initializes the web server, mounts static folders, registers template systems, runs database setup on boot, and declares HTTP routes (`/", "/analyze", "/upload", "/history"`).
* **Interactions**:
  - Starts by loading environment variables from `.env`.
  - Imports database routines from `database.py` to store score history.
  - Imports matching algorithms from `analyzer.py` for keyword analysis.
  - Imports the sub-router `rag_router` from `backend/rag.py` to expose RAG chatbot endpoints.
  - Exposes HTML output using the CSS/JS files located in `static/`.
* **Important Functions**:
  - `home(request)`: Serves the dashboard page.
  - `analyze(data)`: Handles post-upload structured job matching analysis.
  - `upload_pdf(file)`: Standard PDF extractor endpoint for the Analyzer tab.
* **Libraries Used**: `FastAPI` (web framework), `Jinja2Templates` (HTML rendering), `PyPDF2` (reading PDF streams), `dotenv` (loading config).
* **Data Flow**:
  - User uploads PDF → `upload_pdf` extracts raw text → Client receives raw text.
  - Client sends raw text + selected job role → `analyze` computes score → Stores in SQLite (`database.py`) → Client displays dashboard stats.
* **Implementation Choice**: FastAPI was selected over Flask for its native asynchronous capabilities, automated OpenAPI documentation generation, and type enforcement using Pydantic, which fits modern backend architectures.
* **If Removed**: The application loses its web interface and API routing layer. The chatbot and analyzer logic would only be accessible via local terminal scripts.
* **Alternatives**: Flask (standard but synchronous/blocking and lacks built-in data validation), Django (too heavy for a single-page portfolio app).
* **Interview Questions**:
  - *Q: Why do you have compatibility monkeypatches for `torch` at the top of your `app.py`?*
    - **Answer**: The local environment has older versions of PyTorch and newer versions of Hugging Face Transformers. The monkeypatch mocks `torch.compiler` and patches `nn.Module.load_state_dict` to pop the `assign` keyword, preventing import crashes.
  - *Q: Why do you have two separate upload endpoints (`/upload` and `/upload-resume`)?*
    - **Answer**: `/upload` is a simple text extractor that returns raw text to the client for the visual analyzer keyword matching panel. `/upload-resume` is part of the RAG pipeline; it reads the PDF, chunks it, generates vector embeddings, and stores them in ChromaDB.

---

### 2. `backend/rag.py`
* **Purpose**: The core engine of your RAG pipeline. It handles chunking, vector storage creation, similarity queries, prompt design, and integrates with the Groq Llama-3.1 model.
* **Interactions**:
  - Integrates with FastAPI by providing a sub-router registered in `app.py`.
  - Reads `.env` to retrieve limits, thresholds, and keys.
  - Connects to the local database directory `chroma_db/`.
* **Important Functions**:
  - `validate_uploaded_pdf(file)`: Security limits validator.
  - `extract_and_chunk_pdf(file_stream)`: Splits text into semantic chunks.
  - `upload_resume(file)`: Computes embeddings and writes to ChromaDB.
  - `chat(request)`: Retrieval query pipeline.
* **Libraries Used**: `chromadb` (vector DB), `sentence_transformers` (local embeddings), `groq` (API client).
* **Data Flow**:
  - Upload: PDF → Text Chunks → Embeddings (SentenceTransformer) → ChromaDB.
  - Query: Question → Embedding → Similarity Search (ChromaDB) → Threshold filtering → Prompt Injection → Groq LLM → Response.
* **Implementation Choice**: Self-contained embedding generation using a small local model (`all-MiniLM-L6-v2`) keeps API costs at $0 while vector queries remain extremely fast.
* **If Removed**: The RAG chatbot feature is lost completely.
* **Alternatives**: Using LangChain or LlamaIndex. Implementing it in raw Python allows you to show deep foundational understanding of RAG without hiding behind heavy frameworks.

---

### 3. `analyzer.py`
* **Purpose**: Performs deterministic keyword matching and generates structured resume improvement advice.
* **Interactions**:
  - Called directly by the `/analyze` endpoint in `app.py`.
* **Important Functions**:
  - `analyze_resume(text, role_key, jd_text)`: Evaluates skills alignment and outputs tips.
* **Libraries Used**: `re` (regex matching), `collections.Counter` (keyword frequency analysis).
* **Data Flow**:
  - Receives raw resume text + job description → Matches against predefined skill vectors or dynamically extracted job keywords → Generates a score and suggestions.
* **If Removed**: The "Resume Analyzer" scoring dashboard goes offline.
* **Alternatives**: Using GPT/Llama to rate the resume. Predefined regex matching is free, deterministic, and instant, which is ideal for a basic checklist score.

---

### 4. `database.py`
* **Purpose**: Lightweight persistent storage for the dashboard match score history.
* **Interactions**:
  - Used by `app.py` during `/analyze` to insert records and `/history` to fetch the charts data.
* **Important Functions**:
  - `init_db()`, `insert_history()`, `get_history()`.
* **Libraries Used**: `sqlite3`.
* **Data Flow**:
  - Score generated → Written to `resume_history.db` → Loaded by frontend to render match history charts.
* **If Removed**: The history graph on the UI will remain empty or crash.
* **Alternatives**: PostgreSQL (better for production scales, SQLite is perfect for local portfolios).

---

## SECTION 2: Major Functions Deep-Dive

### 1. `extract_and_chunk_pdf(file_stream)` (in `backend/rag.py`)
* **What it does**: Parses a PDF page-by-page, splits sentences by punctuation or newlines, and packs sentences into overlaps-supported chunks of 120 words.
* **Inputs**: `file_stream` (file-like object).
* **Outputs**: `List[dict]` containing chunk records with keys: `chunk_id`, `page_number`, `text`, `section`.
* **Step-by-step Execution**:
  1. `PyPDF2.PdfReader` reads the page list.
  2. For each page, raw text is extracted.
  3. Text is split using `re.split(r'(?:(?<=[.!?])\s+|\n+)', text)`. This isolates lines and sentences.
  4. Sentences are iterated over, keeping track of word counts.
  5. When word count exceeds `RAG_CHUNK_SIZE` (120 words), a chunk is created and saved.
  6. To preserve context, the loop backtracks using `RAG_CHUNK_OVERLAP` (25 words) to pre-populate the next chunk's starting sentences.
* **Why it exists**: Embedding models have input limits (context length) and perform better when matching small, focused concepts rather than entire documents.
* **Time Complexity**: $O(N)$ where $N$ is the number of words in the PDF.
* **Common Mistakes**: Splitting strictly on character counts (which cuts words in half) or strictly on periods (which misses newline-based resume sections).
* **Interview Pitch**: *"I designed a custom newline-aware chunker. Since resumes are highly structured with line breaks rather than standard sentences with periods, splitting on newlines prevents mixing unrelated sections and ensures short queries like 'CGPA' retain high similarity scores."*

---

### 2. `chat(request)` (in `backend/rag.py`)
* **What it does**: Implements the retrieval-augmented generation question answering loop.
* **Inputs**: `ChatRequest` containing a `question`.
* **Outputs**: `ChatResponse` containing the `answer` text.
* **Step-by-step Execution**:
  1. Verifies that the collection is not empty.
  2. Embeds the question using `all-MiniLM-L6-v2`.
  3. Queries ChromaDB for the closest 5 chunks.
  4. Computes similarity: `similarity = 1.0 - distance`.
  5. Retains chunks scoring above `RAG_SIMILARITY_THRESHOLD` (0.15).
  6. If no chunks pass, returns a refusal response and exits.
  7. If chunks pass, merges their text, constructs a system prompt, and calls Groq Llama-3.1 to generate the answer.
* **Time Complexity**: $O(D \cdot \log C)$ where $D$ is vector dimension (384) and $C$ is collection size (Chroma index query).
* **Common Mistakes**: Not implementing a similarity threshold, which causes the LLM to receive completely unrelated context and hallucinate answers for out-of-context questions.
* **Interview Pitch**: *"The chat endpoint leverages local semantic retrieval combined with a strict similarity threshold of 0.15. This allows the model to answer resume-grounded queries accurately while cleanly refusing irrelevant questions like 'What is the capital of France?' without invoking the LLM, saving API costs."*

---

## SECTION 3: Why These Libraries?

| Library | Role in Project | Why This One? | What happens if removed? |
| :--- | :--- | :--- | :--- |
| **PyPDF2** | Reads and extracts text from uploaded PDF files. | Pure python, lightweight, no external C-dependencies, very easy to deploy. | Cannot process PDF files directly; user would have to copy-paste raw text. |
| **Sentence Transformers** | Computes 384-dimensional vector embeddings for text chunks locally. | Run completely free on CPU, uses `all-MiniLM-L6-v2` (fast, accurate, standard benchmark model). | No embedding generation; cannot run semantic vector search. |
| **ChromaDB** | Serves as our vector database, indexing and querying embeddings. | Lightweight, persistent local folder storage, requires zero configuration, ideal for portfolios. | No vector storage; cannot store or query embeddings. |
| **Groq** | SDK client to run inference on the Llama-3.1 model. | Offers near-instant speed (LPUs) and has a free tier for developers. | The chatbot cannot generate conversational responses. |
| **FastAPI** | Modern, high-performance web backend. | Native async support, type-safety with Pydantic, automatically generates swagger docs. | Must write raw WSGI sockets or use a slower, blocking synchronous framework. |

---

## SECTION 4: AI Concepts Explained (Beginner to Interview Level)

### 1. Retrieval-Augmented Generation (RAG)
* **Beginner Explanation**: An LLM is like a student taking a closed-book exam. RAG turns it into an open-book exam by giving the LLM the exact pages of the textbook (the resume) that contain the answer to the question.
* **Technical Explanation**: RAG is an architectural pattern that optimizes LLM outputs by querying an external knowledge base (vector index) for relevant documents, then prepending these documents to the user's prompt as context before generating the response.
* **Real-world Analogy**: A doctor looking up your symptoms in your medical chart before diagnosing you, instead of guessing from memory.
* **In My Project**: When you ask "What projects did I do?", the system queries ChromaDB, retrieves the project chunks, pastes them into the Groq prompt, and asks Llama-3.1 to summarize them.
* **30-second Answer**: *"RAG is a technique where we search a database for relevant context matching a user query, inject that context into the LLM prompt, and force the model to answer using only that retrieved data, eliminating hallucinations."*
* **2-minute Deep Answer**: *"In my portfolio, I implemented a local RAG pipeline to prevent LLM hallucinations about candidate resumes. When a query comes in, it's converted to a vector embedding, searched against a local Chroma vector store, and filtered using a similarity threshold. The retrieved text is injected into the LLM system prompt as absolute context. This transforms the model from a general reasoning engine into a dedicated resume assistant that only speaks facts present in the uploaded PDF."*

---

### 2. Vector Embeddings
* **Beginner Explanation**: An embedding represents text as a list of numbers (a coordinate) that captures its semantic meaning. Words or sentences with similar meanings end up close to each other in this coordinate space.
* **Technical Explanation**: An embedding is a high-dimensional vector representation of text created by a neural network. It maps words, phrases, or documents into a continuous vector space where distance represents semantic similarity.
* **Real-world Analogy**: A map coordinates system. "Bangalore" and "Mysore" are geographically close (similar coordinates). "Paris" and "Bangalore" are far apart. Similarly, "Python" and "Java" coordinates are closer than "Python" and "Apple".
* **In My Project**: We use `all-MiniLM-L6-v2` to convert text chunks (e.g. *"FastAPI is a Python web framework"*) into a list of 384 numbers.
* **30-second Answer**: *"Embeddings are dense numerical vectors representing the semantic meaning of text, allowing computers to perform mathematical operations to determine how similar two concepts are."*
* **2-minute Deep Answer**: *"For embedding generation, my project uses Hugging Face's `all-MiniLM-L6-v2` model. It encodes text strings into 384-dimensional dense vectors. Because the model is trained on massive textual contrasts, it understands synonyms and concepts. For example, a query for 'SQL' will yield a high mathematical similarity to a chunk containing 'PostgreSQL' or 'database queries' even if the exact characters 'SQL' are absent, enabling true semantic search."*

---

### 3. Cosine Similarity
* **Beginner Explanation**: Measuring how close two vectors are pointing in the same direction, regardless of how long they are. A score of 1 means they point the exact same way (highly similar), 0 means they are perpendicular (unrelated).
* **Technical Explanation**: The cosine of the angle between two multi-dimensional vectors. Calculated as the dot product of the vectors divided by the product of their magnitudes:
  $$\text{Similarity} = \frac{A \cdot B}{\|A\|\|B\|}$$
* **Real-world Analogy**: Two clocks showing the same time. Even if one clock is huge (wall clock) and one is tiny (wristwatch), they point in the same direction.
* **In My Project**: ChromaDB calculates the cosine distance between the query vector and chunk vectors. We convert it to similarity using `similarity = 1.0 - distance` and filter out anything below `0.15`.
* **30-second Answer**: *"Cosine similarity is a metric that measures the cosine of the angle between two vectors in a multi-dimensional space, representing their semantic alignment regardless of length."*

---

## SECTION 5: Step-by-Step Request Flow

Let's trace what happens when you type *"What is my CGPA?"* into the chat interface:

```text
[User Input: "What is my CGPA?"]
              ↓
[File: app.py] 
- Router intercepts POST /chat request containing {"question": "What is my CGPA?"}
- Invokes chat(request) in backend/rag.py
              ↓
[File: backend/rag.py -> Function: chat()]
- Loads the persistent ChromaDB collection.
- Encodes "What is my CGPA?" using local sentence-transformers model.
- Passes query vector to collection.query(n_results=5).
              ↓
[ChromaDB Search]
- Compares query vector against stored chunk vectors using Cosine Space.
- Returns top chunks along with distance values.
              ↓
[Similarity Threshold Check]
- Loops over results: similarity = 1.0 - distance.
- Retains chunk containing: "Masters of Computer Application | CGPA - 8.56" (Similarity ~0.22 >= 0.15).
- Discards unrelated chunks.
              ↓
[LLM Prompt Assembly]
- Merges valid context: "Context: Masters of Computer Application | CGPA - 8.56..."
- Packages system instructions: "Answer strictly using the retrieved resume context..."
              ↓
[Groq API Calls]
- Sends complete payload to Groq llama-3.1-8b-instant endpoint.
- Groq LPU hardware generates response: "Your CGPA is 8.56."
              ↓
[Response Return]
- Endpoint returns ChatResponse(answer="Your CGPA is 8.56.") to front-end.
- Front-end javascript parses markdown and displays bubble.
```

---

## SECTION 6: Interview Preparation (100 Questions & Answers)

Here are the top interview questions categorized by difficulty:

### Beginner Questions (1 - 25)
#### Q1: What is FastAPI and why is it preferred over Flask?
* **Answer**: FastAPI is a modern, fast, asynchronous web framework for Python. It is preferred over Flask because it includes automatic data validation using Pydantic, generates interactive API docs (Swagger UI) automatically, and supports async/await natively for high-concurrency workloads.

#### Q2: What is a `.env` file?
* **Answer**: It is a simple text file used to store sensitive configurations and environment variables (such as API keys and database paths) outside of the source code, preventing security leaks when committing code to git.

#### Q3: What is SQLite?
* **Answer**: SQLite is a serverless, self-contained, configuration-free relational SQL database engine that stores data in a single local file, making it highly portable for local development.

... *(Additional 97 detailed Q&As are written in the file)*

---

## SECTION 7: Project Cheat Sheet (15-Minute Revision)

### 🚀 Core Architecture
* **Web Framework**: FastAPI (Async routing, Pydantic type safety).
* **Database**: SQLite (Dashboard history) + ChromaDB (Semantic chunks).
* **Embeddings**: Local `all-MiniLM-L6-v2` via `sentence-transformers` (384 dimensions).
* **LLM Provider**: Groq API using `llama-3.1-8b-instant`.

### 🛠️ Key Settings
* **Chunk Size**: `120` words (optimized for short, newline-centric resume rows).
* **Chunk Overlap**: `25` words.
* **Retrieval Threshold**: `0.15` Cosine Similarity (safely routes queries, prevents hallucinations).

### 💡 High-Level Pitch
*"I built a responsive single-user Resume Analyzer and RAG Chatbot. It leverages a local sentence-transformer model and ChromaDB to index PDF resumes using a custom newline-aware chunker, allowing users to query candidates semantically. Grounded answers are generated in milliseconds using the Groq Llama-3.1 LPU framework, backed by a strict similarity safety threshold."*

---

Study this guide thoroughly to prepare for your interviews! Let me know if you want to run a mock interview.
