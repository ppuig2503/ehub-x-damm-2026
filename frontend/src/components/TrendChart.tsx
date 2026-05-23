import { TrendPoint } from "@/lib/types";
import { formatDate } from "@/lib/format";

type TrendChartProps = {
  points: TrendPoint[];
  proxyLabel: string;
};

function buildPolyline(values: number[]) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return values
    .map((value, index) => {
      const x = (index / (values.length - 1 || 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");
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
          <polyline
            points={buildPolyline(proxyValues)}
            className="trend-line proxy-line"
            fill="none"
          />
          <polyline
            points={buildPolyline(scoreValues)}
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

