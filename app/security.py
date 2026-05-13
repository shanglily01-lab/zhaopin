"""会话与密码工具。

密码：bcrypt（库存遗留密码若是明文 / md5 也兼容判定）。
会话：用 itsdangerous 签名 cookie 存 user_id。
"""
from __future__ import annotations

import hashlib
import logging
from typing import Optional

import bcrypt
from fastapi import Request
from itsdangerous import BadSignature, URLSafeSerializer

from .config import settings
from .db import fetch_one

logger = logging.getLogger(__name__)
_serializer = URLSafeSerializer(settings.SECRET_KEY, salt="zhaopin-session")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, stored: str) -> bool:
    """支持 bcrypt / MD5 / 明文（兼容遗留数据）。"""
    if not stored:
        return False
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), stored.encode("utf-8"))
        except Exception as exc:
            logger.error("bcrypt verify failed: %s", exc)
            return False
    if len(stored) == 32:
        md5 = hashlib.md5(plain.encode("utf-8")).hexdigest()
        return md5 == stored
    return plain == stored


def sign_session(user_id: int) -> str:
    return _serializer.dumps({"uid": int(user_id)})


def read_session(token: str | None) -> Optional[int]:
    if not token:
        return None
    try:
        data = _serializer.loads(token)
        return int(data.get("uid"))
    except BadSignature:
        return None
    except Exception as exc:
        logger.error("session decode error: %s", exc)
        return None


def current_user(request: Request) -> Optional[dict]:
    """从请求 cookie 中解析当前登录用户行，未登录返回 None。"""
    token = request.cookies.get(settings.SESSION_COOKIE)
    uid = read_session(token)
    if not uid:
        return None
    return fetch_one("SELECT * FROM t_user WHERE id=%s", (uid,))


def current_company(user: dict | None) -> Optional[dict]:
    if not user or not user.get("iscom") or not user.get("cid"):
        return None
    return fetch_one("SELECT * FROM t_company WHERE id=%s", (user["cid"],))


def current_resume(user: dict | None) -> Optional[dict]:
    if not user or user.get("iscom"):
        return None
    rid = user.get("rid")
    if rid:
        return fetch_one("SELECT * FROM t_resume WHERE id=%s", (rid,))
    return fetch_one(
        "SELECT * FROM t_resume WHERE uid=%s ORDER BY id DESC LIMIT 1",
        (user["id"],),
    )
