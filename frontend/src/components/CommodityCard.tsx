import Link from "next/link";

import { actionLabel, formatPercent, riskTone, titleize } from "@/lib/format";
import { CommodityOverview } from "@/lib/types";
import { MiniSparkline } from "@/components/MiniSparkline";

type CommodityCardProps = {
  commodity: CommodityOverview;
};

export function CommodityCard({ commodity }: CommodityCardProps) {
  const tone = riskTone(commodity.risk_score);

  return (
    <Link href={`/commodity/${commodity.id}`} className={`commodity-card tone-${tone}`}>
      <div className="card-header-row">
        <div>
          <span className="small-label">{commodity.region}</span>
          <h2>{commodity.name}</h2>
        </div>
        <span className={`status-pill tone-${tone}`}>{actionLabel(commodity.recommended_action)}</span>
      </div>

      <div className="metric-grid">
        <div>
          <span className="metric-label">Risk score</span>
          <strong>{Math.round(commodity.risk_score)}</strong>
        </div>
        <div>
          <span className="metric-label">Confidence</span>
          <strong>{formatPercent(commodity.confidence)}</strong>
        </div>
        <div>
          <span className="metric-label">Horizon</span>
          <strong>{commodity.suggested_horizon}</strong>
        </div>
        <div>
          <span className="metric-label">Top driver</span>
          <strong>{titleize(commodity.top_driver)}</strong>
        </div>
      </div>

      <div className="sparkline-block">
        <MiniSparkline values={commodity.score_history} />
      </div>

      <p className="supporting-copy">{commodity.explanation}</p>

      <div className="change-row">
        <span className={commodity.changed ? "delta-badge changed" : "delta-badge"}>
          {commodity.changed ? "Changed since last update" : "Stable versus last update"}
        </span>
        <span className="small-muted">{commodity.suggested_coverage}</span>
      </div>
    </Link>
  );
}

