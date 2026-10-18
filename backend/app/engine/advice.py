"""Turn match results into a short to-do list and bullet rewrites."""

import re

from ..models import Recommendation, RewrittenBullet
from .match import Match
from .resume import LIST_SECTIONS, ResumeProfile

SWAPPABLE = {"technical_skill", "tool", "domain", "qualification"}
MAX_REWRITES = 6


def _join(items: list[str], limit: int = 8) -> str:
    return ", ".join(items[:limit]) + (f" (+{len(items) - limit} more)" if len(items) > limit else "")


def recommendations(matches: list[Match], resume: ResumeProfile, resume_text: str) -> list[Recommendation]:
    """Only ATS-relevant actions, most important first."""
    recs: list[Recommendation] = []

    def keywords(status: str, importance: str) -> list[str]:
        return [
            m.requirement.term for m in matches
            if m.term.kind in ("skill", "acronym") and m.term.category != "concept"
            and m.requirement.status == status and m.requirement.importance == importance
        ]

    scored = [m for m in matches if m.term.category != "concept"]
    wording = [m for m in scored if m.reason == "wording"]
    if wording:
        recs.append(Recommendation(
            section="skills", priority="high",
            suggestion="Use the job's exact wording: " + "; ".join(
                f"{m.resume_surface} → {m.requirement.term}" for m in wording[:6]
            ) + ".",
            rationale="Many ATS match keywords literally, so a synonym may not count.",
        ))

    missing_required = keywords("missing", "required")
    if missing_required:
        recs.append(Recommendation(
            section="skills", priority="high",
            suggestion=f"Add these required keywords if you genuinely have them: {_join(missing_required)}.",
            rationale="If you don't have them, they're real gaps. Don't add skills you can't back up.",
        ))

    for m in matches:
        if m.term.kind in ("years", "degree") and m.requirement.status != "matched":
            recs.append(Recommendation(
                section="other", priority="medium",
                suggestion=f"{m.requirement.term}: {m.requirement.note}",
                rationale="Some ATS filter on experience and education, so make them easy to find.",
            ))

    related = [m for m in scored if m.reason == "related"]
    if related:
        recs.append(Recommendation(
            section="experience", priority="medium",
            suggestion="Related but not the same: " + "; ".join(
                f"you wrote {m.resume_surface}, the job asks for {m.requirement.term}" for m in related[:6]
            ) + ". Use the job's term only if it's accurate.",
            rationale="These aren't exact synonyms, so they're not changed automatically.",
        ))

    missing_preferred = keywords("missing", "preferred")
    if missing_preferred:
        recs.append(Recommendation(
            section="skills", priority="low",
            suggestion=f"Nice to have, add if you have them: {_join(missing_preferred)}.",
            rationale="Not deal-breakers, but they can rank you higher.",
        ))

    recs.extend(_format_issues(resume, resume_text))
    return recs


def _format_issues(resume: ResumeProfile, resume_text: str) -> list[Recommendation]:
    """Formatting that stops an ATS from reading keywords at all."""
    recs = []
    if any(0x1D400 <= ord(ch) <= 0x1D7FF for ch in resume_text):
        recs.append(Recommendation(
            section="other", priority="high",
            suggestion="Replace the special Unicode “bold” letters (like 𝐭𝐡𝐢𝐬) with normal text.",
            rationale="ATS read these as symbols, so the words inside them don't match any keyword.",
        ))
    elif re.search(r"\*\*[^*\n]+\*\*|__[^_\n]+__", resume_text):
        recs.append(Recommendation(
            section="other", priority="low",
            suggestion="If your resume file contains literal ** or __ markers, remove them.",
            rationale="ATS and recruiters see the raw asterisks.",
        ))
    if resume.has_sections and not resume.has_section("skills"):
        recs.append(Recommendation(
            section="skills", priority="medium",
            suggestion="Add a “Skills” section listing your tools and technologies.",
            rationale="ATS parsers look for a skills section to extract keywords from.",
        ))
    return recs


# ---------- Rewrites ----------


def _replacement(job_term: str, resume_surface: str) -> str:
    def is_acronym(s: str) -> bool:
        return s.isupper() and len(s) <= 6
    if is_acronym(resume_surface) and not is_acronym(job_term):
        return f"{job_term} ({resume_surface})"
    if is_acronym(job_term) and not is_acronym(resume_surface):
        return f"{resume_surface} ({job_term})"
    if resume_surface.lower() in {"k8s", "postgres", "mongo", "js"}:
        return f"{job_term} ({resume_surface})"
    return job_term


def _is_statement(line) -> bool:
    """A bullet or sentence describing work, not a heading, list or contact line.
    Bullet markers are often lost when copying from a PDF, so long lines count too."""
    return line.section not in LIST_SECTIONS and (line.is_bullet or len(line.text) >= 40)


def rewrites(matches: list[Match]) -> list[RewrittenBullet]:
    """Swap the job's wording into bullets that already use a true synonym.

    These rewrites can't add anything untrue: they only rename what the bullet already says.
    """
    edits: dict[int, tuple[str, list[tuple[int, int, str]], list[str]]] = {}
    for m in matches:
        if m.reason != "wording" or not m.occurrences or m.term.category not in SWAPPABLE:
            continue
        if m.term.skill and m.term.skill.is_related(m.requirement.term):
            continue
        for occ in m.occurrences:
            if not _is_statement(occ.line):
                continue
            text, spans, used = edits.setdefault(id(occ.line), (occ.line.text, [], []))
            if any(occ.start < e and s < occ.end for s, e, _ in spans):
                continue
            spans.append((occ.start, occ.end, _replacement(m.requirement.term, occ.surface)))
            used.append(m.requirement.term)

    out = []
    for text, spans, used in edits.values():
        improved = text
        for start, end, repl in sorted(spans, reverse=True):
            improved = improved[:start] + repl + improved[end:]
        out.append(RewrittenBullet(original=text, improved=improved, keywords_used=list(dict.fromkeys(used))))
        if len(out) == MAX_REWRITES:
            break
    return out
