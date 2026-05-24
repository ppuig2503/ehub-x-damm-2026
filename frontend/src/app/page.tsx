import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { CommodityCard } from "@/components/CommodityCard";
import { RefreshSignalsButton } from "@/components/RefreshSignalsButton";
import { formatDate, refreshLabel } from "@/lib/format";
import { getOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const overview = await getOverview();
  const topRisks = overview.commodities.slice(0, 2);

  return (
    <AppShell currentPath="/">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">Procurement Radar</span>
          <h2>Today&apos;s highest buying pressure sits in {topRisks.map((item) => item.name).join(" and ")}.</h2>
          <p>
            DammBuy normalizes external signals, blends them with proxy data, and
            keeps the barley dataset in the decision loop without pretending it is an exact price series.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="hero-metric">
            <span>Market status</span>
            <strong>{overview.market_status}</strong>
          </div>
          <div className="hero-metric">
            <span>Latest update</span>
            <strong>{formatDate(overview.generated_at)}</strong>
          </div>
          <div className="hero-metric">
            <span className="metric-with-help">
              <span>Refresh mode</span>
              <details className="micro-help">
                <summary aria-label="Refresh mode help">?</summary>
                <div className="micro-help-card align-top">
                  <p><strong>Live</strong> = connected Cala refresh.</p>
                  <p><strong>Fallback</strong> = Cala was attempted, local backup is shown.</p>
                  <p><strong>Seed</strong> = base demo dataset only.</p>
                </div>
              </details>
            </span>
            <strong>{refreshLabel(overview.refresh_status)}</strong>
          </div>
        </div>
      </section>

      <section className="inline-actions">
        <RefreshSignalsButton />
      </section>

      <section className="card-grid">
        {overview.commodities.map((commodity) => (
          <CommodityCard key={commodity.id} commodity={commodity} generatedAt={overview.generated_at} />
        ))}
      </section>

      <section>
        <article className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Top risks today</span>
              <h3>Priority for the purchasing meeting</h3>
            </div>
          </div>
          <div className="rank-list">
            {overview.commodities.map((commodity, index) => (
              <div key={commodity.id} className="rank-row">
                <strong>{index + 1}</strong>
                <div>
                  <Link href={`/commodity/${commodity.id}`}>{commodity.name}</Link>
                  <p className="small-muted">{commodity.change_note}</p>
                </div>
                <span>{Math.round(commodity.risk_score)}</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AppShell>
  );
}
