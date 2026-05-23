"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { refreshSignals } from "@/lib/api";
import { writeRefreshState } from "@/lib/refresh-state";

export function RefreshSignalsButton() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!isRefreshing) {
      return;
    }

    const startedAt = Date.now();
    const intervalId = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [isRefreshing]);

  const handleRefresh = async () => {
    setElapsedSeconds(0);
    const loadingMessage = "Launching Cala queries. This can take a while while Cala resolves the request.";
    setMessage(loadingMessage);
    setIsRefreshing(true);
    writeRefreshState({
      active: true,
      startedAt: Date.now(),
      message: loadingMessage,
    });
    try {
      const response = await refreshSignals();
      setMessage(`${response.status.toUpperCase()}: ${response.message}`);
      writeRefreshState({
        active: false,
        startedAt: null,
        message: null,
      });
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Signal refresh failed.",
      );
      writeRefreshState({
        active: false,
        startedAt: null,
        message: null,
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  return (
    <div className={`refresh-block ${isRefreshing ? "is-loading" : ""}`}>
      <button type="button" className="action-button" onClick={() => void handleRefresh()} disabled={isRefreshing}>
        {isRefreshing ? "Running Cala queries..." : "Refresh from Cala"}
      </button>
      <p className="small-muted">
        {message || "Live refresh attempts Cala first, then falls back locally."}
      </p>
      {isRefreshing ? (
        <div className="refresh-activity" aria-live="polite">
          <div className="refresh-spinner" aria-hidden="true" />
          <div className="refresh-copy">
            <strong>Waiting for Cala</strong>
            <span>
              Query execution in progress{elapsedSeconds > 0 ? ` • ${elapsedSeconds}s elapsed` : ""}.
            </span>
          </div>
        </div>
      ) : null}
      <div className={`refresh-progress ${isRefreshing ? "active" : ""}`} aria-hidden="true" />
    </div>
  );
}
