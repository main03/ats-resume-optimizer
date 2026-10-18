# ATS Resume Optimizer

Paste a resume and a job description. The app finds which job requirements the resume
already covers, which are underrepresented or missing, and suggests truthful
improvements, including ATS-friendly rewrites of existing bullets.

## Architecture

```
frontend/  Next.js + React + TypeScript (single page)
  app/page.tsx            inputs, loading/error state
  components/Report.tsx   score, keyword sections, recommendations, bullet rewrites
  lib/api.ts              API types + fetch client

backend/   FastAPI + Pydantic
  app/main.py             POST /api/analyze, GET /api/health
  app/models.py           request/response + LLM output schemas
  app/analyzer.py         one Claude call with structured (schema-enforced) output
  app/scoring.py          evidence verification + deterministic score
  tests/                  pytest (LLM mocked)
```

Flow: frontend → `POST /api/analyze` → one Claude call returns JSON matching
`LLMAnalysis` → `scoring.py` post-processes it → frontend renders the report.
No database, nothing stored.

### How the match score works

The LLM extracts the job's requirements (each one `required` or `preferred`) and labels
each as `matched`, `partial` or `missing`, quoting supporting resume text. The backend
then:

1. **Verifies evidence.** A quote not found in the resume is discarded, and a "matched"
   item without verifiable evidence is downgraded to "partial".
2. **Drops invented rewrites.** A bullet rewrite whose "original" isn't actually in the
   resume is removed.
3. **Scores deterministically.** `score = Σ(weight × credit) / Σ weight × 100`, with
   required = 3, preferred = 1, matched = 1, partial = 0.5, missing = 0.

The score measures keyword and requirement coverage only. It does not predict interviews.

## Running locally

Requirements: Python 3.12+ with [uv](https://docs.astral.sh/uv/), Node 20+, and an
[Anthropic API key](https://console.anthropic.com/).

**Backend** (port 8000):

```bash
cd backend
cp .env.example .env        # then set ANTHROPIC_API_KEY in .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**Frontend** (port 3000):

```bash
cd frontend
cp .env.local.example .env.local   # only needed if the backend isn't on localhost:8000
npm install
npm run dev
```

Open http://localhost:3000.

### Configuration (backend `.env`)

| Variable | Default | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | (none) | Required. Stays on the server. |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | |
| `ANTHROPIC_EFFORT` | `medium` | `low` is faster/cheaper, `high` more thorough. |
| `LLM_TIMEOUT_SECONDS` | `180` | |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated. |

Requests use Anthropic's server-side refusal fallback (`fallbacks: "default"`). If a
safety classifier declines a request, it is retried on a recommended model.

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck
```

## Input limits

Resume: 100–30,000 characters. Job description: 100–20,000 characters. These are
enforced in both the UI and the API (`app/models.py`).
