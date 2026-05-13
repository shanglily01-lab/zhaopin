"""职位列表 / 详情 / 发布。"""
from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..ai import polish_job_description
from ..db import execute, fetch_all, fetch_one
from ..security import current_company, current_user
from ..templating import render

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_filters(kw: str, remote: str, alltime: str, urg: str):
    where = ["COALESCE(d.isopera,1)=1"]
    args: list = []
    if kw:
        where.append("(d.dname LIKE %s OR d.cname LIKE %s OR d.skills LIKE %s OR c.cname LIKE %s)")
        like = f"%{kw}%"
        args.extend([like, like, like, like])
    if remote in ("0", "1", "2"):
        where.append("d.isremote=%s")
        args.append(int(remote))
    if alltime in ("0", "1", "2"):
        where.append("d.isall=%s")
        args.append(int(alltime))
    if urg == "1":
        where.append("d.urg=1")
    return " AND ".join(where), args


@router.get("/jobs")
async def jobs_list(
    request: Request,
    kw: str = Query(""),
    remote: str = Query(""),
    alltime: str = Query(""),
    urg: str = Query(""),
    page: int = Query(1, ge=1),
):
    page_size = 20
    where_sql, args = _build_filters(kw, remote, alltime, urg)
    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM t_degree d LEFT JOIN t_company c ON c.id=d.cid WHERE {where_sql}",
        args,
    )["c"]
    offset = (page - 1) * page_size
    rows = fetch_all(
        f"""
        SELECT d.id, d.dname, d.cname, d.skills, d.salary, d.waddr, d.ddate,
               d.isremote, d.isall, d.urg, d.cid,
               c.cname AS company_name, c.clogo, c.ctype, c.wrks
        FROM t_degree d
        LEFT JOIN t_company c ON c.id=d.cid
        WHERE {where_sql}
        ORDER BY d.urg DESC, d.ddate DESC, d.id DESC
        LIMIT %s OFFSET %s
        """,
        args + [page_size, offset],
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return render(
        request,
        "jobs_list.html",
        jobs=rows,
        total=total,
        page=page,
        pages=pages,
        kw=kw,
        remote=remote,
        alltime=alltime,
        urg=urg,
    )


@router.get("/jobs/new")
async def job_new_page(request: Request):
    user = current_user(request)
    if not user or not user.get("iscom"):
        return RedirectResponse("/login", status_code=303)
    company = current_company(user)
    if not company:
        return RedirectResponse("/me/company", status_code=303)
    return render(request, "post_job.html", job=None, company=company)


@router.get("/jobs/{job_id}")
async def job_detail(request: Request, job_id: int):
    job = fetch_one(
        """
        SELECT d.*, c.cname AS company_name, c.clogo, c.ctype, c.wrks, c.cim, c.cdesc,
               c.cnet, c.tg, c.ws, c.tt, c.disc
        FROM t_degree d
        LEFT JOIN t_company c ON c.id=d.cid
        WHERE d.id=%s
        """,
        (job_id,),
    )
    if not job:
        raise HTTPException(status_code=404, detail="职位不存在")
    related = fetch_all(
        """
        SELECT id, dname, cname, salary, isremote
        FROM t_degree
        WHERE cid=%s AND id<>%s AND COALESCE(isopera,1)=1
        ORDER BY id DESC LIMIT 6
        """,
        (job["cid"], job_id),
    )
    return render(request, "job_detail.html", job=job, related=related)


@router.post("/jobs/new")
async def job_create(
    request: Request,
    dname: str = Form(...),
    cname: str = Form(""),
    salary: str = Form(""),
    waddr: str = Form(""),
    skills: str = Form(""),
    isremote: int = Form(1),
    isall: int = Form(1),
    urg: int = Form(0),
    ddesc: str = Form(""),
    demark: str = Form(""),
    benefit: str = Form(""),
):
    user = current_user(request)
    if not user or not user.get("iscom"):
        raise HTTPException(403, "请使用企业账号")
    cid = user.get("cid") or 0
    if not cid:
        raise HTTPException(400, "请先完善公司资料")
    job_id = execute(
        """
        INSERT INTO t_degree
        (cid, dname, cname, urg, ddate, isremote, isall, skills, waddr,
         ddesc, demark, salary, benefit, isopera)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
        """,
        (
            cid, dname.strip(), cname.strip(), int(urg), dt.date.today(),
            int(isremote), int(isall), skills.strip(), waddr.strip(),
            ddesc.strip(), demark.strip(), salary.strip(), benefit.strip(),
        ),
    )
    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


@router.get("/jobs/{job_id}/edit")
async def job_edit_page(request: Request, job_id: int):
    user = current_user(request)
    if not user or not user.get("iscom"):
        return RedirectResponse("/login", status_code=303)
    job = fetch_one("SELECT * FROM t_degree WHERE id=%s", (job_id,))
    if not job or job["cid"] != user.get("cid"):
        raise HTTPException(403, "无权编辑该职位")
    company = current_company(user)
    return render(request, "post_job.html", job=job, company=company)


@router.post("/jobs/{job_id}/edit")
async def job_update(
    request: Request,
    job_id: int,
    dname: str = Form(...),
    cname: str = Form(""),
    salary: str = Form(""),
    waddr: str = Form(""),
    skills: str = Form(""),
    isremote: int = Form(1),
    isall: int = Form(1),
    urg: int = Form(0),
    ddesc: str = Form(""),
    demark: str = Form(""),
    benefit: str = Form(""),
    isopera: int = Form(1),
):
    user = current_user(request)
    if not user or not user.get("iscom"):
        raise HTTPException(403)
    job = fetch_one("SELECT cid FROM t_degree WHERE id=%s", (job_id,))
    if not job or job["cid"] != user.get("cid"):
        raise HTTPException(403, "无权编辑")
    execute(
        """
        UPDATE t_degree SET dname=%s, cname=%s, salary=%s, waddr=%s, skills=%s,
            isremote=%s, isall=%s, urg=%s, ddesc=%s, demark=%s, benefit=%s,
            isopera=%s
        WHERE id=%s
        """,
        (
            dname.strip(), cname.strip(), salary.strip(), waddr.strip(), skills.strip(),
            int(isremote), int(isall), int(urg), ddesc.strip(), demark.strip(),
            benefit.strip(), int(isopera), job_id,
        ),
    )
    return RedirectResponse(url=f"/jobs/{job_id}", status_code=303)


@router.post("/api/jobs/polish")
async def api_polish_job(request: Request, dname: str = Form(""), ddesc: str = Form("")):
    """AI 润色岗位描述。"""
    if not ddesc.strip():
        return {"ok": False, "msg": "原文为空"}
    text = polish_job_description(dname or "Web3 岗位", ddesc)
    if not text:
        return {"ok": False, "msg": "AI 不可用或调用失败"}
    return {"ok": True, "text": text}
