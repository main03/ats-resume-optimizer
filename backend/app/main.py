"""FastAPI entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import analyzer, engine
from .config import settings
from .models import AnalyzeRequest, AnalyzeResponse
from .scoring import postprocess

app = FastAPI(title="ATS Resume Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(analyzer.AnalysisError)
async def analysis_error_handler(_, exc: analyzer.AnalysisError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "engine": "claude" if settings.use_claude else "builtin"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    if settings.use_claude:
        analysis = await analyzer.analyze(request.resume, request.job_description)
        engine_name = "claude"
    else:
        analysis = engine.analyze(request.resume, request.job_description)
        engine_name = "builtin"
    return AnalyzeResponse(engine=engine_name, **postprocess(analysis, request.resume))
