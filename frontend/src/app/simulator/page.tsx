import { AppShell } from "@/components/AppShell";
import { ScenarioLab } from "@/components/ScenarioLab";
import { evaluateScenarioServer, getOverview, getScenarioCatalog } from "@/lib/api";
import { ScenarioInput } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function SimulatorPage() {
  const [overview, catalog] = await Promise.all([getOverview(), getScenarioCatalog()]);
  const defaults = Object.fromEntries(
    catalog.variables.map((item) => [item.id, item.default]),
  ) as Record<string, string | number>;
  const initialScenario: ScenarioInput = {
    commodity: overview.commodities[0]?.id ?? "aluminium",
    energy_cost_shock: Number(defaults.energy_cost_shock ?? 0),
    oil_shock: Number(defaults.oil_shock ?? 0),
    supply_disruption: (defaults.supply_disruption ?? "none") as ScenarioInput["supply_disruption"],
    demand_outlook: (defaults.demand_outlook ?? "neutral") as ScenarioInput["demand_outlook"],
    inventory_level: (defaults.inventory_level ?? "normal") as ScenarioInput["inventory_level"],
    geopolitical_risk: (defaults.geopolitical_risk ?? "medium") as ScenarioInput["geopolitical_risk"],
    weather_risk: (defaults.weather_risk ?? "medium") as ScenarioInput["weather_risk"],
    coverage_secured: (defaults.coverage_secured ?? "0") as ScenarioInput["coverage_secured"],
  };
  const initialResult = await evaluateScenarioServer(initialScenario);

  return (
    <AppShell currentPath="/simulator">
      <section className="hero-panel">
        <div className="hero-copy">
          <span className="eyebrow">What-if Simulator</span>
          <h2>Stress a commodity before you commit to the buying plan.</h2>
          <p>
            This is the demo moment: tweak energy, inventories, geopolitics, or
          weather and let the decision engine explain the shift.
          </p>
        </div>
      </section>
      <ScenarioLab
        overview={overview.commodities}
        catalog={catalog}
        initialResult={initialResult}
      />
    </AppShell>
  );
}
