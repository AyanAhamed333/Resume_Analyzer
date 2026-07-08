import os
import re
import time
import logging
from typing import List, Any

import PyPDF2
import chromadb
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from groq import Groq

# --------------------------------------------------------------------------
# Logger Initialization
# --------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RAGChatbot")

# --------------------------------------------------------------------------
# Router Definition
# --------------------------------------------------------------------------
router = APIRouter()

# --------------------------------------------------------------------------
# Request & Response Schemas
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str = Field(..., description="The question to ask about the indexed resume.")

class ChatSource(BaseModel):
    page: int
    chunk: int
    section: str
    similarity: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = []

# --------------------------------------------------------------------------
# Global Singletons & Compatibility Interfaces
# --------------------------------------------------------------------------
_embedding_model = None
_chroma_client = None
_groq_client = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading local SentenceTransformer model: {model_name}")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model

def get_chroma_collection(reset: bool = False) -> Any:
    global _chroma_client
    if _chroma_client is None:
        db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        logger.info(f"Connecting to persistent Chroma database at: {db_path}")
        _chroma_client = chromadb.PersistentClient(path=db_path)
    
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "resume_collection")
    if reset:
        try:
            _chroma_client.delete_collection(collection_name)
            logger.info(f"Deleted old Chroma collection: {collection_name}")
        except Exception:
            pass
            
    return _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("GROQ_API_KEY environment variable is not configured.")
            raise ValueError("Groq API key missing. Please verify your environment configurations.")
        _groq_client = Groq(api_key=api_key)
    return _groq_client

# --------------------------------------------------------------------------
# PDF Processing, Parsing & Security Validations
# --------------------------------------------------------------------------
def validate_uploaded_pdf(file: UploadFile):
    """Applies security validators on file size, type, and format integrity."""
    if file.content_type != "application/pdf" or not file.filename.lower().endswith(".pdf"):
        raise ValueError("Invalid file format. Only PDF files (.pdf) are allowed.")

    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)

    max_file_size_mb = float(os.getenv("RAG_MAX_FILE_SIZE_MB", "5.0"))
    if size_bytes > max_file_size_mb * 1024 * 1024:
        raise ValueError(f"File size exceeds the maximum limit of {max_file_size_mb}MB.")

    try:
        pdf_reader = PyPDF2.PdfReader(file.file)
        _ = len(pdf_reader.pages)
        file.file.seek(0)
    except Exception as e:
        logger.error(f"Integrity check failed: PDF is corrupted or unreadable. Detail: {str(e)}")
        raise ValueError("The uploaded PDF file is corrupted or structurally invalid.")

def detect_section_header(text: str) -> str:
    """Detects which standard section heading this chunk belongs to."""
    sections = {
        "experience": ["experience", "work history", "employment history"],
        "education": ["education", "academic background", "degrees"],
        "skills": ["skills", "technical skills", "competencies", "expertise"],
        "projects": ["projects", "personal projects", "portfolio"],
        "certifications": ["certifications", "certs", "courses"],
        "summary": ["summary", "profile", "objective"]
    }
    text_lower = text.lower()
    for sec_name, keywords in sections.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                return sec_name.title()
    return "General"

def extract_and_chunk_pdf(file_stream) -> List[dict]:
    """Parses PDF page-by-page and extracts sentence-bounded text chunks with overlap."""
    pdf_reader = PyPDF2.PdfReader(file_stream)
    pages = []
    
    for page_idx, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append((page_idx + 1, text))
            
    if not pages:
        raise ValueError("Could not extract readable text from PDF pages.")

    chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "400"))
    chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "75"))
    chunks = []
    chunk_idx = 0

    for page_num, page_text in pages:
        # Split by sentence boundaries (.!?) or newlines (\n) to keep chunks clean
        sentences = re.split(r'(?:(?<=[.!?])\s+|\n+)', page_text.strip())
        current_chunk_sentences = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            s_words = sentence.split()
            s_len = len(s_words)
            if s_len == 0:
                continue
                
            if current_word_count + s_len > chunk_size and current_chunk_sentences:
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "chunk_id": chunk_idx,
                    "page_number": page_num,
                    "text": chunk_text,
                    "section": detect_section_header(chunk_text)
                })
                chunk_idx += 1
                
                # Backtrack to build the overlap list
                overlap_sentences = []
                overlap_word_count = 0
                for prev in reversed(current_chunk_sentences):
                    prev_len = len(prev.split())
                    if overlap_word_count + prev_len > chunk_overlap:
                        break
                    overlap_sentences.insert(0, prev)
                    overlap_word_count += prev_len
                
                current_chunk_sentences = overlap_sentences + [sentence]
                current_word_count = overlap_word_count + s_len
            else:
                current_chunk_sentences.append(sentence)
                current_word_count += s_len
                
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "chunk_id": chunk_idx,
                "page_number": page_num,
                "text": chunk_text,
                "section": detect_section_header(chunk_text)
            })
            chunk_idx += 1
            
    return chunks

# --------------------------------------------------------------------------
# REST API Endpoint: POST /upload-resume
# --------------------------------------------------------------------------
@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Endpoint to process PDF resumes, chunk, generate embeddings, and save to ChromaDB."""
    start_time = time.time()
    logger.info(f"Received resume upload request: {file.filename}")
    
    try:
        validate_uploaded_pdf(file)
        chunks = extract_and_chunk_pdf(file.file)
        
        model = get_embedding_model()
        chunk_texts = [c["text"] for c in chunks]
        embeddings = model.encode(chunk_texts, show_progress_bar=False).tolist()
        
        collection = get_chroma_collection(reset=True)
        ids = [f"chunk_{c['chunk_id']}" for c in chunks]
        metadatas = [
            {
                "chunk_id": c["chunk_id"],
                "page_number": c["page_number"],
                "section": c["section"],
                "source_filename": file.filename
            }
            for c in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=chunk_texts
        )
        
        elapsed_sec = time.time() - start_time
        logger.info(f"Resume indexed successfully in {elapsed_sec:.2f} seconds.")
        
        return {
            "status": "success",
            "message": "Resume indexed successfully",
            "chunks": len(chunks),
            "processing_time": f"{elapsed_sec:.1f} sec",
            "suggested_questions": [
                "What are my strongest skills?",
                "Summarize my resume.",
                "What projects have I completed?",
                "Which backend technologies do I know?",
                "How can I improve my resume?",
                "What jobs fit my profile?"
            ]
        }
        
    except ValueError as ve:
        logger.warning(f"Failed parsing PDF: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Uncaught exception indexing resume: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing resume upload.")

# --------------------------------------------------------------------------
# REST API Endpoint: POST /chat
# --------------------------------------------------------------------------
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG-grounded chat endpoint using similarity thresholding and Groq SDK."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    logger.info(f"Incoming query: '{question}'")
    
    try:
        collection = get_chroma_collection()
        if collection.count() == 0:
            return ChatResponse(
                answer="No resume has been uploaded yet. Please upload a PDF resume first.",
                sources=[]
            )
            
        model = get_embedding_model()
        q_emb = model.encode(question, show_progress_bar=False).tolist()
        
        max_retrieved = int(os.getenv("RAG_MAX_RETRIEVED_CHUNKS", "5"))
        results = collection.query(
            query_embeddings=[q_emb],
            n_results=min(max_retrieved, collection.count())
        )
        
        similarity_threshold = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.2"))
        
        # Bypass threshold for generic document-level summaries
        is_generic = any(kw in question.lower() for kw in ["summarize", "summary", "overview", "resume", "profile", "about", "who is", "entire"])
        if is_generic:
            similarity_threshold = 0.0
            
        valid_chunks = []
        sources = []
        
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            
            for doc_text, distance, meta in zip(docs, dists, metas):
                similarity = 1.0 - distance
                if similarity >= similarity_threshold:
                    valid_chunks.append(doc_text)
                    sources.append(ChatSource(
                        page=int(meta.get("page_number", 1)),
                        chunk=int(meta.get("chunk_id", 0)),
                        section=meta.get("section", "General"),
                        similarity=float(round(similarity, 4))
                    ))
                    
        if not valid_chunks:
            return ChatResponse(
                answer="I couldn't find that information in the uploaded resume.",
                sources=[]
            )
            
        full_context_str = "\n\n---\n\n".join(valid_chunks)
        
        system_prompt = (
            "You are an AI Resume Assistant.\n\n"
            "Rules:\n"
            "- Base your answers strictly on the retrieved resume context. Do not invent achievements, experiences, or skills that are not present.\n"
            "- If specific factual information about the candidate is missing, clearly say so: \"I couldn't find that information in the uploaded resume.\"\n"
            "- Keep answers concise.\n"
            "- Quote resume information when useful.\n"
            "- Use bullet points when appropriate."
        )
        
        groq_client = get_groq_client()
        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{full_context_str}\n\nQuestion:\n{question}\n\nResponse:"}
            ],
            model=model_name,
            temperature=0.0,
            max_tokens=1024
        )
        
        answer = completion.choices[0].message.content or "I couldn't find that information in the uploaded resume."
        answer_stripped = answer.strip()
        
        # Clear sources if LLM refuses/indicates info not found
        lowered_ans = answer_stripped.lower()
        refusal_keywords = [
            "couldn't find", 
            "could not find", 
            "not mentioned", 
            "not found", 
            "no information", 
            "not present"
        ]
        if any(kw in lowered_ans for kw in refusal_keywords):
            sources = []
            
        return ChatResponse(
            answer=answer_stripped,
            sources=sources
        )
        
    except ValueError as ve:
        logger.warning(f"Validation failure in chat request: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Uncaught exception executing RAG chat: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error processing the chat question."
        )
