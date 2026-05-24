"use client";

import { useMemo, useState } from "react";
import { TrendPoint } from "@/lib/types";
import { formatDate } from "@/lib/format";

type TrendChartProps = {
  points: TrendPoint[];
  historyLabel: string;
  historySource: "cala_benchmark" | "local_fallback" | "barley_csv";
  historyNote?: string | null;
};

function buildPoints(values: number[]) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return values.map((value, index) => {
    const x = (index / (values.length - 1 || 1)) * 100;
    const y = 100 - ((value - min) / range) * 100;
    return { x, y };
  });
}

function catmullRom2bezier(points: { x: number; y: number }[]) {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x},${points[0].y}`;
  let d = `M ${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] || p2;

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    d += ` C ${cp1x},${cp1y} ${cp2x},${cp2y} ${p2.x},${p2.y}`;
  }
  return d;
}

export function TrendChart({ points, historyLabel, historySource, historyNote }: TrendChartProps) {
  const scoreValues = points.map((point) => point.score ?? 0);
  const proxyValues = points.map((point) => point.value);

  const scorePts = buildPoints(scoreValues);
  const proxyPts = buildPoints(proxyValues);
  const scorePath = catmullRom2bezier(scorePts);
  const proxyPath = catmullRom2bezier(proxyPts);
  const scoreArea = `${scorePath} L 100,100 L 0,100 Z`;
  const proxyArea = `${proxyPath} L 100,100 L 0,100 Z`;
  const scoreLast = scorePts[scorePts.length - 1];
  const proxyLast = proxyPts[proxyPts.length - 1];

  const [active, setActive] = useState<{
    series: "score" | "proxy";
    index: number;
  } | null>(null);

  function handleEnter(series: "score" | "proxy", index: number) {
    setActive({ series, index });
  }

  function handleLeave() {
    setActive(null);
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Price & risk trend</span>
          <h3>Signal score against market benchmark</h3>
        </div>
        <div className="legend">
          <span className="legend-item">
            <span className="legend-swatch risk-line" />
            SmartBuy score
          </span>
          <span className="legend-item">
            <span className="legend-swatch proxy-line" />
            {historyLabel}
          </span>
        </div>
      </div>
      {historySource === "local_fallback" && historyNote ? (
        <p className="history-fallback-note">{historyNote}</p>
      ) : null}
      <div className="trend-chart">
        <svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="proxyGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff9a00" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#ff9a00" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.18" />
              <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
            </linearGradient>
          </defs>

          <path d={proxyArea} className="trend-area proxy-area" fill="url(#proxyGradient)" />
          <path d={proxyPath} className="trend-line proxy-line" fill="none" vectorEffect="non-scaling-stroke" />

          <path d={scoreArea} className="trend-area score-area" fill="url(#riskGradient)" />
          <path d={scorePath} className="trend-line risk-line" fill="none" vectorEffect="non-scaling-stroke" />

          {proxyPts.map((p, i) => (
            <g key={`proxy-group-${i}`}>
              <circle
                className="trend-hit proxy-hit"
                cx={p.x}
                cy={p.y}
                r={6}
                vectorEffect="non-scaling-stroke"
                tabIndex={0}
                onMouseEnter={() => handleEnter("proxy", i)}
                onFocus={() => handleEnter("proxy", i)}
                onMouseLeave={handleLeave}
                onBlur={handleLeave}
              />
              <circle
                className={`trend-point proxy-point ${active?.series === "proxy" && active.index === i ? "active" : ""}`}
                cx={p.x}
                cy={p.y}
                r={2.2}
                vectorEffect="non-scaling-stroke"
              />
            </g>
          ))}
          {scorePts.map((p, i) => (
            <g key={`score-group-${i}`}>
              <circle
                className="trend-hit score-hit"
                cx={p.x}
                cy={p.y}
                r={6}
                vectorEffect="non-scaling-stroke"
                tabIndex={0}
                onMouseEnter={() => handleEnter("score", i)}
                onFocus={() => handleEnter("score", i)}
                onMouseLeave={handleLeave}
                onBlur={handleLeave}
              />
              <circle
                className={`trend-point score-point ${active?.series === "score" && active.index === i ? "active" : ""}`}
                cx={p.x}
                cy={p.y}
                r={2.2}
                vectorEffect="non-scaling-stroke"
              />
            </g>
          ))}

          {proxyLast ? (
            <circle className="trend-end proxy-end" cx={proxyLast.x} cy={proxyLast.y} r={4.2} vectorEffect="non-scaling-stroke" />
          ) : null}
          {scoreLast ? (
            <circle className="trend-end score-end" cx={scoreLast.x} cy={scoreLast.y} r={4.2} vectorEffect="non-scaling-stroke" />
          ) : null}
        </svg>
        {active ? (
          <div
            className={`trend-tooltip ${active.series}-tooltip`}
            style={{
              left: `${(active.series === "score" ? scorePts[active.index]?.x : proxyPts[active.index]?.x) ?? 0}%`,
              top: `${(active.series === "score" ? scorePts[active.index]?.y : proxyPts[active.index]?.y) ?? 0}%`,
            }}
          >
            {formatDate(points[active.index]?.date || "")}
          </div>
        ) : null}
      </div>
      <div className="trend-footer">
        <span>{formatDate(points[0]?.date || "")}</span>
        <span>{formatDate(points[points.length - 1]?.date || "")}</span>
      </div>
    </section>
  );
}

