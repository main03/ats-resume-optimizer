import { AnalyzeResponse, Requirement } from "@/lib/api";

const TOP_ACTIONS = 3;

// A condensed view of the report: what's missing and the few changes that matter most.
export default function GapSummary({ result }: { result: AnalyzeResponse }) {
  const keywords = result.requirements.filter((r) => r.category !== "responsibility");
  const responsibilities = result.requirements.filter((r) => r.category === "responsibility");

  const missingRequired = keywords.filter((r) => r.status === "missing" && r.importance === "required");
  const missingPreferred = keywords.filter((r) => r.status === "missing" && r.importance === "preferred");
  const weak = keywords.filter((r) => r.status === "partial");
  const missingResponsibilities = responsibilities.filter((r) => r.status === "missing");
  const requiredTotal = keywords.filter((r) => r.importance === "required").length;
  const topActions = result.recommendations.slice(0, TOP_ACTIONS);

  const nothingMissing = missingRequired.length + missingPreferred.length + weak.length === 0;

  return (
    <section className="card summary-card" id="summary">
      <h3>Summary: what&apos;s missing</h3>
      <p className="summary-headline">
        {nothingMissing
          ? "Your resume covers every keyword this posting asks for."
          : `${missingRequired.length} of ${requiredTotal} required items are missing` +
            (weak.length ? `, and ${weak.length} need stronger wording or placement.` : ".")}
      </p>

      <SummaryRow label="Missing (required)" items={missingRequired} tone="missing" />
      <SummaryRow label="Needs stronger wording" items={weak} tone="partial" />
      <SummaryRow label="Missing (nice to have)" items={missingPreferred} tone="neutral" />

      {missingResponsibilities.length > 0 && (
        <p className="small-text">
          <strong>{missingResponsibilities.length}</strong> of {responsibilities.length} key
          responsibilities aren&apos;t reflected in your experience.
        </p>
      )}

      {topActions.length > 0 && (
        <>
          <h4>Do these first</h4>
          <ol className="top-actions">
            {topActions.map((r, i) => (
              <li key={i}>{r.suggestion}</li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}

function SummaryRow({
  label,
  items,
  tone,
}: {
  label: string;
  items: Requirement[];
  tone: "missing" | "partial" | "neutral";
}) {
  if (items.length === 0) return null;
  return (
    <div className="summary-row">
      <span className="summary-label">{label}</span>
      <div className="summary-chips">
        {items.map((r, i) => (
          <span key={`${r.term}-${i}`} className={`pill ${tone}`}>
            {r.term}
          </span>
        ))}
      </div>
    </div>
  );
}
