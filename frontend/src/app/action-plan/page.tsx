import { AppShell } from "@/components/AppShell";
import { ActionPlanTable } from "@/components/ActionPlanTable";
import { formatDate, refreshLabel } from "@/lib/format";
import { getActionPlan } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ActionPlanPage() {
  const payload = await getActionPlan();

  return (
    <AppShell currentPath="/action-plan">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">Action Plan</span>
          <h2>Turn analysis into a committee-ready procurement recommendation.</h2>
          <p>{payload.memo}</p>
        </div>
        <div className="hero-metrics">
          <div className="hero-metric">
            <span>Snapshot</span>
            <strong>{formatDate(payload.generated_at)}</strong>
          </div>
          <div className="hero-metric">
            <span>Refresh mode</span>
            <strong>{refreshLabel(payload.refresh_status)}</strong>
          </div>
        </div>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Priority queue</span>
            <div className="heading-with-help">
              <h3>Procurement recommendation table</h3>
              <details className="micro-help">
                <summary aria-label="Action plan terms help">?</summary>
                <div className="micro-help-card align-left">
                  <p><strong>Confidence</strong> = how reliable the signal looks based on source quality and supporting context.</p>
                  <p><strong>Coverage</strong> = the share of expected buying volume DammBuy suggests securing now.</p>
                </div>
              </details>
            </div>
          </div>
        </div>
        <ActionPlanTable priorities={payload.priorities} />
      </section>

      <div className="two-column-layout">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Decision memo</span>
              <h3>Executive summary</h3>
            </div>
          </div>
          <p>{payload.memo}</p>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">Follow-up triggers</span>
              <h3>What would change the recommendation</h3>
            </div>
          </div>
          <ul className="trigger-list">
            {payload.triggers.map((trigger) => (
              <li key={trigger}>{trigger}</li>
            ))}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
