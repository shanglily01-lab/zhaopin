"""个人/企业控制台 + 消息（投递）。"""
from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..db import execute, fetch_all, fetch_one
from ..security import current_company, current_resume, current_user
from ..templating import render

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard")
async def dashboard(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.get("iscom"):
        company = current_company(user)
        jobs = []
        applicants = []
        if company:
            jobs = fetch_all(
                """
                SELECT id, dname, cname, salary, isremote, isall, urg, ddate, isopera
                FROM t_degree WHERE cid=%s ORDER BY id DESC LIMIT 50
                """,
                (company["id"],),
            )
            applicants = fetch_all(
                """
                SELECT m.id, m.mdate, m.isread, m.did, m.sendid,
                       d.dname AS job_name,
                       u.uname AS applicant_name,
                       r.id AS resume_id, r.nick, r.degree, r.cname AS role_cn,
                       r.salary, r.skills
                FROM t_mess m
                LEFT JOIN t_degree d ON d.id=m.did
                LEFT JOIN t_user u ON u.id=m.sendid
                LEFT JOIN t_resume r ON r.uid=m.sendid
                WHERE m.uid=%s
                ORDER BY m.id DESC LIMIT 50
                """,
                (user["id"],),
            )
        return render(
            request, "company_dashboard.html",
            company=company, jobs=jobs, applicants=applicants,
        )
    # 个人
    resume = current_resume(user)
    applies = fetch_all(
        """
        SELECT m.id, m.mdate, m.isread, m.did,
               d.dname, d.cname AS role_cn, d.salary, d.cid,
               c.cname AS company_name, c.clogo
        FROM t_mess m
        LEFT JOIN t_degree d ON d.id=m.did
        LEFT JOIN t_company c ON c.id=d.cid
        WHERE m.sendid=%s
        ORDER BY m.id DESC LIMIT 50
        """,
        (user["id"],),
    )
    return render(request, "user_dashboard.html", resume=resume, applies=applies)


@router.post("/jobs/{job_id}/apply")
async def apply_job(request: Request, job_id: int):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.get("iscom"):
        raise HTTPException(403, "请使用个人账号投递")
    job = fetch_one("SELECT cid FROM t_degree WHERE id=%s", (job_id,))
    if not job:
        raise HTTPException(404, "职位不存在")
    target_user = fetch_one(
        "SELECT id FROM t_user WHERE cid=%s AND iscom=1 ORDER BY id ASC LIMIT 1",
        (job["cid"],),
    )
    target_uid = target_user["id"] if target_user else 0
    dup = fetch_one(
        "SELECT id FROM t_mess WHERE did=%s AND sendid=%s",
        (job_id, user["id"]),
    )
    if not dup:
        execute(
            """
            INSERT INTO t_mess (uid, mdate, did, sendid, isread)
            VALUES (%s, %s, %s, %s, 0)
            """,
            (target_uid, dt.date.today(), job_id, user["id"]),
        )
    return RedirectResponse(url=f"/jobs/{job_id}?applied=1", status_code=303)


@router.post("/api/messages/{mid}/read")
async def mark_read(request: Request, mid: int):
    user = current_user(request)
    if not user:
        raise HTTPException(401)
    execute("UPDATE t_mess SET isread=1 WHERE id=%s AND uid=%s", (mid, user["id"]))
    return {"ok": True}
