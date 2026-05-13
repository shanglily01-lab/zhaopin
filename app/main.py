"""FastAPI 入口。"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .routers import auth, companies, dashboard, home, jobs, resumes
from .templating import render

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

app = FastAPI(title="Web3 招聘平台", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(companies.router)
app.include_router(dashboard.router)


@app.exception_handler(StarletteHTTPException)
async def http_exc(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return render(request, "error.html", status_code=404, status=404, message="页面不存在")
    if exc.status_code == 403:
        return render(request, "error.html", status_code=403, status=403, message=str(exc.detail or "无权访问"))
    return HTMLResponse(
        f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code,
    )
