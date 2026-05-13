"""首页 + 搜索。"""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..db import fetch_all, fetch_one
from ..templating import render

router = APIRouter()


@router.get("/")
async def index(request: Request):
    hot_jobs = fetch_all(
        """
        SELECT d.id, d.dname, d.cname, d.skills, d.salary, d.waddr, d.ddate,
               d.isremote, d.isall, d.urg, d.cid,
               c.cname AS company_name, c.clogo, c.ctype
        FROM t_degree d
        LEFT JOIN t_company c ON c.id = d.cid
        WHERE COALESCE(d.isopera, 1) = 1
        ORDER BY d.ddate DESC, d.id DESC
        LIMIT 12
        """
    )
    hot_companies = fetch_all(
        """
        SELECT c.id, c.cname, c.clogo, c.ctype, c.wrks, c.cim,
               (SELECT COUNT(*) FROM t_degree d WHERE d.cid = c.id AND COALESCE(d.isopera,1)=1) AS job_count
        FROM t_company c
        WHERE c.cname IS NOT NULL AND c.cname<>''
        ORDER BY job_count DESC, c.id DESC
        LIMIT 8
        """
    )
    stats = fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM t_company WHERE cname IS NOT NULL AND cname<>'') AS company_total,
          (SELECT COUNT(*) FROM t_degree WHERE COALESCE(isopera,1)=1) AS job_total,
          (SELECT COUNT(*) FROM t_resume WHERE COALESCE(isvis,1)=1) AS resume_total
        """
    )
    return render(
        request,
        "index.html",
        hot_jobs=hot_jobs,
        hot_companies=hot_companies,
        stats=stats or {"company_total": 0, "job_total": 0, "resume_total": 0},
    )
