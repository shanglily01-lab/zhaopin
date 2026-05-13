"""Gemini AI 助手：润色职位描述 / 简历亮点。"""
from __future__ import annotations

import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from google import genai

        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as exc:
        logger.error("init gemini failed: %s", exc)
        _client = None
    return _client


def generate(prompt: str, model: str = "gemini-2.0-flash") -> Optional[str]:
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        return (resp.text or "").strip()
    except Exception as exc:
        logger.error("gemini call failed: %s", exc)
        return None


def polish_job_description(role: str, raw: str) -> Optional[str]:
    prompt = (
        f"你是 Web3 招聘平台的文案助手。请把下面这段【{role}】岗位描述\n"
        f"改写得更专业、有吸引力，保留全部关键信息，使用中文，分段用空行：\n\n{raw}\n"
    )
    return generate(prompt)


def polish_resume_advantage(role: str, raw: str) -> Optional[str]:
    prompt = (
        f"你是简历润色助手。求职者目标岗位是【{role}】。\n"
        "请把下面这段【个人优势】润色得更具体、量化、有说服力，使用中文，120 字内：\n\n"
        f"{raw}\n"
    )
    return generate(prompt)
