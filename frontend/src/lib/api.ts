import {
  ActionPlanResponse,
  CommodityDetail,
  OverviewResponse,
  RefreshResponse,
  ScenarioCatalog,
  ScenarioInput,
  ScenarioResult,
  SignalsResponse,
} from "@/lib/types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1";

function getApiBaseUrl() {
  return (
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    DEFAULT_API_BASE_URL
  );
}

export const browserApiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL;

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export function getOverview() {
  return fetchJson<OverviewResponse>("/overview");
}

export function getCommodityDetail(id: string) {
  return fetchJson<CommodityDetail>(`/commodities/${id}`);
}

export function getSignals(query = "") {
  return fetchJson<SignalsResponse>(`/signals${query ? `?${query}` : ""}`);
}

export function getScenarioCatalog() {
  return fetchJson<ScenarioCatalog>("/scenarios/catalog");
}

export function getActionPlan() {
  return fetchJson<ActionPlanResponse>("/action-plan");
}

export async function evaluateScenario(input: ScenarioInput) {
  const response = await fetch(`${browserApiBaseUrl}/scenarios/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!response.ok) {
    throw new Error("Scenario evaluation failed.");
  }

  return response.json() as Promise<ScenarioResult>;
}

export async function refreshSignals() {
  const response = await fetch(`${browserApiBaseUrl}/cala/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

  if (!response.ok) {
    throw new Error("Refresh failed.");
  }

  return response.json() as Promise<RefreshResponse>;
}

export function evaluateScenarioServer(input: ScenarioInput) {
  return fetchJson<ScenarioResult>("/scenarios/evaluate", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
