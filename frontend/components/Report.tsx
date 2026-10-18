"use client";

import { useState } from "react";
import { AnalyzeResponse, Requirement } from "@/lib/api";
import CopyButton from "./CopyButton";
import GapSummary from "./GapSummary";
import Section from "./Section";

const SECTION_LABELS = {
  summary: "Summary",
  skills: "Skills",
  experience: "Experience",
  other: "Other",
} as const;

const PRIORITY_LABELS = { high: "High priority", medium: "Medium", low: "Low" } as const;

export default function Report({ result }: { result: AnalyzeResponse }) {
  const { requirements, highlights, recommendations, rewritten_bullets } = result;
  const keywords = requirements.filter((r) => r.category !== "responsibility");
  const responsibilities = requirements.filter((r) => r.category === "responsibility");
  const matched = keywords.filter((r) => r.status === "matched");
  const partial = keywords.filter((r) => r.status === "partial");
  const missing = keywords.filter((r) => r.status === "missing");
  const missingRequired = missing.filter((r) => r.importance === "required");
  const missingPreferred = missing.filter((r) => r.importance === "preferred");

  const nav = [
    { id: "score", label: "Score" },
    { id: "matched", label: "Already have", count: matched.length },
    { id: "partial", label: "Needs work", count: partial.length },
    { id: "missing", label: "Missing", count: missing.length },
    ...(responsibilities.length ? [{ id: "responsibilities", label: "Responsibilities" }] : []),
    { id: "recommendations", label: "Changes", count: recommendations.length },
    ...(highlights.length ? [{ id: "highlights", label: "Highlight" }] : []),
    { id: "bullets", label: "Bullets", count: rewritten_bullets.length },
    { id: "summary", label: "Summary" },
  ];
  let step = 0;

  return (
    <div className="report">
      <nav className="report-nav" aria-label="Report sections">
        <span className="muted small-text">Jump to:</span>
        {nav.map((n) => (
          <a key={n.id} href={`#${n.id}`}>
            {n.label}
            {n.count !== undefined && <span className="nav-count">{n.count}</span>}
          </a>
        ))}
      </nav>

      <Section
        id="score" step={++step} title="Match score"
        purpose={`How well your resume covers the requirements of “${result.role_title}”.`}
        action="Use it to compare versions of your resume for this job. Raise it by fixing the items in sections 3–5."
      >
        <ScoreBlock result={result} />
      </Section>

      <Section
        id="matched" step={++step} title="Already in your resume" count={matched.length}
        purpose="Requirements your resume clearly demonstrates, using the posting's own wording."
        action="Nothing to fix. Keep these when you edit your resume."
      >
        <MatchedList items={matched} />
      </Section>

      <Section
        id="partial" step={++step} title="Needs stronger wording" count={partial.length}
        purpose="Things you have, but in a weak form: only listed under Skills, or written differently from the posting (e.g. “k8s” instead of “Kubernetes”)."
        action="Use the posting's exact term, and mention the skill in the experience bullet where you used it."
      >
        <DetailList items={partial} tone="partial" empty="Nothing here. Your wording already matches the posting." />
      </Section>

      <Section
        id="missing" step={++step} title="Missing from your resume" count={missing.length}
        purpose="Requirements the posting asks for that don't appear anywhere in your resume."
        action="Add an item only if you genuinely have that experience. If you don't, it's a real gap. Mention how you're addressing it in your cover letter."
      >
        {missing.length === 0 ? (
          <p className="muted">Nothing missing. Your resume covers every keyword in the posting.</p>
        ) : (
          <>
            {missingRequired.length > 0 && (
              <>
                <h4 className="subheading">Required <span className="muted">· screened for first</span></h4>
                <DetailList items={missingRequired} tone="missing" empty="" />
              </>
            )}
            {missingPreferred.length > 0 && (
              <>
                <h4 className="subheading">Nice to have <span className="muted">· can set you apart</span></h4>
                <DetailList items={missingPreferred} tone="missing" empty="" />
              </>
            )}
          </>
        )}
      </Section>

      {responsibilities.length > 0 && (
        <Section
          id="responsibilities" step={++step} title="Responsibilities coverage"
          count={responsibilities.length}
          purpose="The main duties of the role, and whether your experience describes similar work. Matching is by overlapping words, so treat it as a guide."
          action="For anything marked missing that you have done, add a bullet describing it in similar language."
        >
          <ul className="resp-list">
            {responsibilities.map((r, i) => (
              <li key={i}>
                <span className={`pill ${r.status}`}>{statusLabel(r.status)}</span>
                <div>
                  <p>{r.term}</p>
                  {r.resume_evidence && (
                    <blockquote className="small-text">Closest in your resume: “{r.resume_evidence}”</blockquote>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section
        id="recommendations" step={++step} title="Recommended changes" count={recommendations.length}
        purpose="Specific edits to your resume, most important first. Each one names the section to change and why."
        action="Work from the top down. The high-priority items have the biggest effect."
      >
        <ol className="recommendations">
          {recommendations.map((r, i) => (
            <li key={i} className={`rec priority-border-${r.priority}`}>
              <div className="rec-head">
                <span className={`pill priority-${r.priority}`}>{PRIORITY_LABELS[r.priority]}</span>
                <span className="pill neutral">{SECTION_LABELS[r.section]} section</span>
              </div>
              <p className="rec-text">{r.suggestion}</p>
              {r.rationale && <p className="muted small-text">Why: {r.rationale}</p>}
            </li>
          ))}
        </ol>
      </Section>

      {highlights.length > 0 && (
        <Section
          id="highlights" step={++step} title="Experience to highlight"
          purpose="Lines from your resume that already prove several required skills at once."
          action="Move these near the top of each role. Recruiters often skim only the first few bullets."
        >
          <ul className="plain-list">
            {highlights.map((h, i) => (
              <li key={i}>
                <p className="quote-line">“{h.experience}”</p>
                <p className="muted small-text">{h.why_relevant}</p>
              </li>
            ))}
          </ul>
        </Section>
      )}

      <Section
        id="bullets" step={++step} title="Improved bullet points" count={rewritten_bullets.length}
        purpose="Your own bullets with the posting's exact terms swapped in, where you already used a true synonym (e.g. k8s → Kubernetes). Nothing new is added."
        action="Review each one, then copy the ones you like into your resume."
        aside={rewritten_bullets.length > 0 && (
          <CopyButton text={rewritten_bullets.map((b) => `• ${b.improved}`).join("\n")} label="Copy all" />
        )}
      >
        {rewritten_bullets.length === 0 ? (
          <p className="muted">
            No wording swaps needed: your bullets already use the posting&apos;s terms where they overlap.
          </p>
        ) : (
          <ul className="bullets">
            {rewritten_bullets.map((b, i) => (
              <li key={i}>
                <div className="before-after">
                  <span className="tag">Before</span>
                  <p className="original">{b.original}</p>
                  <span className="tag after">After</span>
                  <div className="improved-row">
                    <p className="improved">{b.improved}</p>
                    <CopyButton text={b.improved} />
                  </div>
                </div>
                {b.keywords_used.length > 0 && (
                  <p className="keywords-used">
                    <span className="muted small-text">Terms added:</span>
                    {b.keywords_used.map((k) => (
                      <span key={k} className="chip">{k}</span>
                    ))}
                  </p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <GapSummary result={result} step={++step} />
    </div>
  );
}

function ScoreBlock({ result }: { result: AnalyzeResponse }) {
  const { score } = result;
  const level = scoreLevel(score.score);
  return (
    <div className="score-block">
      <div className={`score-ring ${level.className}`}>
        <span className="score-value">{score.score}</span>
        <span className="score-label">out of 100</span>
      </div>
      <div className="score-text">
        <p className="score-verdict">{level.label}</p>
        <p>{level.meaning}</p>
        <p className="counts">
          <a href="#matched" className="pill matched">{score.matched} already in resume</a>
          <a href="#partial" className="pill partial">{score.partial} need work</a>
          <a href="#missing" className="pill missing">{score.missing} missing</a>
        </p>
        <details className="small-text">
          <summary>How is this calculated?</summary>
          <p className="muted">{score.explanation}</p>
        </details>
        <p className="muted small-text disclaimer">{score.disclaimer}</p>
        <a className="jump-link small-text" href="#summary">Short on time? Jump to the summary ↓</a>
      </div>
    </div>
  );
}

function MatchedList({ items }: { items: Requirement[] }) {
  const [showWhere, setShowWhere] = useState(false);
  if (items.length === 0) {
    return <p className="muted">No exact matches yet. Start with the “Needs stronger wording” section.</p>;
  }
  return (
    <>
      <div className="chip-cloud">
        {items.map((r, i) => (
          <span key={`${r.term}-${i}`} className="pill matched">
            {r.term}
            {r.importance === "required" && <span className="req-dot" title="Required">●</span>}
          </span>
        ))}
      </div>
      <p className="muted small-text legend">● = required by the posting</p>
      <button className="secondary small" onClick={() => setShowWhere((v) => !v)}>
        {showWhere ? "Hide where they appear" : "Show where they appear"}
      </button>
      {showWhere && <DetailList items={items} tone="matched" empty="" />}
    </>
  );
}

function DetailList({
  items, tone, empty,
}: { items: Requirement[]; tone: "matched" | "partial" | "missing"; empty: string }) {
  if (items.length === 0) return empty ? <p className="muted">{empty}</p> : null;
  return (
    <ul className="keywords">
      {items.map((r, i) => (
        <li key={`${r.term}-${i}`} className={`keyword ${tone}`}>
          <div className="keyword-head">
            <strong>{r.term}</strong>
            <span className={`pill ${r.importance === "required" ? "neutral strong" : "neutral"}`}>
              {r.importance === "required" ? "Required" : "Nice to have"}
            </span>
            <span className="category">{r.category.replace("_", " ")}</span>
          </div>
          {r.note && <p className="small-text">{r.note}</p>}
          {r.resume_evidence && (
            <blockquote className="small-text">In your resume: “{r.resume_evidence}”</blockquote>
          )}
        </li>
      ))}
    </ul>
  );
}

function statusLabel(status: Requirement["status"]): string {
  return { matched: "Covered", partial: "Partly", missing: "Missing" }[status];
}

function scoreLevel(score: number) {
  if (score >= 75)
    return {
      className: "high", label: "Strong match",
      meaning: "Your resume covers most of what this posting asks for. Polish the remaining items below.",
    };
  if (score >= 50)
    return {
      className: "mid", label: "Fair match",
      meaning: "You cover a good part of the requirements, but several important ones are weak or missing.",
    };
  return {
    className: "low", label: "Low match",
    meaning: "Many requirements aren't visible in your resume. Check whether you have them but haven't written them down.",
  };
}
