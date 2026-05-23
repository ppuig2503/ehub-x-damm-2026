import { DriverContribution } from "@/lib/types";
import { titleize } from "@/lib/format";

type DriverBreakdownProps = {
  contributions: DriverContribution[];
};

export function DriverBreakdown({ contributions }: DriverBreakdownProps) {
  const max = Math.max(...contributions.map((item) => Math.abs(item.contribution)), 1);

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <span className="eyebrow">Driver contribution</span>
          <h3>What is moving the recommendation</h3>
        </div>
      </div>
      <div className="driver-list">
        {contributions.map((item) => {
          const width = `${(Math.abs(item.contribution) / max) * 100}%`;
          return (
            <div key={item.driver} className="driver-row">
              <div className="driver-copy">
                <span>{titleize(item.driver)}</span>
                <strong>{item.contribution > 0 ? "+" : ""}{item.contribution.toFixed(1)}</strong>
              </div>
              <div className="bar-track">
                <div
                  className={
                    item.contribution > 0 ? "bar-fill bullish" : item.contribution < 0 ? "bar-fill bearish" : "bar-fill neutral"
                  }
                  style={{ width }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

