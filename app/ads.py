"""可替换广告图：覆盖 app/static/img/ads/ 下同名文件即可，无需改代码。"""
from __future__ import annotations

from .config import settings

AD_DIR = settings.STATIC_DIR / "img" / "ads"
_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".svg")


def _url_for(path) -> str:
    ver = int(path.stat().st_mtime)
    return f"/static/img/ads/{path.name}?v={ver}"


def resolve(*names: str) -> str:
    """按文件名顺序查找，命中则返回带时间戳的 URL，方便换图后立刻刷新缓存。"""
    for name in names:
        for ext in _EXTS:
            path = AD_DIR / f"{name}{ext}"
            if path.is_file():
                return _url_for(path)
    return ""


def context() -> dict:
    side = resolve("side")
    return {
        "ad_side_left": resolve("side-left", "side"),
        "ad_side_right": resolve("side-right", "side"),
        "ad_poster": resolve("poster", "side"),
        "ad_mobile": resolve("mobile", "side-left", "side"),
        "ad_qr": resolve("qr"),
        "ad_has_side": bool(side or resolve("side-left") or resolve("side-right")),
    }
