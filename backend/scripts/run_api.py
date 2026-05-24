from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.getenv("SMARTBUY_API_PORT", "8002"))
    reload_enabled = os.getenv("SMARTBUY_API_RELOAD", "1") != "0"
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    main()
