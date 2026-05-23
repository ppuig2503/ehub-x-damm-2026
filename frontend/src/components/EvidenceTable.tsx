import { Signal } from "@/lib/types";
import { formatDate, formatPercent, titleize } from "@/lib/format";

type EvidenceTableProps = {
  signals: Signal[];
};

export function EvidenceTable({ signals }: EvidenceTableProps) {
  return (
    <div className="evidence-table">
      {signals.map((signal) => (
        <details key={signal.id} className="evidence-row">
          <summary>
            <span>{formatDate(signal.date)}</span>
            <span>{titleize(signal.commodity)}</span>
            <span>{titleize(signal.driver)}</span>
            <span>{signal.event}</span>
            <span className={`dir-${signal.direction}`}>{titleize(signal.direction)}</span>
            <span>{formatPercent(signal.impact_score * 100)}</span>
            <span>{formatPercent(signal.confidence * 100)}</span>
            <span>{signal.used_in_score ? "Used" : "Ignored"}</span>
          </summary>
          <div className="evidence-details">
            <p>{signal.evidence}</p>
            <p>
              <strong>Mechanism:</strong> {signal.mechanism}
            </p>
            <p>
              <strong>Source:</strong>{" "}
              <a href={signal.source_url} target="_blank" rel="noreferrer">
                {signal.source_name}
              </a>
            </p>
            <p>
              <strong>Horizon:</strong> {signal.horizon}
            </p>
          </div>
        </details>
      ))}
    </div>
  );
}

