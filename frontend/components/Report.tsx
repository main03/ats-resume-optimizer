import { AnalyzeResponse, Requirement } from "@/lib/api";
import CopyButton from "./CopyButton";

// Three parts: the score, every keyword with its status, and a short to-do list.
export default function Report({ result }: { result: AnalyzeResponse }) {
  const { score, recommendations, rewritten_bullets } = result;
  // General practice words ("refactoring", "scalability") are shown separately and not scored.
  const requirements = result.requirements.filter((r) => r.category !== "concept");
  const concepts = result.requirements.filter((r) => r.category === "concept");
  const byImportance = (a: Requirement, b: Requirement) =>
    Number(b.importance === "required") - Number(a.importance === "required");
  const found = requirements.filter((r) => r.status === "matched").sort(byImportance);
  const different = requirements.filter((r) => r.status === "partial").sort(byImportance);
  const missing = requirements.filter((r) => r.status === "missing").sort(byImportance);
  const required = requirements.filter((r) => r.importance === "required");
  const requiredFound = required.filter((r) => r.status === "matched").length;
  const level = scoreLevel(score.score);

  return (
    <div className="report">
      {/* 1. Score */}
      <section className="card score-card">
        <div className={`score-ring ${level.className}`}>
          <span className="score-value">{score.score}</span>
          <span className="score-label">/ 100</span>
        </div>
        <div className="score-text">
          <h2>{level.label} for {result.role_title}</h2>
          <p>
            Your resume contains <strong>{found.length} of {requirements.length}</strong> keywords
            from this job, including <strong>{requiredFound} of {required.length}</strong> required ones.
          </p>
          <details>
            <summary>How is this calculated?</summary>
            <p className="muted">{score.explanation}</p>
          </details>
          <p className="muted small-text">{score.disclaimer}</p>
        </div>
      </section>

      {/* 2. Keywords */}
      <section className="card">
        <h2>Keywords from the job</h2>
        <p className="muted small-text">
          ATS systems scan your resume for these words. <span className="req-dot">●</span> = required by the job.
        </p>
        <div className="keyword-columns">
          <KeywordColumn title="Found" icon="✓" tone="matched" items={found}
            empty="None of the job's keywords were found." />
          <KeywordColumn title="Written differently" icon="≈" tone="partial" items={different}
            empty="None. Your wording matches the job." showNote />
          <KeywordColumn title="Missing" icon="✗" tone="missing" items={missing}
            empty="Nothing missing." groupByImportance />
        </div>
        {concepts.length > 0 && (
          <div className="concepts">
            <p className="small-text">
              <strong>Also mentioned in the job (not scored):</strong>{" "}
              <span className="muted">general practice words. Mention them where they fit naturally.</span>
            </p>
            <div className="concept-chips">
              {concepts.map((r, i) => (
                <span key={`${r.term}-${i}`} className={`pill ${r.status === "matched" ? "matched" : "neutral"}`}
                  title={r.note}>
                  {r.status === "matched" ? "✓ " : ""}{r.term}
                </span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* 3. Summary */}
      <section className="card">
        <h2>What to do</h2>
        {recommendations.length === 0 ? (
          <p>Your resume already covers this job&apos;s keywords. No changes needed.</p>
        ) : (
          <ol className="todo">
            {recommendations.map((r, i) => (
              <li key={i} className={`todo-${r.priority}`}>
                <p>{r.suggestion}</p>
                {r.rationale && <p className="muted small-text">{r.rationale}</p>}
              </li>
            ))}
          </ol>
        )}

        {rewritten_bullets.length > 0 && (
          <details className="bullet-fixes">
            <summary>Copy-ready bullet fixes ({rewritten_bullets.length})</summary>
            <p className="muted small-text">
              Your own bullets with the job&apos;s exact terms swapped in. Nothing new is added.
            </p>
            <ul>
              {rewritten_bullets.map((b, i) => (
                <li key={i}>
                  <p className="original">{b.original}</p>
                  <div className="improved-row">
                    <p className="improved">{b.improved}</p>
                    <CopyButton text={b.improved} />
                  </div>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>
    </div>
  );
}

function KeywordColumn({
  title, icon, tone, items, empty, showNote = false, groupByImportance = false,
}: {
  title: string;
  icon: string;
  tone: "matched" | "partial" | "missing";
  items: Requirement[];
  empty: string;
  showNote?: boolean;
  groupByImportance?: boolean;
}) {
  const groups = groupByImportance
    ? [
        { label: "Required", items: items.filter((r) => r.importance === "required") },
        { label: "Nice to have", items: items.filter((r) => r.importance === "preferred") },
      ].filter((g) => g.items.length > 0)
    : [{ label: "", items }];
  return (
    <div className={`keyword-column ${tone}`}>
      <h3>
        <span className="icon" aria-hidden>{icon}</span> {title} <span className="count">{items.length}</span>
      </h3>
      {items.length === 0 ? (
        <p className="muted small-text">{empty}</p>
      ) : (
        groups.map((g) => (
          <div key={g.label} className="keyword-group">
            {g.label && <p className="group-label">{g.label}</p>}
            <ul>
              {g.items.map((r, i) => (
                <li key={`${r.term}-${i}`} title={r.resume_evidence ? `In your resume: “${r.resume_evidence}”` : r.note}>
                  <span className="term">
                    {r.term}
                    {r.importance === "required" && <span className="req-dot" aria-label="required"> ●</span>}
                  </span>
                  {showNote && r.note && <span className="note">{r.note}</span>}
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  );
}

function scoreLevel(score: number) {
  if (score >= 75) return { className: "high", label: "Strong match" };
  if (score >= 50) return { className: "mid", label: "Fair match" };
  return { className: "low", label: "Low match" };
}
