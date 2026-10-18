# ATS Resume Optimizer

Paste a resume and a job description. The app finds which job requirements the resume
already covers, which are underrepresented or missing, and suggests truthful
improvements, including ATS-friendly rewrites of existing bullets.

It works **offline with no API key** using a built-in rule-based engine. If you set an
`ANTHROPIC_API_KEY`, it switches to Claude for deeper analysis and full bullet rewrites.

## Architecture

```
frontend/  Next.js + React + TypeScript (single page)
  app/page.tsx            inputs, loading/error state
  components/Report.tsx   score, keyword sections, recommendations, bullet rewrites
  lib/api.ts              API types + fetch client

backend/   FastAPI + Pydantic
  app/main.py             POST /api/analyze, GET /api/health
  app/models.py           request/response + analysis schemas
  app/engine/             built-in analyzer (default, no API key)
    job.py                job description -> requirements (sections, required/preferred)
    resume.py             resume sections + years of experience from date ranges
    skills.py             keyword search over data/skills.json
    match.py              matched / partial / missing per requirement
    advice.py             recommendations, highlights, wording-swap rewrites
  app/data/skills.json    skills dictionary with synonyms (edit to extend)
  app/analyzer.py         Claude analyzer (used only when ANTHROPIC_API_KEY is set)
  app/scoring.py          evidence verification + deterministic score
  tests/                  pytest (Claude mocked)
```

Flow: frontend → `POST /api/analyze` → the built-in engine (or Claude, if a key is set)
produces an `Analysis` → `scoring.py` verifies it and computes the score → frontend
renders the report. No database, nothing stored.

### Built-in engine

1. **Job description.** Detects sections ("Requirements", "Nice to have",
   "Responsibilities"; "About us" and "Benefits" are ignored). Each keyword is marked
   required or preferred from its section and cues like "a plus" or "must". Also extracts
   years of experience, degree level, unknown acronyms (e.g. HIPAA) and responsibility
   bullets.
2. **Resume.** Splits into sections (Summary, Experience, Skills, Education…) and adds up
   the date ranges of your roles, merging overlaps.
3. **Matching.**
   - **matched:** the posting's wording appears in your experience, projects or summary.
   - **partial:** the term appears only in a skills list, under a synonym (k8s vs
     Kubernetes), or as a related term (CI vs CI/CD).
   - **missing:** not found.

   Responsibilities are matched by word overlap with your bullets. Because that is
   approximate, they always count as preferred (1×) in the score.
4. **Advice.** Template-based recommendations plus resume-quality checks (weak openers,
   bullets without numbers, Unicode "bold" letters ATS can't read). Rewrites only swap the
   posting's wording in for **true synonyms** (`k8s` → `Kubernetes (k8s)`), so they can't
   add anything untrue. Related terms (marked `~` in `skills.json`) are never swapped.

To teach the engine new skills, add them to `backend/app/data/skills.json`. The format is
described at the top of that file.

### How the match score works

The analyzer (built-in or Claude) extracts the requirements (`required` or `preferred`), labels
each `matched`, `partial` or `missing` and quotes supporting resume text. The backend
then:

1. **Verifies evidence.** A quote not found in the resume is discarded, and a "matched"
   item without verifiable evidence is downgraded to "partial".
2. **Drops invented rewrites.** A bullet rewrite whose "original" isn't actually in the
   resume is removed.
3. **Scores deterministically.** `score = Σ(weight × credit) / Σ weight × 100`, with
   required = 3, preferred = 1, matched = 1, partial = 0.5, missing = 0.

The score measures keyword and requirement coverage only. It does not predict interviews.

## Running locally

Requirements: Python 3.12+ with [uv](https://docs.astral.sh/uv/) and Node 20+. An
[Anthropic API key](https://console.anthropic.com/) is optional.

**Backend** (port 8000):

```bash
cd backend
cp .env.example .env        # optional: set ANTHROPIC_API_KEY to use Claude
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
| `ANTHROPIC_API_KEY` | (none) | Optional. If set, Claude is used instead of the built-in engine. Stays on the server. |
| `ANTHROPIC_MODEL` | `claude-opus-5-5` | |
| `ANTHROPIC_EFFORT` | `medium` | `low` is faster/cheaper, `high` more thorough. |
| `LLM_TIMEOUT_SECONDS` | `180` | |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated. |

With a key set, requests use Anthropic's server-side refusal fallback (`fallbacks: "default"`). If a
safety classifier declines a request, it is retried on a recommended model.

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck
```

## Input limits

Resume: 100–30,000 characters. Job description: 100–20,000 characters. These are
enforced in both the UI and the API (`app/models.py`).
