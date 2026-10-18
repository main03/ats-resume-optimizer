interface Props {
  id: string;
  step: number;
  title: string;
  count?: number;
  purpose: string;   // what this section shows
  action?: string;   // what the reader should do with it
  aside?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}

// Every report section uses the same layout: numbered title, purpose, suggested action.
export default function Section({
  id, step, title, count, purpose, action, aside, className = "", children,
}: Props) {
  return (
    <section className={`card section ${className}`} id={id}>
      <header className="section-header">
        <div className="section-title">
          <span className="step" aria-hidden>{step}</span>
          <h3>
            {title}
            {count !== undefined && <span className="count">{count}</span>}
          </h3>
          {aside && <div className="section-aside">{aside}</div>}
        </div>
        <p className="purpose">{purpose}</p>
        {action && (
          <p className="action">
            <strong>What to do:</strong> {action}
          </p>
        )}
      </header>
      <div className="section-body">{children}</div>
    </section>
  );
}
