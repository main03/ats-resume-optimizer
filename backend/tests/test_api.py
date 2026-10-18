from fastapi.testclient import TestClient

from app import analyzer, main
from app.models import LLMAnalysis

client = TestClient(main.app)

RESUME = "Senior engineer.\n- Built REST APIs in Python with FastAPI for a payments platform.\n" + "x" * 100
JOB = "We need a backend engineer with Python, FastAPI and Kubernetes experience. " + "y" * 100

FAKE_ANALYSIS = LLMAnalysis.model_validate({
    "role_title": "Backend Engineer",
    "requirements": [
        {"term": "Python", "category": "technical_skill", "importance": "required",
         "status": "matched", "resume_evidence": "REST APIs in Python", "note": ""},
        {"term": "Kubernetes", "category": "tool", "importance": "required",
         "status": "missing", "resume_evidence": "", "note": ""},
    ],
    "highlights": [],
    "recommendations": [
        {"section": "skills", "priority": "low", "suggestion": "a", "rationale": ""},
        {"section": "summary", "priority": "high", "suggestion": "b", "rationale": ""},
    ],
    "rewritten_bullets": [
        {"original": "Built REST APIs in Python with FastAPI for a payments platform.",
         "improved": "Built Python REST APIs with FastAPI for a payments platform.",
         "keywords_used": ["Python", "FastAPI"]},
    ],
})


def test_analyze_returns_scored_report(monkeypatch):
    async def fake_analyze(resume, job_description):
        return FAKE_ANALYSIS

    monkeypatch.setattr(analyzer, "analyze", fake_analyze)
    res = client.post("/api/analyze", json={"resume": RESUME, "job_description": JOB})

    assert res.status_code == 200
    body = res.json()
    assert body["score"]["score"] == 50
    assert [r["priority"] for r in body["recommendations"]] == ["high", "low"]
    assert len(body["rewritten_bullets"]) == 1


def test_short_input_is_rejected():
    res = client.post("/api/analyze", json={"resume": "too short", "job_description": JOB})
    assert res.status_code == 422


def test_analysis_error_is_returned_as_detail(monkeypatch):
    async def failing_analyze(resume, job_description):
        raise analyzer.AnalysisError("The AI service is busy.", 429)

    monkeypatch.setattr(analyzer, "analyze", failing_analyze)
    res = client.post("/api/analyze", json={"resume": RESUME, "job_description": JOB})
    assert res.status_code == 429
    assert res.json() == {"detail": "The AI service is busy."}
