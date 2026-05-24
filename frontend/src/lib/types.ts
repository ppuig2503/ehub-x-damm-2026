export type RefreshStatus = "seed" | "fallback" | "live";
export type RecommendedAction = "buy" | "wait" | "hedge" | "monitor";

export interface Signal {
  id: string;
  commodity: string;
  driver: string;
  event: string;
  date: string;
  region: string;
  direction: "bullish" | "bearish" | "neutral";
  impact_score: number;
  confidence: number;
  horizon: string;
  source_name: string;
  source_url: string;
  source_reference?: string | null;
  source_link_status?: "direct" | "fallback";
  evidence: string;
  mechanism: string;
  used_in_score: boolean;
}

export interface DriverContribution {
  driver: string;
  contribution: number;
  direction: "bullish" | "bearish" | "neutral";
  signals: number;
}

export interface DecisionRecommendation {
  recommended_action: RecommendedAction;
  suggested_coverage: string;
  suggested_horizon: string;
  explanation: string;
}

export interface CommodityOverview {
  id: string;
  name: string;
  region: string;
  risk_score: number;
  confidence: number;
  uncertainty_score: number;
  recommended_action: RecommendedAction;
  suggested_coverage: string;
  suggested_horizon: string;
  top_driver: string;
  change_note?: string | null;
  changed: boolean;
  refresh_status: RefreshStatus;
  proxy_label: string;
  score_history: number[];
  benchmark_history?: number[] | null;
  history_source: "cala_benchmark" | "local_fallback" | "barley_csv";
  history_label: string;
  history_note?: string | null;
  history_start?: string | null;
  history_end?: string | null;
  history_dates?: string[] | null;
  explanation: string;
}

export interface TrendPoint {
  date: string;
  value: number;
  score?: number | null;
  covid_flag?: number | null;
}

export interface CommodityDetail {
  id: string;
  name: string;
  region: string;
  risk_score: number;
  confidence: number;
  uncertainty_score: number;
  recommendation: DecisionRecommendation;
  top_bullish_drivers: string[];
  top_bearish_drivers: string[];
  driver_contributions: DriverContribution[];
  trend: TrendPoint[];
  proxy_label: string;
  proxy_value_label: string;
  latest_proxy_value: number;
  history_source: "cala_benchmark" | "local_fallback" | "barley_csv";
  history_label: string;
  history_value_label: string;
  latest_history_value: number;
  history_note?: string | null;
  signals: Signal[];
  refresh_status: RefreshStatus;
  barley_features?: Record<string, string | number> | null;
  what_changed?: string | null;
}

export interface OverviewResponse {
  generated_at: string;
  refresh_status: RefreshStatus;
  market_status: "Stable" | "Watch" | "High Risk";
  new_signals: Record<string, number>;
  commodities: CommodityOverview[];
}

export interface ScenarioVariableDefinition {
  id: string;
  label: string;
  type: "range" | "select";
  min?: number | null;
  max?: number | null;
  step?: number | null;
  default: number | string;
  options?: string[] | null;
  applies_to: string[];
}

export interface ScenarioCatalog {
  generated_at: string;
  variables: ScenarioVariableDefinition[];
}

export interface ScenarioInput {
  commodity: string;
  energy_cost_shock: number;
  oil_shock: number;
  supply_disruption: "none" | "mild" | "severe";
  demand_outlook: "weak" | "neutral" | "strong";
  inventory_level: "low" | "normal" | "high";
  geopolitical_risk: "low" | "medium" | "high";
  weather_risk: "low" | "medium" | "high";
  coverage_secured: "0" | "25" | "50" | "75";
}

export interface ScenarioResult {
  commodity: string;
  base_risk_score: number;
  new_risk_score: number;
  delta: number;
  refresh_status: RefreshStatus;
  recommendation: DecisionRecommendation;
  driver_impacts: DriverContribution[];
  narrative: string;
}

export interface SignalsResponse {
  generated_at: string;
  refresh_status: RefreshStatus;
  count: number;
  signals: Signal[];
}

export interface ActionPlanResponse {
  generated_at: string;
  refresh_status: RefreshStatus;
  priorities: CommodityOverview[];
  memo: string;
  triggers: string[];
}

export interface RefreshResponse {
  status: RefreshStatus;
  generated_at: string;
  message: string;
  signals_available: number;
  commodity_scope: string;
  driver_scope: string[];
}

export interface CalaSearchResponse {
  query: string;
  content: string;
  explainability: string[];
  context: string[];
  entities: string[];
}
