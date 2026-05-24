"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { actionLabel, formatMonthYear, formatPercent, riskTone, titleize } from "@/lib/format";
import { CommodityOverview } from "@/lib/types";
import { MiniSparkline } from "@/components/MiniSparkline";

type CommodityCardProps = {
  commodity: CommodityOverview;
  generatedAt: string;
};

function buildMonthlyDates(endIso: string, count: number) {
  const end = new Date(endIso);
  end.setDate(1);
  const dates: string[] = [];
  for (let offset = count - 1; offset >= 0; offset -= 1) {
    const value = new Date(end.getFullYear(), end.getMonth() - offset, 1);
    dates.push(value.toISOString());
  }
  return dates;
}

export function CommodityCard({ commodity, generatedAt }: CommodityCardProps) {
  const tone = riskTone(commodity.risk_score);
  const canToggleBenchmark = Boolean(commodity.benchmark_history?.length);
  const [viewMode, setViewMode] = useState<"score" | "benchmark">("score");
  const sparklineValues =
    canToggleBenchmark && viewMode === "benchmark"
      ? commodity.benchmark_history ?? commodity.score_history
      : commodity.score_history;

  const fallbackHistoryDates = useMemo(
    () => buildMonthlyDates(generatedAt, sparklineValues.length),
    [generatedAt, sparklineValues.length],
  );
  const sparklineDates =
    commodity.history_dates?.length === sparklineValues.length
      ? commodity.history_dates
      : fallbackHistoryDates;
  const historyStart = sparklineDates[0] ?? commodity.history_start;
  const historyEnd = sparklineDates[sparklineDates.length - 1] ?? commodity.history_end;

  return (
    <Link
      href={`/commodity/${commodity.id}`}
      className={`commodity-card tone-${tone}`}
      aria-label={`Open ${commodity.name} details`}
    >
      <div className="card-header-row">
        <div>
          <span className="small-label">{commodity.region}</span>
          <h2>{commodity.name}</h2>
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
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setViewMode("score");
              }}
            >
              Score
            </button>
            <button
              type="button"
              className={viewMode === "benchmark" ? "active" : ""}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setViewMode("benchmark");
              }}
            >
              Benchmark
            </button>
          </div>
        </div>
      ) : null}

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
            dates={sparklineDates}
          />
          {historyStart && historyEnd ? (
            <div className="sparkline-axis" aria-hidden="true">
              <span>{formatMonthYear(historyStart)}</span>
              <span>{formatMonthYear(historyEnd)}</span>
            </div>
          ) : null}
        </div>
      </div>
      <div className="change-row">
        <span className={commodity.changed ? "delta-badge changed" : "delta-badge"}>
          {commodity.changed ? "Changed since last update" : "Stable versus last update"}
        </span>
        <span className="small-muted">{commodity.suggested_coverage}</span>
      </div>
    </Link>
  );
}

