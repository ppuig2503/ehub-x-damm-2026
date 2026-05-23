export const CALA_REFRESH_STORAGE_KEY = "smartbuy.calaRefreshState";
export const CALA_REFRESH_EVENT = "smartbuy:cala-refresh-state";

export type CalaRefreshClientState = {
  active: boolean;
  startedAt: number | null;
  message: string | null;
};

export function readRefreshState(): CalaRefreshClientState {
  if (typeof window === "undefined") {
    return {
      active: false,
      startedAt: null,
      message: null,
    };
  }

  try {
    const rawValue = window.localStorage.getItem(CALA_REFRESH_STORAGE_KEY);
    if (!rawValue) {
      return {
        active: false,
        startedAt: null,
        message: null,
      };
    }

    const parsed = JSON.parse(rawValue) as Partial<CalaRefreshClientState>;
    return {
      active: parsed.active === true,
      startedAt: typeof parsed.startedAt === "number" ? parsed.startedAt : null,
      message: typeof parsed.message === "string" ? parsed.message : null,
    };
  } catch {
    return {
      active: false,
      startedAt: null,
      message: null,
    };
  }
}

export function writeRefreshState(state: CalaRefreshClientState) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(CALA_REFRESH_STORAGE_KEY, JSON.stringify(state));
  window.dispatchEvent(new CustomEvent(CALA_REFRESH_EVENT, { detail: state }));
}
