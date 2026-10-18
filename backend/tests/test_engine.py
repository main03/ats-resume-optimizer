from datetime import date

from app import engine
from app.engine.resume import experience_years, parse_resume

JOB = """Backend Engineer

About Us
Our stack includes Elixir.

Requirements
- 3+ years of software engineering experience
- Python, Kubernetes and CI/CD
- Bachelor's degree in Computer Science

Nice to have: Terraform
"""

RESUME = """SUMMARY
Backend engineer.

EXPERIENCE
Engineer, Acme — Jan 2020 – Dec 2023
• Built REST APIs in Python
• Deployed services to k8s and maintained the CI pipeline

SKILLS
Terraform

EDUCATION
B.S. Computer Science
"""


def by_term(analysis):
    return {r.term: r for r in analysis.requirements}


def test_builtin_engine_end_to_end():
    analysis = engine.analyze(RESUME, JOB)
    reqs = by_term(analysis)

    assert analysis.role_title == "Backend Engineer"
    assert "Elixir" not in reqs                              # "About Us" is ignored
    assert reqs["Python"].status == "matched"
    assert reqs["Kubernetes"].status == "partial"            # synonym: k8s
    assert reqs["CI/CD"].status == "partial"                 # related term: CI
    assert reqs["Terraform"].importance == "preferred"
    assert reqs["Terraform"].status == "matched"             # skills list counts, like an ATS
    assert reqs["Bachelor's degree"].status == "matched"
    assert reqs["3+ years of experience"].status == "matched"

    # Synonyms are swapped in; related terms (CI -> CI/CD) never are.
    [rewrite] = analysis.rewritten_bullets
    assert rewrite.improved == "Deployed services to Kubernetes (k8s) and maintained the CI pipeline"


def test_experience_years_merges_overlaps():
    profile = parse_resume("EXPERIENCE\nA — Jan 2018 – Dec 2020\nB — Jan 2020 – Present\n")
    years, _ = experience_years(profile, today=date(2024, 1, 1))
    assert years == 6.0


def test_requirement_lines_without_bullets_are_not_mistaken_for_headings():
    # Bullet markers are often lost in PDF text.
    job = "Requirements\n5+ years of professional software engineering experience\nPython and Docker\n"
    terms = {r.term for r in engine.analyze(RESUME, job).requirements}
    assert "5+ years of experience" in terms


def test_inflections_versions_and_hyphens_count_as_same_wording():
    job = (
        "Backend Engineer at Acme\n\nRequirements\n"
        "- Implementing automated testing platforms\n- HTML5 and CSS3\n- Front-end basics\n"
    )
    resume = "EXPERIENCE\n- Added 1,300+ automated tests\n- Built frontend pages with HTML and CSS\n"
    analysis = engine.analyze(resume, job)
    assert analysis.role_title == "Backend Engineer at Acme"
    statuses = {r.term: r.status for r in analysis.requirements}
    assert statuses["automated testing"] == "matched"
    assert statuses["HTML5"] == "matched"
    assert statuses["CSS3"] == "matched"
    assert statuses["Front-end"] == "matched"


def test_responsibilities_count_as_preferred():
    job = "What You'll Do\n- Refactor the codebase\n\nRequirements\n- Python\n"
    reqs = {r.term: r.importance for r in engine.analyze(RESUME, job).requirements}
    assert reqs["Refactor"] == "preferred"
    assert reqs["Python"] == "required"
