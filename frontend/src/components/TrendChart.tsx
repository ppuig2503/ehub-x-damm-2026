import { TrendPoint } from "@/lib/types";
import { formatDate } from "@/lib/format";

type TrendChartProps = {
  points: TrendPoint[];
  proxyLabel: string;
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

export function TrendChart({ points, proxyLabel }: TrendChartProps) {
  const scoreValues = points.map((point) => point.score ?? 0);
  const proxyValues = points.map((point) => point.value);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Price & risk trend</span>
          <h3>Signal score against market proxy</h3>
        </div>
        <div className="legend">
          <span className="legend-item">
            <span className="legend-swatch risk-line" />
            SmartBuy score
          </span>
          <span className="legend-item">
            <span className="legend-swatch proxy-line" />
            {proxyLabel}
          </span>
        </div>
      </div>
      <div className="trend-chart">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none">
            <path
              d={catmullRom2bezier(buildPoints(proxyValues))}
              className="trend-line proxy-line"
              fill="none"
            />
            <path
              d={catmullRom2bezier(buildPoints(scoreValues))}
              className="trend-line risk-line"
              fill="none"
            />
        </svg>
      </div>
      <div className="trend-footer">
        <span>{formatDate(points[0]?.date || "")}</span>
        <span>{formatDate(points[points.length - 1]?.date || "")}</span>
      </div>
    </section>
  );
}

