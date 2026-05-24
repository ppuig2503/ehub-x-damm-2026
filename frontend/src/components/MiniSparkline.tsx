"use client";

import { useMemo, useState } from "react";

import { formatDate } from "@/lib/format";

type MiniSparklineProps = {
  values: number[];
  dates?: string[];
};

const SPARKLINE_X_PADDING = 4;
const SPARKLINE_Y_PADDING = 8;

export function MiniSparkline({ values, dates }: MiniSparklineProps) {
  const normalizedDates = useMemo(() => {
    if (!dates?.length) return null;
    if (dates.length === values.length) return dates;
    return null;
  }, [dates, values.length]);

  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  if (!values.length) {
    return null;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const innerWidth = 100 - SPARKLINE_X_PADDING * 2;
  const innerHeight = 100 - SPARKLINE_Y_PADDING * 2;
  const pts = values.map((value, index) => {
    const x = SPARKLINE_X_PADDING + (index / (values.length - 1 || 1)) * innerWidth;
    const y = 100 - SPARKLINE_Y_PADDING - ((value - min) / range) * innerHeight;
    return { x, y };
  });

  function catmullRom2bezier(points: { x: number; y: number }[]) {
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

  const pathD = catmullRom2bezier(pts);
  const areaD = `${pathD} L ${100 - SPARKLINE_X_PADDING},${100 - SPARKLINE_Y_PADDING} L ${SPARKLINE_X_PADDING},${100 - SPARKLINE_Y_PADDING} Z`;
  const lastPoint = pts[pts.length - 1];

  const activePoint = activeIndex !== null ? pts[activeIndex] : null;
  const activeDate =
    activeIndex !== null && normalizedDates
      ? normalizedDates[activeIndex]
      : null;

  return (
    <div className="sparkline-wrap">
      <svg className="sparkline" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="sparklineGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="currentColor" stopOpacity="0.22" />
            <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path
          d={areaD}
          className="sparkline-area"
          fill="url(#sparklineGradient)"
        />
        <path
          d={pathD}
          className="sparkline-line"
          fill="none"
          stroke="currentColor"
          vectorEffect="non-scaling-stroke"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {pts.map((point, index) => (
          <g key={`spark-group-${index}`}>
            <circle
              className={`sparkline-hit ${activeIndex === index ? "active" : ""}`}
              cx={point.x}
              cy={point.y}
              r={6}
              vectorEffect="non-scaling-stroke"
              tabIndex={0}
              onMouseEnter={() => setActiveIndex(index)}
              onFocus={() => setActiveIndex(index)}
              onMouseLeave={() => setActiveIndex(null)}
              onBlur={() => setActiveIndex(null)}
            />
            <circle
              className={
                activeIndex === index
                  ? "sparkline-point active"
                  : "sparkline-point"
              }
              cx={point.x}
              cy={point.y}
              r={2.6}
              vectorEffect="non-scaling-stroke"
            />
          </g>
        ))}
        <circle
          className="sparkline-end"
          cx={lastPoint.x}
          cy={lastPoint.y}
          r="3.6"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      {activePoint && activeDate ? (
        <div
          className="sparkline-tooltip"
          style={{
            left: `${activePoint.x}%`,
            top: `${activePoint.y}%`,
          }}
        >
          {formatDate(activeDate)}
        </div>
      ) : null}
    </div>
  );
}

