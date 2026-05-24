"use client";

import { useEffect, useMemo, useState } from "react";
import { Signal } from "@/lib/types";
import { formatDate, formatPercent, titleize } from "@/lib/format";

type EvidenceTableProps = {
  signals: Signal[];
  pageSize?: number; // number of rows per page
};

export function EvidenceTable({ signals, pageSize = 10 }: EvidenceTableProps) {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState<number>(pageSize);

  // adjust rowsPerPage to match the visual height of the heatmap-list
  useEffect(() => {
    function recompute() {
      const heat = document.querySelector(".heatmap-list");
      const firstRow = document.querySelector(".evidence-row summary");
      const heatH = heat ? (heat as HTMLElement).clientHeight : 0;
      const rowH = firstRow ? (firstRow as HTMLElement).clientHeight : 64;
      if (heatH > 0 && rowH > 0) {
        const desired = Math.max(1, Math.floor(heatH / rowH));
        if (desired !== rowsPerPage) {
          setRowsPerPage(desired);
          setPage(0);
        }
      }
    }

    // run once after mount
    recompute();
    // update on resize
    window.addEventListener("resize", recompute);
    return () => window.removeEventListener("resize", recompute);
  }, [signals, rowsPerPage]);

  const totalPages = Math.max(1, Math.ceil(signals.length / rowsPerPage));

  const pageSignals = useMemo(() => {
    // clamp page
    const currentPage = Math.max(0, Math.min(page, totalPages - 1));
    let start = currentPage * rowsPerPage;

    // if last chunk is short, move start back so this page is full
    if (start + rowsPerPage > signals.length) {
      start = Math.max(0, signals.length - rowsPerPage);
    }

    return signals.slice(start, start + rowsPerPage);
  }, [signals, page, rowsPerPage, totalPages]);

  function goto(next: number) {
    const clamped = Math.max(0, Math.min(totalPages - 1, next));
    setPage(clamped);
  }

  return (
    <div className="evidence-table">
      <div className="evidence-header" aria-hidden="true">
        <span>Date</span>
        <span>Commodity</span>
        <span>Driver</span>
        <span>Event</span>
        <span>Direction</span>
        <span>Impact</span>
        <span>Confidence</span>
        <span>Usage</span>
      </div>
      {pageSignals.map((signal) => {
        const hasDirectSourceUrl =
          (signal.source_link_status ?? "fallback") === "direct" &&
          signal.source_url !== "https://docs.cala.ai";

        return (
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
              <p className="source-row">
                <strong>Source:</strong>{" "}
                {hasDirectSourceUrl ? (
                  <a href={signal.source_url} target="_blank" rel="noreferrer">
                    {signal.source_name}
                  </a>
                ) : (
                  <span>{signal.source_name}</span>
                )}
                <span className={`source-status ${hasDirectSourceUrl ? "direct" : "fallback"}`}>
                  {hasDirectSourceUrl ? "Direct source" : "Fallback link unavailable"}
                </span>
              </p>
              {signal.source_reference ? (
                <p>
                  <strong>Source trace:</strong> {signal.source_reference}
                </p>
              ) : null}
              <p>
                <strong>Horizon:</strong> {signal.horizon}
              </p>
            </div>
          </details>
        );
      })}

      <div className="evidence-pagination" aria-label="Evidence pagination">
        <button className="pagination-button" onClick={() => goto(page - 1)} disabled={page === 0}>
          Previous
        </button>
        <span className="pagination-info">
          Page {page + 1} of {totalPages}
        </span>
        <button className="pagination-button" onClick={() => goto(page + 1)} disabled={page >= totalPages - 1}>
          Next
        </button>
      </div>
    </div>
  );
}
