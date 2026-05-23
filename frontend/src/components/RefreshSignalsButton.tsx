"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { refreshSignals } from "@/lib/api";

export function RefreshSignalsButton() {
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const handleRefresh = () => {
    startTransition(() => {
      void (async () => {
      try {
        const response = await refreshSignals();
        setMessage(`${response.status.toUpperCase()}: ${response.message}`);
        router.refresh();
      } catch (error) {
        setMessage(
          error instanceof Error ? error.message : "Signal refresh failed.",
        );
      }
      })();
    });
  };

  return (
    <div className="refresh-block">
      <button type="button" className="action-button" onClick={handleRefresh} disabled={isPending}>
        {isPending ? "Refreshing..." : "Refresh from Cala"}
      </button>
      <p className="small-muted">{message || "Live refresh attempts Cala first, then falls back locally."}</p>
    </div>
  );
}
