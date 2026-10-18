"""Deterministic post-processing: verify LLM claims against the resume and compute the score.

The LLM decides *what* the job requires and how the resume relates to it; this module
makes sure every "matched" claim is backed by text that actually exists in the resume,
and computes the score with a transparent formula instead of asking the LLM for a number.
"""

import re

from .models import LLMAnalysis, Requirement, RewrittenBullet, ScoreBreakdown

IMPORTANCE_WEIGHT = {"required": 3, "preferred": 1}
STATUS_CREDIT = {"matched": 1.0, "partial": 0.5, "missing": 0.0}
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

DISCLAIMER = (
    "This score estimates keyword and requirement coverage only. Real ATS systems and "
    "recruiters vary, and no score guarantees an interview or shortlisting."
)

_PUNCT_MAP = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def normalize(text: str) -> str:
    """Lowercase, unify quotes/dashes, drop leading bullet markers and collapse whitespace."""
    text = text.translate(_PUNCT_MAP).lower()
    text = re.sub(r"^\s*[-*•·▪◦]+\s*", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip().rstrip(".")


def appears_in(snippet: str, resume_normalized: str) -> bool:
    snippet = normalize(snippet)
    return bool(snippet) and snippet in resume_normalized


def verify_requirements(requirements: list[Requirement], resume: str) -> list[Requirement]:
    """Drop evidence that isn't in the resume; downgrade unsupported "matched" claims."""
    resume_normalized = normalize(resume)
    verified = []
    for req in requirements:
        evidence = req.resume_evidence if appears_in(req.resume_evidence, resume_normalized) else ""
        status = req.status
        if status == "matched" and not evidence:
            status = "partial"
        verified.append(req.model_copy(update={"resume_evidence": evidence, "status": status}))
    return verified


def verify_bullets(bullets: list[RewrittenBullet], resume: str) -> list[RewrittenBullet]:
    """Keep only rewrites whose original bullet really exists in the resume."""
    resume_normalized = normalize(resume)
    return [b for b in bullets if appears_in(b.original, resume_normalized)]


def compute_score(requirements: list[Requirement]) -> ScoreBreakdown:
    counts = {"matched": 0, "partial": 0, "missing": 0}
    earned = possible = 0.0
    for req in requirements:
        weight = IMPORTANCE_WEIGHT[req.importance]
        possible += weight
        earned += weight * STATUS_CREDIT[req.status]
        counts[req.status] += 1

    score = round(100 * earned / possible) if possible else 0
    explanation = (
        f"Weighted coverage of {len(requirements)} job requirements. Required items count "
        f"{IMPORTANCE_WEIGHT['required']}x, preferred items 1x. A clearly demonstrated item "
        f"earns full credit, a partially demonstrated or weakly worded one earns half, and a "
        f"missing one earns none. \"Matched\" is only granted when the supporting text is "
        f"found verbatim in your resume. Result: {earned:g} of {possible:g} points."
    )
    return ScoreBreakdown(score=score, **counts, explanation=explanation, disclaimer=DISCLAIMER)


def postprocess(analysis: LLMAnalysis, resume: str) -> dict:
    requirements = verify_requirements(analysis.requirements, resume)
    return {
        "role_title": analysis.role_title,
        "score": compute_score(requirements),
        "requirements": requirements,
        "highlights": analysis.highlights,
        "recommendations": sorted(
            analysis.recommendations, key=lambda r: PRIORITY_ORDER[r.priority]
        ),
        "rewritten_bullets": verify_bullets(analysis.rewritten_bullets, resume),
    }
