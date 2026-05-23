import Link from "next/link";

import { actionLabel, formatPercent, titleize } from "@/lib/format";
import { CommodityOverview } from "@/lib/types";

type ActionPlanTableProps = {
  priorities: CommodityOverview[];
};

export function ActionPlanTable({ priorities }: ActionPlanTableProps) {
  return (
    <div className="priority-table">
      <div className="priority-header">
        <span>Priority</span>
        <span>Commodity</span>
        <span>Action</span>
        <span>Coverage</span>
        <span>Horizon</span>
        <span>Confidence</span>
      </div>
      {priorities.map((item, index) => (
        <div key={item.id} className="priority-row">
          <span>{index + 1}</span>
          <span>
            <Link href={`/commodity/${item.id}`}>{item.name}</Link>
          </span>
          <span>{actionLabel(item.recommended_action)}</span>
          <span>{item.suggested_coverage}</span>
          <span>{item.suggested_horizon}</span>
          <span>{formatPercent(item.confidence)}</span>
          <p className="priority-reason">
            {titleize(item.top_driver)} is the dominant driver with a {Math.round(item.risk_score)} risk score.
          </p>
        </div>
      ))}
    </div>
  );
}

