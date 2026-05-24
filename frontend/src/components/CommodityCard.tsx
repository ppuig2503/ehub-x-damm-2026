"use client";

import Link from "next/link";
import { useState } from "react";

import { actionLabel, formatMonthYear, formatPercent, riskTone, titleize } from "@/lib/format";
import { CommodityOverview } from "@/lib/types";
import { MiniSparkline } from "@/components/MiniSparkline";

type CommodityCardProps = {
  commodity: CommodityOverview;
};

export function CommodityCard({ commodity }: CommodityCardProps) {
  const tone = riskTone(commodity.risk_score);
  const canToggleBenchmark = commodity.history_source !== "barley_csv" && Boolean(commodity.benchmark_history?.length);
  const [viewMode, setViewMode] = useState<"score" | "benchmark">("score");
  const sparklineValues =
    canToggleBenchmark && viewMode === "benchmark"
      ? commodity.benchmark_history ?? commodity.score_history
      : commodity.score_history;

  const historyStart = commodity.history_start;
  const historyEnd = commodity.history_end;

  return (
    <section className={`commodity-card tone-${tone}`}>
      <div className="card-header-row">
        <div>
          <span className="small-label">{commodity.region}</span>
          <h2>
            <Link href={`/commodity/${commodity.id}`}>{commodity.name}</Link>
          </h2>
        </div>
        <span className={`status-pill action-${commodity.recommended_action}`}>
          {actionLabel(commodity.recommended_action)}
        </span>
      </div>

      {canToggleBenchmark ? (
        <div className="sparkline-toggle-row">
          <span className="small-muted">Chart</span>
          <div className="sparkline-toggle" role="tablist" aria-label={`${commodity.name} sparkline mode`}>
            <button
              type="button"
              className={viewMode === "score" ? "active" : ""}
              onClick={() => setViewMode("score")}
            >
              Score
            </button>
            <button
              type="button"
              className={viewMode === "benchmark" ? "active" : ""}
              onClick={() => setViewMode("benchmark")}
            >
              Benchmark
            </button>
          </div>
        </div>
      ) : null}

      <Link href={`/commodity/${commodity.id}`} className="commodity-card-link">
        <div className="metric-chart-row">
          <div className="metric-stack">
            <div className="metric-item">
              <span className="metric-label">Risk score</span>
              <strong>{Math.round(commodity.risk_score)}</strong>
            </div>
            <div className="metric-item">
              <span className="metric-label">Horizon</span>
              <strong>{commodity.suggested_horizon}</strong>
            </div>
            <div className="metric-item">
              <span className="metric-label">Confidence</span>
              <strong>{formatPercent(commodity.confidence)}</strong>
            </div>
            <div className="metric-item">
              <span className="metric-label">Top driver</span>
              <strong>{titleize(commodity.top_driver)}</strong>
            </div>
          </div>

          <div className="sparkline-block">
            <MiniSparkline
              values={sparklineValues}
              dates={commodity.history_dates ?? undefined}
            />
            {historyStart && historyEnd ? (
              <div className="sparkline-axis" aria-hidden="true">
                <span>{formatMonthYear(historyStart)}</span>
                <span>{formatMonthYear(historyEnd)}</span>
              </div>
            ) : null}
          </div>
        </div>

        <p className="supporting-copy">{commodity.explanation}</p>

        <div className="change-row">
          <span className={commodity.changed ? "delta-badge changed" : "delta-badge"}>
            {commodity.changed ? "Changed since last update" : "Stable versus last update"}
          </span>
          <span className="small-muted">{commodity.suggested_coverage}</span>
        </div>
      </Link>
    </section>
  );
}

