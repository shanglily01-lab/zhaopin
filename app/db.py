"""MySQL 连接封装（PyMySQL，DictCursor）。

简单连接池：用 contextmanager + 每次新建连接的方式保证线程安全；
小规模流量足够，且与现有数据库兼容。
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterable, Sequence

import pymysql
from pymysql.cursors import DictCursor

from .config import settings

logger = logging.getLogger(__name__)


def _new_conn() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASS,
        database=settings.DB_NAME,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
        connect_timeout=10,
    )


@contextmanager
def get_conn():
    conn = _new_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception as exc:
            logger.error("rollback failed: %s", exc)
        raise
    finally:
        try:
            conn.close()
        except Exception as exc:
            logger.error("close failed: %s", exc)


def fetch_all(sql: str, args: Sequence[Any] | None = None) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, args or ())
        return list(cur.fetchall())


def fetch_one(sql: str, args: Sequence[Any] | None = None) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchone()


def execute(sql: str, args: Sequence[Any] | None = None) -> int:
    """执行写入，返回 lastrowid 或 affected rows。"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, args or ())
        return cur.lastrowid or cur.rowcount


def execute_many(sql: str, rows: Iterable[Sequence[Any]]) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        return cur.executemany(sql, list(rows))
