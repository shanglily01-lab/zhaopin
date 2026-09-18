"""配置：从 .env 加载，禁止硬编码。"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASS: str = os.getenv("DB_PASS", "")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "5020"))

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    TELEGRAM_GROUP: str = os.getenv("TELEGRAM_GROUP", "https://t.me/jobsofweb3")
    AD_URL: str = os.getenv(
        "AD_URL",
        "https://chainpoker.io?wsp=eyJjaWQiOiIxMDAwMSIsImFpZCI6IjUwMDA1In0%3D",
    )

    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    STATIC_DIR: Path = ROOT_DIR / "app" / "static"
    TEMPLATE_DIR: Path = ROOT_DIR / "app" / "templates"

    SESSION_COOKIE: str = "zp_sid"
    SESSION_MAX_AGE: int = 60 * 60 * 24 * 7  # 7 天


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
