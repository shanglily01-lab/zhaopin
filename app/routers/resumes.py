"""简历列表 / 详情 / 编辑。"""
from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..ai import polish_resume_advantage
from ..db import execute, fetch_all, fetch_one
from ..security import current_user
from ..templating import render

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/resumes")
async def resumes_list(
    request: Request,
    kw: str = Query(""),
    wtype: str = Query(""),
    edu: str = Query(""),
    page: int = Query(1, ge=1),
):
    page_size = 20
    where = ["COALESCE(r.isvis,1)=1", "COALESCE(r.isopera,1)=1"]
    args: list = []
    if kw:
        where.append("(r.degree LIKE %s OR r.cname LIKE %s OR r.skills LIKE %s OR r.nick LIKE %s)")
        like = f"%{kw}%"
        args.extend([like, like, like, like])
    if wtype in ("0", "1", "2"):
        where.append("r.wtype=%s")
        args.append(int(wtype))
    if edu:
        where.append("r.edu=%s")
        args.append(int(edu))

    where_sql = " AND ".join(where)
    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM t_resume r WHERE {where_sql}", args,
    )["c"]
    offset = (page - 1) * page_size
    rows = fetch_all(
        f"""
        SELECT r.id, r.nick, r.addr, r.isen, r.degree, r.cname, r.wtype,
               r.edu, r.exp, r.salary, r.skills, r.indate, r.logo
        FROM t_resume r
        WHERE {where_sql}
        ORDER BY r.indate DESC, r.id DESC
        LIMIT %s OFFSET %s
        """,
        args + [page_size, offset],
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return render(
        request,
        "resumes_list.html",
        resumes=rows, total=total, page=page, pages=pages,
        kw=kw, wtype=wtype, edu=edu,
    )


@router.get("/resumes/{rid}")
async def resume_detail(request: Request, rid: int):
    user = current_user(request)
    resume = fetch_one("SELECT * FROM t_resume WHERE id=%s", (rid,))
    if not resume:
        raise HTTPException(404, "简历不存在")
    owner = bool(user and user.get("id") == resume.get("uid"))
    if not owner and not user:
        return render(request, "resume_detail.html", resume=resume, restricted=True, owner=False)
    if not owner and resume.get("isvis") == 0:
        return render(request, "resume_detail.html", resume=resume, restricted=True, owner=False)
    return render(request, "resume_detail.html", resume=resume, restricted=False, owner=owner)


@router.get("/me/resume")
async def my_resume_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.get("iscom"):
        return RedirectResponse("/dashboard", status_code=303)
    resume = fetch_one(
        "SELECT * FROM t_resume WHERE uid=%s ORDER BY id DESC LIMIT 1",
        (user["id"],),
    )
    return render(request, "resume_edit.html", resume=resume)


@router.post("/me/resume")
async def my_resume_save(
    request: Request,
    nick: str = Form(""),
    addr: str = Form(""),
    degree: str = Form(""),
    cname: str = Form(""),
    wtype: int = Form(1),
    edu: int = Form(0),
    exp: int = Form(0),
    isen: int = Form(0),
    isall: int = Form(1),
    salary: str = Form(""),
    skills: str = Form(""),
    pexp: str = Form(""),
    adv: str = Form(""),
    ws: str = Form(""),
    tg: str = Form(""),
    isvis: int = Form(1),
):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if user.get("iscom"):
        raise HTTPException(403, "企业账号无法填写简历")
    existing = fetch_one(
        "SELECT id FROM t_resume WHERE uid=%s ORDER BY id DESC LIMIT 1",
        (user["id"],),
    )
    if existing:
        execute(
            """
            UPDATE t_resume SET nick=%s, addr=%s, degree=%s, cname=%s, wtype=%s,
                edu=%s, exp=%s, isen=%s, isall=%s, salary=%s, skills=%s,
                pexp=%s, adv=%s, ws=%s, tg=%s, isvis=%s, isopera=1
            WHERE id=%s
            """,
            (
                nick.strip(), addr.strip(), degree.strip(), cname.strip(),
                int(wtype), int(edu), int(exp), int(isen), int(isall),
                salary.strip(), skills.strip(), pexp.strip(), adv.strip(),
                ws.strip(), tg.strip(), int(isvis), existing["id"],
            ),
        )
        rid = existing["id"]
    else:
        rid = execute(
            """
            INSERT INTO t_resume
            (uid, indate, isvis, nick, addr, isen, ws, tg, degree, cname,
             wtype, edu, exp, salary, skills, pexp, adv, isall, isopera)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            """,
            (
                user["id"], dt.date.today(), int(isvis), nick.strip(), addr.strip(),
                int(isen), ws.strip(), tg.strip(), degree.strip(), cname.strip(),
                int(wtype), int(edu), int(exp), salary.strip(), skills.strip(),
                pexp.strip(), adv.strip(), int(isall),
            ),
        )
        execute("UPDATE t_user SET rid=%s WHERE id=%s", (rid, user["id"]))
    return RedirectResponse(url=f"/resumes/{rid}", status_code=303)


@router.post("/api/resumes/polish")
async def api_polish_resume(request: Request, degree: str = Form(""), adv: str = Form("")):
    if not adv.strip():
        return {"ok": False, "msg": "请先填写个人优势"}
    text = polish_resume_advantage(degree or "Web3 岗位", adv)
    if not text:
        return {"ok": False, "msg": "AI 不可用或调用失败"}
    return {"ok": True, "text": text}
