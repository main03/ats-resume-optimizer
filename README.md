# ATS Resume Optimizer

Paste a resume and a job description. The app finds which job requirements the resume
already covers, which are underrepresented or missing, and suggests truthful
improvements, including ATS-friendly wording for existing bullets.

Everything runs locally with a custom rule-based analysis engine. There are no external
APIs, no API keys, and no database. Nothing you paste is stored or sent anywhere.

## Architecture

```
frontend/  Next.js + React + TypeScript (single page)
  app/page.tsx            inputs, loading/error state
  components/Report.tsx   score, keyword lists (found / different / missing), to-do list
  lib/api.ts              API types + fetch client

backend/   FastAPI + Pydantic
  app/main.py             POST /api/analyze, GET /api/health
  app/models.py           request/response + analysis schemas
  app/engine/             analysis engine
    job.py                job description -> requirements (sections, required/preferred)
    resume.py             resume sections + years of experience from date ranges
    skills.py             keyword search over data/skills.json
    match.py              matched / partial / missing per requirement
    advice.py             to-do list and wording-swap rewrites
    text.py               shared text helpers (sections, tokens, stemming)
  app/data/skills.json    skills dictionary with synonyms (edit to extend)
  app/scoring.py          evidence verification + deterministic score
  tests/                  pytest
```

Flow: frontend → `POST /api/analyze` → the engine produces an analysis → `scoring.py`
verifies it and computes the score → frontend renders the report.

## What the report shows

1. **Score:** the share of the job's keywords your resume contains, with a one-line verdict.
2. **Keywords**, in three lists:
   - **Found:** the keyword appears anywhere in your resume, Skills section included,
     the same way an ATS searches.
   - **Written differently:** you used a synonym (k8s vs Kubernetes) or a related term
     (CI vs CI/CD). A literal-match ATS may miss these.
   - **Missing:** not in your resume.
3. **What to do:** a short, prioritized list of ATS-relevant fixes, plus copy-ready
   bullet fixes.

## How the engine works

1. **Job description.** Detects sections ("Requirements", "Nice to have"; "About us" and
   "Benefits" are ignored, so the company's own tech stack isn't mistaken for a
   requirement). Each keyword is marked required or preferred from its section and cues
   like "a plus" or "must". It also extracts years of experience, degree level and
   unknown acronyms (e.g. HIPAA). Soft skills are left out: ATS keyword filters target
   hard skills, tools, certifications and qualifications.
2. **Resume.** Splits into sections and adds up the date ranges of your roles, merging
   overlaps. Markdown `**bold**` and Unicode bold letters (𝐏𝐲𝐭𝐡𝐨𝐧) are normalized before
   matching.
3. **Matching.** Each keyword is found, written differently, or missing (see above).
4. **To-do list.** Only fixes that affect ATS matching: wording to change, missing
   required and nice-to-have keywords, experience/degree gaps, and formatting that ATS
   can't read (Unicode bold letters, a missing Skills section).

### Truthful rewrites

Rewrites only swap the posting's wording in for **true synonyms** that your bullet
already uses, e.g. `Deployed services to k8s` → `Deployed services to Kubernetes (k8s)`.
They never add skills, achievements or numbers. Related-but-different terms (CI vs CI/CD,
Spring vs Spring Boot) get partial credit and an "only if accurate" note, but are never
swapped in automatically.

### Extending the skills dictionary

The engine recognizes skills listed in `backend/app/data/skills.json`, plus acronyms it
finds in the posting. To support a new skill, add it under a category:

```json
"tool": {
  "Kubernetes": ["k8s"],
  "=Excel": ["Microsoft Excel"],
  "CI/CD": ["~=CI", "~continuous integration"]
}
```

- A plain alias is a true synonym and may be swapped into rewrites.
- `=` means case-sensitive, for words that are also common English (Go, Excel, Spring).
- `~` means a related term, not a synonym: it earns partial credit but is never swapped.

## How the match score works

Each requirement is labelled `matched`, `partial` or `missing`, with a supporting quote
from the resume. The backend then:

1. **Verifies evidence.** A quote not found in the resume is discarded, and a "matched"
   item without verifiable evidence is downgraded to "partial".
2. **Drops invalid rewrites.** A bullet rewrite whose original isn't actually in the
   resume is removed.
3. **Scores deterministically.** `score = Σ(weight × credit) / Σ weight × 100`, with
   required = 2, preferred = 1; found = 1, written differently = 0.5, missing = 0.

The score measures keyword and requirement coverage only. Every ATS works differently,
so no tool can guarantee a pass, an interview or shortlisting. Keyword coverage is the
part they all share.

## Running locally

Requirements: Python 3.12+ with [uv](https://docs.astral.sh/uv/) and Node 20+.

**Backend** (port 8000):

```bash
cd backend
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

### Configuration

| Where | Variable | Default | Notes |
|---|---|---|---|
| `backend/.env` | `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins. |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL. |

## Tests

```bash
cd backend && uv run pytest
cd frontend && npm run typecheck
```

## Input limits

Resume: 100–30,000 characters. Job description: 100–20,000 characters. These are
enforced in both the UI and the API (`app/models.py`).

## Known limitations

- Skills outside `skills.json` are only detected if they're acronyms (e.g. HIPAA). Add
  domain-specific terms to the dictionary for best results.
- Rewrites are limited to wording swaps; the engine doesn't write new bullets.
