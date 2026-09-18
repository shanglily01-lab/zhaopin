"""Jinja2 模板配置 + 全局上下文。"""
from __future__ import annotations

from datetime import date, datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates

from . import dicts
from .config import settings
from .security import current_user

templates = Jinja2Templates(directory=str(settings.TEMPLATE_DIR))


def _fmt_date(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    return str(value)


def _truncate(value, length: int = 80) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= length else text[: length - 1] + "…"


templates.env.filters["fmt_date"] = _fmt_date
templates.env.filters["truncate_zh"] = _truncate
templates.env.filters["wrks_label"] = lambda v: dicts.label(dicts.WRKS, v)
templates.env.filters["ctype_label"] = lambda v: dicts.label(dicts.CTYPE, v)
templates.env.filters["edu_label"] = lambda v: dicts.label(dicts.EDU, v)
templates.env.filters["exp_label"] = lambda v: dicts.label(dicts.EXP, v)
templates.env.filters["remote_label"] = lambda v: dicts.label(dicts.REMOTE, v)
templates.env.filters["alltime_label"] = lambda v: dicts.label(dicts.ALLTIME, v)
templates.env.filters["wtype_label"] = lambda v: dicts.label(dicts.WTYPE, v)
templates.env.filters["chains_labels"] = dicts.chain_labels
templates.env.filters["skills_list"] = dicts.parse_skills


def render(request: Request, name: str, status_code: int = 200, **ctx):
    user = current_user(request)
    base = {
        "user": user,
        "telegram_group": settings.TELEGRAM_GROUP,
        "ad_url": settings.AD_URL,
        "dicts": dicts,
    }
    base.update(ctx)
    return templates.TemplateResponse(request, name, base, status_code=status_code)
