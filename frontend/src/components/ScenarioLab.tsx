"use client";

import { useState, useTransition } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { evaluateScenario, searchCala } from "@/lib/api";
import { actionLabel, titleize } from "@/lib/format";
import {
  CalaSearchResponse,
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
  const [searchQuery, setSearchQuery] = useState("How did the aluminium price evolve in the different past geopolitical events?");
  const [searchResult, setSearchResult] = useState<CalaSearchResponse | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

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

  const submitSearch = async () => {
    const trimmedQuery = searchQuery.trim();
    if (!trimmedQuery) {
      setSearchError("Enter a question for Cala.");
      return;
    }

    setIsSearching(true);
    setSearchError(null);
    try {
      const response = await searchCala(trimmedQuery);
      setSearchResult(response);
    } catch (issue) {
      setSearchError(issue instanceof Error ? issue.message : "Cala search failed.");
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
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
                className="commodity-select"
                key={selectedCommodity}
                defaultValue={selectedCommodity}
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

      <section className="panel scenario-search-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">Cala Search</span>
            <h3>Ask Cala in natural language</h3>
          </div>
        </div>
        <div className="scenario-search-layout">
          <label className="field scenario-search-field">
            <span>Question</span>
            <textarea
              className="scenario-search-input"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="How did the aluminium price evolve during past geopolitical events?"
              rows={4}
            />
          </label>
          <div className="scenario-search-actions">
            <button type="button" className="action-button" onClick={() => void submitSearch()} disabled={isSearching}>
              {isSearching ? "Asking Cala..." : "Ask Cala"}
            </button>
            <p className="small-muted">
              Use broader market questions here. Cala answers in natural language and may take a few minutes.
            </p>
          </div>
        </div>
        {searchError ? <p className="error-text">{searchError}</p> : null}
        {searchResult ? (
          <div className="scenario-search-result">
            <p className="scenario-search-question">
              <strong>Query:</strong> {searchResult.query}
            </p>
            <div className="scenario-search-answer">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {searchResult.content}
              </ReactMarkdown>
            </div>
            {searchResult.entities.length ? (
              <div className="scenario-search-meta">
                <strong>Entities</strong>
                <div className="tag-list">
                  {searchResult.entities.map((item) => (
                    <span key={item} className="tag">{item}</span>
                  ))}
                </div>
              </div>
            ) : null}
            {searchResult.context.length ? (
              <div className="scenario-search-meta">
                <strong>Context</strong>
                <ul className="trigger-list">
                  {searchResult.context.map((item, index) => (
                    <li key={`context-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {searchResult.explainability.length ? (
              <div className="scenario-search-meta">
                <strong>Explainability</strong>
                <ul className="trigger-list">
                  {searchResult.explainability.map((item, index) => (
                    <li key={`explainability-${index}`}>{item}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <p className="small-muted">Ask a market question and Cala will answer in natural language here.</p>
        )}
      </section>
    </>
  );
}
