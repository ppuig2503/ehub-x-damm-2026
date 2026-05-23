"use client";

import { useState, useTransition } from "react";

import { evaluateScenario } from "@/lib/api";
import { actionLabel, titleize } from "@/lib/format";
import {
  CommodityOverview,
  ScenarioCatalog,
  ScenarioInput,
  ScenarioResult,
} from "@/lib/types";

type ScenarioLabProps = {
  overview: CommodityOverview[];
  catalog: ScenarioCatalog;
  initialResult: ScenarioResult;
};

function buildDefaults(catalog: ScenarioCatalog, commodity: string): ScenarioInput {
  const values = Object.fromEntries(
    catalog.variables.map((item) => [item.id, item.default]),
  ) as Record<string, string | number>;

  return {
    commodity,
    energy_cost_shock: Number(values.energy_cost_shock ?? 0),
    oil_shock: Number(values.oil_shock ?? 0),
    supply_disruption: (values.supply_disruption ?? "none") as ScenarioInput["supply_disruption"],
    demand_outlook: (values.demand_outlook ?? "neutral") as ScenarioInput["demand_outlook"],
    inventory_level: (values.inventory_level ?? "normal") as ScenarioInput["inventory_level"],
    geopolitical_risk: (values.geopolitical_risk ?? "medium") as ScenarioInput["geopolitical_risk"],
    weather_risk: (values.weather_risk ?? "medium") as ScenarioInput["weather_risk"],
    coverage_secured: (values.coverage_secured ?? "0") as ScenarioInput["coverage_secured"],
  };
}

export function ScenarioLab({ overview, catalog, initialResult }: ScenarioLabProps) {
  const [selectedCommodity, setSelectedCommodity] = useState(overview[0]?.id ?? "aluminium");
  const [formState, setFormState] = useState<ScenarioInput>(() =>
    buildDefaults(catalog, overview[0]?.id ?? "aluminium"),
  );
  const [result, setResult] = useState<ScenarioResult | null>(initialResult);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const requestScenario = (nextState: ScenarioInput) => {
    startTransition(() => {
      void (async () => {
        try {
          setResult(await evaluateScenario(nextState));
          setError(null);
        } catch (issue) {
          setError(issue instanceof Error ? issue.message : "Scenario evaluation failed.");
        }
      })();
    });
  };

  const updateField = (field: keyof ScenarioInput, value: string) => {
    setFormState((current) => ({
      ...current,
      commodity: selectedCommodity,
      [field]:
        field === "energy_cost_shock" || field === "oil_shock" ? Number(value) : value,
    }));
  };

  const handleCommodityChange = (nextCommodity: string) => {
    const nextState = buildDefaults(catalog, nextCommodity);
    setSelectedCommodity(nextCommodity);
    setFormState(nextState);
    requestScenario(nextState);
  };

  const submit = () => {
    requestScenario({ ...formState, commodity: selectedCommodity });
  };

  return (
    <div className="scenario-layout">
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Scenario setup</span>
            <h3>Stress the recommendation</h3>
          </div>
        </div>
        <div className="field-grid">
          <label className="field">
            <span>Commodity</span>
            <select
              value={selectedCommodity}
              onChange={(event) => handleCommodityChange(event.target.value)}
            >
              {overview.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          {catalog.variables.map((variable) => {
            if (!variable.applies_to.includes(selectedCommodity)) {
              return null;
            }

            if (variable.type === "range") {
              return (
                <label key={variable.id} className="field">
                  <span>{variable.label}</span>
                  <input
                    type="range"
                    min={variable.min ?? 0}
                    max={variable.max ?? 100}
                    step={variable.step ?? 1}
                    value={String(formState[variable.id as keyof ScenarioInput])}
                    onChange={(event) => updateField(variable.id as keyof ScenarioInput, event.target.value)}
                  />
                  <strong>{formState[variable.id as keyof ScenarioInput]}</strong>
                </label>
              );
            }

            return (
              <label key={variable.id} className="field">
                <span>{variable.label}</span>
                <select
                  value={String(formState[variable.id as keyof ScenarioInput])}
                  onChange={(event) => updateField(variable.id as keyof ScenarioInput, event.target.value)}
                >
                  {(variable.options || []).map((option) => (
                    <option key={option} value={option}>
                      {titleize(option)}
                    </option>
                  ))}
                </select>
              </label>
            );
          })}
        </div>
        <button type="button" className="action-button" onClick={submit} disabled={isPending}>
          {isPending ? "Recalculating..." : "Generate buying plan"}
        </button>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Result</span>
            <h3>Before vs after</h3>
          </div>
        </div>
        {result ? (
          <div className="scenario-result">
            <div className="scenario-score-grid">
              <div className="hero-metric">
                <span>Base risk</span>
                <strong>{Math.round(result.base_risk_score)}</strong>
              </div>
              <div className="hero-metric">
                <span>New risk</span>
                <strong>{Math.round(result.new_risk_score)}</strong>
              </div>
              <div className="hero-metric">
                <span>Delta</span>
                <strong>{result.delta > 0 ? "+" : ""}{result.delta.toFixed(1)}</strong>
              </div>
            </div>
            <p className="scenario-callout">
              {actionLabel(result.recommendation.recommended_action)} | {result.recommendation.suggested_coverage} |{" "}
              {result.recommendation.suggested_horizon}
            </p>
            <p>{result.narrative}</p>
            <div className="driver-list compact">
              {result.driver_impacts.map((item) => (
                <div key={item.driver} className="driver-row compact">
                  <span>{titleize(item.driver)}</span>
                  <strong>{item.contribution > 0 ? "+" : ""}{item.contribution.toFixed(1)}</strong>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="small-muted">Evaluating the base scenario...</p>
        )}
        {error ? <p className="error-text">{error}</p> : null}
      </section>
    </div>
  );
}
