import os
import sys

# Workaround for protobuf descriptors error with older tensorflow versions
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Monkeypatches for compatibility with torch 2.0.1 and transformers 4.50+
try:
    import torch
    
    # 1. Mock torch.compiler
    if not hasattr(torch, "compiler"):
        class MockCompiler:
            @staticmethod
            def disable(recursive=False):
                def decorator(func):
                    return func
                return decorator
        torch.compiler = MockCompiler
        
    # 2. Patch nn.Module.load_state_dict to ignore 'assign' keyword
    import torch.nn
    original_load = torch.nn.Module.load_state_dict
    
    def patched_load(self, *args, **kwargs):
        kwargs.pop('assign', None)
        return original_load(self, *args, **kwargs)
        
    torch.nn.Module.load_state_dict = patched_load
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import PyPDF2
from dotenv import load_dotenv

# Load environment variables at startup
load_dotenv()

from database import init_db, insert_history, get_history
from analyzer import analyze_resume
from backend.rag import router as rag_router

# Create app FIRST
app = FastAPI()

# Register new RAG endpoints router
app.include_router(rag_router)

# THEN mount static
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

init_db()

# -----------------------------
# Request Schema
# -----------------------------

class AnalyzeRequest(BaseModel):
    resume_text: str
    role: str = ""
    jd_text: str = ""

# -----------------------------
# Routes
# -----------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):

    resume_text = data.resume_text.strip()
    role = data.role.strip()
    jd_text = data.jd_text.strip()

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Resume text is empty"
        )

    if not role and not jd_text:
        raise HTTPException(
            status_code=400,
            detail="Please select a role or provide a Job Description"
        )

    analysis_result = analyze_resume(
        resume_text,
        role,
        jd_text
    )

    if not analysis_result:
        raise HTTPException(
            status_code=400,
            detail="Invalid role or unable to analyze"
        )

    # Store history
    insert_history(
        role if role else "Custom JD",
        analysis_result["score"]
    )

    # Resume analyzed successfully, return result

    return analysis_result

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF file."
        )

    try:

        pdf_reader = PyPDF2.PdfReader(file.file)

        extracted_text = ""

        for page in pdf_reader.pages:
            text = page.extract_text()

            if text:
                extracted_text += text + "\n"

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF. It may be image-based."
            )

        return {
            "text": extracted_text
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error reading PDF: {str(e)}"
        )

@app.get("/history")
async def history():

    records = get_history()

    return records