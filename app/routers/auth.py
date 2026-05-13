"""注册 / 登录 / 退出。"""
from __future__ import annotations

import datetime as dt
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from ..config import settings
from ..db import execute, fetch_one
from ..security import hash_password, sign_session, verify_password
from ..templating import render

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    return render(request, "login.html", error=None)


@router.post("/login")
async def login_submit(
    request: Request,
    uname: str = Form(...),
    upass: str = Form(...),
):
    row = fetch_one("SELECT * FROM t_user WHERE uname=%s LIMIT 1", (uname.strip(),))
    if not row or not verify_password(upass, row.get("upass") or ""):
        return render(request, "login.html", error="账号或密码错误")
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(
        settings.SESSION_COOKIE,
        sign_session(row["id"]),
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return resp


@router.get("/register")
async def register_page(request: Request):
    return render(request, "register.html", error=None, form={})


@router.post("/register")
async def register_submit(
    request: Request,
    uname: str = Form(...),
    upass: str = Form(...),
    upass2: str = Form(...),
    iscom: int = Form(0),
    cname: str = Form(""),
):
    uname = uname.strip()
    form = {"uname": uname, "iscom": iscom, "cname": cname}
    if not uname or not upass:
        return render(request, "register.html", error="账号和密码必填", form=form)
    if upass != upass2:
        return render(request, "register.html", error="两次密码不一致", form=form)
    if len(upass) < 6:
        return render(request, "register.html", error="密码至少 6 位", form=form)
    if fetch_one("SELECT id FROM t_user WHERE uname=%s", (uname,)):
        return render(request, "register.html", error="账号已存在", form=form)

    ip = request.client.host if request.client else ""
    cid = 0
    if iscom == 1:
        if not cname.strip():
            return render(request, "register.html", error="企业账号需填写公司名", form=form)
        cid = execute(
            "INSERT INTO t_company (cname) VALUES (%s)",
            (cname.strip(),),
        )

    uid = execute(
        """
        INSERT INTO t_user (cid, uname, upass, rdate, ip, iscom, rid)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (cid, uname, hash_password(upass), dt.date.today(), ip, int(iscom), 0),
    )
    resp = RedirectResponse(url="/dashboard", status_code=303)
    resp.set_cookie(
        settings.SESSION_COOKIE,
        sign_session(uid),
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie(settings.SESSION_COOKIE)
    return resp
