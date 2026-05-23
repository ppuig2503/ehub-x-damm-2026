"use client";

import { useEffect, useState } from "react";

import {
  CALA_REFRESH_EVENT,
  CalaRefreshClientState,
  readRefreshState,
} from "@/lib/refresh-state";

function formatElapsedLabel(startedAt: number | null, now: number) {
  if (!startedAt) {
    return "";
  }

  const elapsedSeconds = Math.max(0, Math.floor((now - startedAt) / 1000));
  return elapsedSeconds > 0 ? ` • ${elapsedSeconds}s elapsed` : "";
}

export function GlobalRefreshStatus() {
  const [state, setState] = useState<CalaRefreshClientState>(() => readRefreshState());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const handleStateChange = (event: Event) => {
      const customEvent = event as CustomEvent<CalaRefreshClientState>;
      if (customEvent.detail) {
        setState(customEvent.detail);
        return;
      }
      setState(readRefreshState());
    };

    const handleStorage = () => setState(readRefreshState());

    window.addEventListener(CALA_REFRESH_EVENT, handleStateChange as EventListener);
    window.addEventListener("storage", handleStorage);

    return () => {
      window.removeEventListener(CALA_REFRESH_EVENT, handleStateChange as EventListener);
      window.removeEventListener("storage", handleStorage);
    };
  }, []);

  useEffect(() => {
    if (!state.active) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setNow(Date.now());
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [state.active]);

  if (!state.active) {
    return null;
  }

  return (
    <div className="global-refresh-banner" aria-live="polite">
      <div className="refresh-spinner" aria-hidden="true" />
      <div className="global-refresh-copy">
        <strong>Cala refresh in progress</strong>
        <span>
          {state.message || "Queries are still running in Cala."}
          {formatElapsedLabel(state.startedAt, now)}
        </span>
      </div>
    </div>
  );
}
