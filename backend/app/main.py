"""FastAPI entry point."""

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from . import engine, pdf
from .config import settings
from .models import AnalyzeRequest, AnalyzeResponse, ExtractedText
from .scoring import postprocess

app = FastAPI(title="ATS Resume Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    analysis = engine.analyze(request.resume, request.job_description)
    return AnalyzeResponse(**postprocess(analysis, request.resume))


@app.post("/api/extract-text", response_model=ExtractedText)
async def extract_text(file: UploadFile) -> ExtractedText:
    """Turn an uploaded PDF into plain text for the resume or job description field."""
    data = await file.read(pdf.MAX_PDF_BYTES + 1)
    try:
        # PDF parsing is CPU-bound; keep it off the event loop.
        text, pages = await run_in_threadpool(pdf.extract_text, data)
    except pdf.PdfError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return ExtractedText(text=text, pages=pages)
