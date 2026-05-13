"""公司列表 / 详情 / 资料编辑。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from ..db import execute, fetch_all, fetch_one
from ..security import current_user
from ..templating import render

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/companies")
async def companies_list(
    request: Request,
    kw: str = Query(""),
    ctype: str = Query(""),
    page: int = Query(1, ge=1),
):
    page_size = 20
    where = ["c.cname IS NOT NULL", "c.cname<>''"]
    args: list = []
    if kw:
        where.append("(c.cname LIKE %s OR c.cdesc LIKE %s OR c.cim LIKE %s)")
        like = f"%{kw}%"
        args.extend([like, like, like])
    if ctype:
        where.append("c.ctype=%s")
        args.append(int(ctype))
    where_sql = " AND ".join(where)
    total = fetch_one(
        f"SELECT COUNT(*) AS c FROM t_company c WHERE {where_sql}", args
    )["c"]
    offset = (page - 1) * page_size
    rows = fetch_all(
        f"""
        SELECT c.id, c.cname, c.clogo, c.ctype, c.wrks, c.chains, c.cim, c.cnet,
               (SELECT COUNT(*) FROM t_degree d WHERE d.cid=c.id AND COALESCE(d.isopera,1)=1) AS job_count
        FROM t_company c
        WHERE {where_sql}
        ORDER BY job_count DESC, c.id DESC
        LIMIT %s OFFSET %s
        """,
        args + [page_size, offset],
    )
    pages = max(1, (total + page_size - 1) // page_size)
    return render(
        request,
        "companies_list.html",
        companies=rows, total=total, page=page, pages=pages, kw=kw, ctype=ctype,
    )


@router.get("/companies/{cid}")
async def company_detail(request: Request, cid: int):
    company = fetch_one("SELECT * FROM t_company WHERE id=%s", (cid,))
    if not company:
        raise HTTPException(404, "公司不存在")
    jobs = fetch_all(
        """
        SELECT id, dname, cname, salary, isremote, isall, urg, ddate, skills, waddr
        FROM t_degree WHERE cid=%s AND COALESCE(isopera,1)=1
        ORDER BY ddate DESC, id DESC LIMIT 50
        """,
        (cid,),
    )
    return render(request, "company_detail.html", company=company, jobs=jobs)


@router.get("/me/company")
async def my_company_page(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if not user.get("iscom"):
        raise HTTPException(403, "仅企业账号可编辑公司资料")
    company = fetch_one("SELECT * FROM t_company WHERE id=%s", (user.get("cid"),))
    return render(request, "company_profile.html", company=company)


@router.post("/me/company")
async def my_company_save(
    request: Request,
    cname: str = Form(...),
    cnet: str = Form(""),
    clogo: str = Form(""),
    ctype: int = Form(0),
    wrks: int = Form(0),
    chains: str = Form(""),
    cim: str = Form(""),
    cdesc: str = Form(""),
    tg: str = Form(""),
    ws: str = Form(""),
    tt: str = Form(""),
    disc: str = Form(""),
    git: str = Form(""),
):
    user = current_user(request)
    if not user or not user.get("iscom"):
        raise HTTPException(403)
    cid = user.get("cid") or 0
    if cid:
        execute(
            """
            UPDATE t_company SET cname=%s, cnet=%s, clogo=%s, ctype=%s, wrks=%s,
                chains=%s, cim=%s, cdesc=%s, tg=%s, ws=%s, tt=%s, disc=%s, git=%s
            WHERE id=%s
            """,
            (cname.strip(), cnet.strip(), clogo.strip(), int(ctype), int(wrks),
             chains.strip(), cim.strip(), cdesc.strip(), tg.strip(), ws.strip(),
             tt.strip(), disc.strip(), git.strip(), cid),
        )
    else:
        cid = execute(
            """
            INSERT INTO t_company
            (cname, cnet, clogo, ctype, wrks, chains, cim, cdesc, tg, ws, tt, disc, git)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (cname.strip(), cnet.strip(), clogo.strip(), int(ctype), int(wrks),
             chains.strip(), cim.strip(), cdesc.strip(), tg.strip(), ws.strip(),
             tt.strip(), disc.strip(), git.strip()),
        )
        execute("UPDATE t_user SET cid=%s WHERE id=%s", (cid, user["id"]))
    return RedirectResponse(url=f"/companies/{cid}", status_code=303)
