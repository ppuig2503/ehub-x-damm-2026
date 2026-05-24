import Link from "next/link";
import { notFound } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { DriverBreakdown } from "@/components/DriverBreakdown";
import { EvidenceTable } from "@/components/EvidenceTable";
import { ForcesPanel } from "@/components/ForcesPanel";
import { TrendChart } from "@/components/TrendChart";
import { actionLabel, formatPercent } from "@/lib/format";
import { getCommodityDetail, getOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

type CommodityDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function CommodityDetailPage({ params }: CommodityDetailPageProps) {
  const { id } = await params;
  const detail = await getCommodityDetail(id).catch(() => null);
  if (!detail) {
    notFound();
  }
  const overview = await getOverview();

  return (
    <AppShell currentPath="/">
      <section className="detail-hero">
        <div>
          <span className="eyebrow">{detail.region}</span>
          <h2>{detail.name}</h2>
          <p>{detail.recommendation.explanation}</p>
        </div>
        <div className="hero-metrics">
          <div className="hero-metric">
            <span>Recommendation</span>
            <strong>{actionLabel(detail.recommendation.recommended_action)}</strong>
          </div>
          <div className="hero-metric">
            <span>Coverage</span>
            <strong>{detail.recommendation.suggested_coverage}</strong>
          </div>
          <div className="hero-metric">
            <span>Horizon</span>
            <strong>{detail.recommendation.suggested_horizon}</strong>
          </div>
          <div className="hero-metric">
            <span>Confidence</span>
            <strong>{formatPercent(detail.confidence)}</strong>
          </div>
        </div>
      </section>

      <nav className="subnav" aria-label="Commodity switcher">
        {overview.commodities.map((commodity) => (
          <Link
            key={commodity.id}
            href={`/commodity/${commodity.id}`}
            className={commodity.id === id ? "subnav-chip active" : "subnav-chip"}
          >
            {commodity.name}
          </Link>
        ))}
      </nav>

      <div className="detail-layout">
        <TrendChart
          points={detail.trend}
          historyLabel={detail.history_label}
          historySource={detail.history_source}
          historyNote={detail.history_note}
        />
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Explanation card</span>
              <h3>Why SmartBuy recommends this move</h3>
            </div>
          </div>
          <p>{detail.recommendation.explanation}</p>
          <div className="detail-kpis">
            <div>
              <span className="metric-label">Latest benchmark</span>
              <strong>{detail.latest_history_value}</strong>
              <small>{detail.history_value_label}</small>
            </div>
            <div>
              <span className="metric-label">Risk score</span>
              <strong>{Math.round(detail.risk_score)}</strong>
              <small>0-100</small>
            </div>
            <div>
              <span className="metric-label">Uncertainty</span>
              <strong>{Math.round(detail.uncertainty_score)}</strong>
              <small>0-100</small>
            </div>
          </div>
          <p className="small-muted">{detail.what_changed}</p>
        </section>
      </div>

      <div className="detail-layout">
        <DriverBreakdown contributions={detail.driver_contributions} />
        <ForcesPanel bullish={detail.top_bullish_drivers} bearish={detail.top_bearish_drivers} />
      </div>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Evidence</span>
            <h3>Signals behind the recommendation</h3>
          </div>
        </div>
        <EvidenceTable signals={detail.signals.slice(0, 5)} />
        <div className="inline-actions">
          <Link href="/evidence" className="text-link">
            Open full Evidence Board
          </Link>
        </div>
      </section>
    </AppShell>
  );
}
