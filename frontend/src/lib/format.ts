import { RecommendedAction, RefreshStatus } from "@/lib/types";

export function formatPercent(value: number) {
  return `${Math.round(value)}%`;
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export function titleize(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function actionLabel(action: RecommendedAction) {
  const labels: Record<RecommendedAction, string> = {
    buy: "Buy",
    wait: "Wait",
    hedge: "Hedge",
    monitor: "Monitor",
  };
  return labels[action];
}

export function refreshLabel(status: RefreshStatus) {
  const labels: Record<RefreshStatus, string> = {
    seed: "Seed",
    fallback: "Fallback",
    live: "Live",
  };
  return labels[status];
}

export function riskTone(score: number) {
  if (score >= 75) {
    return "critical";
  }
  if (score >= 55) {
    return "warning";
  }
  if (score >= 40) {
    return "watch";
  }
  return "calm";
}

