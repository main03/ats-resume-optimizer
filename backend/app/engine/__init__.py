"""Rule-based resume analyzer. Runs fully offline.

Pipeline: parse the job description into terms (job.py) -> parse the resume into sections
(resume.py) -> match each term (match.py) -> derive advice (advice.py).
"""

from collections import Counter

from ..models import Analysis, Requirement
from .advice import recommendations, rewrites
from .job import parse_job
from .match import match_all
from .resume import parse_resume


def analyze(resume: str, job_description: str) -> Analysis:
    job = parse_job(job_description)
    profile = parse_resume(resume)
    matches = match_all(job.terms, profile)
    return Analysis(
        role_title=job.role_title,
        requirements=_share_line_weights(matches),
        recommendations=recommendations(matches, profile, resume),
        rewritten_bullets=rewrites(matches),
    )


def _share_line_weights(matches) -> list[Requirement]:
    """One bullet = one requirement. "SSO and Federated ID" on one line share its points
    instead of each costing a full requirement."""
    def group(m):
        scored = m.term.kind in ("skill", "acronym") and m.term.category != "concept"
        return ("line", m.term.order) if scored else ("own", id(m))
    sizes = Counter(group(m) for m in matches)
    return [m.requirement.model_copy(update={"weight": 1 / sizes[group(m)]}) for m in matches]
