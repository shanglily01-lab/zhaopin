"""开发启动入口：python run.py。生产建议用 uvicorn 直接启动。"""
from __future__ import annotations

import sys

import uvicorn

from app.config import settings


def main() -> None:
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.SERVER_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
