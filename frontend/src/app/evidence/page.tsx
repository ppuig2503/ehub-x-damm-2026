import { AppShell } from "@/components/AppShell";
import { EvidenceTable } from "@/components/EvidenceTable";
import { getSignals } from "@/lib/api";
import { titleize } from "@/lib/format";

export const dynamic = "force-dynamic";

type EvidencePageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

function getSingleValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value;
}

export default async function EvidencePage({ searchParams }: EvidencePageProps) {
  const params = await searchParams;
  const query = new URLSearchParams();

  const commodity = getSingleValue(params.commodity);
  const driver = getSingleValue(params.driver);
  const direction = getSingleValue(params.direction);
  const minImpact = getSingleValue(params.min_impact);

  if (commodity) query.set("commodity", commodity);
  if (driver) query.set("driver", driver);
  if (direction) query.set("direction", direction);
  if (minImpact) query.set("min_impact", minImpact);
  query.set("limit", "100");

  const payload = await getSignals(query.toString());
  const bullishCount = payload.signals.filter((signal) => signal.direction === "bullish").length;
  const bearishCount = payload.signals.filter((signal) => signal.direction === "bearish").length;
  const neutralCount = payload.signals.filter((signal) => signal.direction === "neutral").length;
  const heatmap = Array.from(
    payload.signals.reduce((map, signal) => {
      const key = `${signal.commodity}-${signal.driver}`;
      map.set(key, {
        commodity: signal.commodity,
        driver: signal.driver,
        count: (map.get(key)?.count || 0) + 1,
      });
      return map;
    }, new Map<string, { commodity: string; driver: string; count: number }>())
      .values(),
  );

  return (
    <AppShell currentPath="/evidence">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">Evidence Board</span>
          <h2>Trace every recommendation back to a signal, source, and mechanism.</h2>
          <p>
            Analysts can filter by commodity or driver, inspect source traceability,
            and decide which signals deserve attention before the committee meeting.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="hero-metric">
            <span className="metric-title total">Total signals</span>
            <strong>{payload.count}</strong>
          </div>
          <div className="hero-metric">
            <span className="metric-title bullish">Bullish</span>
            <strong>{bullishCount}</strong>
          </div>
          <div className="hero-metric">
            <span className="metric-title bearish">Bearish</span>
            <strong>{bearishCount}</strong>
          </div>
          <div className="hero-metric">
            <span className="metric-title neutral">Neutral</span>
            <strong>{neutralCount}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <form className="filter-grid" method="get">
          <label className="field">
            <span>Commodity</span>
            <select key={`commodity-${commodity || "none"}`} name="commodity" defaultValue={commodity || ""}>
              <option value="">All</option>
              <option value="aluminium">Aluminium</option>
              <option value="pet">PET</option>
              <option value="energy">Energy</option>
              <option value="barley">Barley</option>
            </select>
          </label>
          <label className="field">
            <span>Driver</span>
            <input key={`driver-${driver || "none"}`} type="text" name="driver" defaultValue={driver || ""} placeholder="energy, weather..." />
          </label>
          <label className="field">
            <span>Direction</span>
            <select key={`direction-${direction || "none"}`} name="direction" defaultValue={direction || ""}>
              <option value="">All</option>
              <option value="bullish">Bullish</option>
              <option value="bearish">Bearish</option>
              <option value="neutral">Neutral</option>
            </select>
          </label>
          <label className="field">
            <span>Minimum impact</span>
            <input key={`minimpact-${minImpact || "none"}`} type="number" min="0" max="1" step="0.05" name="min_impact" defaultValue={minImpact || ""} placeholder="0.00 to 1.00" />
          </label>
          <button type="submit" className="action-button">
            Apply filters
          </button>
        </form>
      </section>

      <div className="two-column-layout evidence-layout">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Signal traceability</span>
              <div className="heading-with-help">
                <h3>Normalized evidence rows</h3>
                <details className="micro-help">
                  <summary aria-label="Evidence terms help">?</summary>
                  <div className="micro-help-card align-left">
                    <p><strong>Confidence</strong> = how reliable the signal looks based on source quality and supporting context.</p>
                    <p><strong>Coverage</strong> = the share of expected buying volume SmartBuy suggests securing now.</p>
                  </div>
                </details>
              </div>
            </div>
          </div>
          <EvidenceTable signals={payload.signals} pageSize={7} />
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Driver x commodity</span>
              <h3>Heatmap summary</h3>
            </div>
          </div>
          <div className="heatmap-list">
            {heatmap.map((item) => (
              <div key={`${item.commodity}-${item.driver}`} className="heatmap-row">
                <span>{titleize(item.commodity)}</span>
                <span>{titleize(item.driver)}</span>
                <strong>{item.count}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

