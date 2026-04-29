"""FastAPI read-only web dashboard."""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils.config import get_config

_DB_PATH = get_config("database.path", "sent_posts.db")
_TEMPLATES = Path(__file__).parent / "templates"
_STATIC = Path(__file__).parent / "static"
_PER_PAGE = 25

app = FastAPI(title="RedBot Dashboard", docs_url="/api/docs", redoc_url=None)
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")
templates = Jinja2Templates(directory=str(_TEMPLATES))


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _conn():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _jobs_query(
    q: str = "",
    remote: bool = False,
    source: str = "",
    min_salary: int = 0,
    days: int = 0,
    offset: int = 0,
    limit: int = _PER_PAGE,
) -> tuple[list[dict], int]:
    filters = ["archived = 0"]
    params: list = []

    if q:
        filters.append("(title LIKE ? OR description LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]
    if remote:
        filters.append("is_remote = 1")
    if source:
        filters.append("source = ?")
        params.append(source)
    if min_salary:
        filters.append("salary_min >= ?")
        params.append(min_salary)
    if days:
        cutoff = int((datetime.utcnow() - timedelta(days=days)).timestamp())
        filters.append("created_utc >= ?")
        params.append(cutoff)

    where = " AND ".join(filters)

    with _conn() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM job_postings WHERE {where}", params
        ).fetchone()[0]

        rows = conn.execute(
            f"SELECT * FROM job_postings WHERE {where} "
            f"ORDER BY priority_score DESC, created_utc DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()

    jobs = []
    for row in rows:
        d = dict(row)
        d["matched_keywords"] = json.loads(d.get("matched_keywords") or "[]")
        d["red_flags"] = json.loads(d.get("red_flags") or "[]")
        d["posted_str"] = _relative(d["created_utc"])
        d["salary_str"] = _salary_str(d)
        jobs.append(d)

    return jobs, total


def _relative(ts: int) -> str:
    diff = datetime.utcnow() - datetime.utcfromtimestamp(ts)
    if diff.days >= 1:
        return f"{diff.days}d ago"
    h = diff.seconds // 3600
    if h >= 1:
        return f"{h}h ago"
    return f"{diff.seconds // 60}m ago"


def _salary_str(d: dict) -> str:
    lo, hi = d.get("salary_min"), d.get("salary_max")
    sym = {"GBP": "£", "EUR": "€"}.get(d.get("salary_currency") or "", "$")
    if lo and hi and lo != hi:
        return f"{sym}{lo:,}–{sym}{hi:,}/yr"
    if lo or hi:
        v = lo or hi
        return f"{sym}{v:,}/yr"
    return ""


def _stats() -> dict:
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM job_postings WHERE archived=0").fetchone()[0]
        today_cutoff = int((datetime.utcnow() - timedelta(hours=24)).timestamp())
        today = conn.execute(
            "SELECT COUNT(*) FROM job_postings WHERE created_utc>=? AND archived=0",
            (today_cutoff,),
        ).fetchone()[0]
        week_cutoff = int((datetime.utcnow() - timedelta(days=7)).timestamp())
        week = conn.execute(
            "SELECT COUNT(*) FROM job_postings WHERE created_utc>=? AND archived=0",
            (week_cutoff,),
        ).fetchone()[0]
        remote = conn.execute(
            "SELECT COUNT(*) FROM job_postings WHERE is_remote=1 AND archived=0"
        ).fetchone()[0]
        avg_salary = conn.execute(
            "SELECT AVG(salary_min) FROM job_postings WHERE salary_min IS NOT NULL AND archived=0"
        ).fetchone()[0]
        sources = conn.execute(
            "SELECT source, COUNT(*) AS n FROM job_postings WHERE archived=0 "
            "GROUP BY source ORDER BY n DESC LIMIT 5"
        ).fetchall()
        top_skills_rows = conn.execute(
            "SELECT matched_keywords FROM job_postings "
            "WHERE matched_keywords IS NOT NULL AND archived=0 LIMIT 500"
        ).fetchall()

    skill_counts: dict[str, int] = {}
    for row in top_skills_rows:
        for kw in json.loads(row[0] or "[]"):
            skill_counts[kw] = skill_counts.get(kw, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:10]

    return {
        "total": total,
        "today": today,
        "week": week,
        "remote": remote,
        "remote_pct": round(remote / total * 100) if total else 0,
        "avg_salary": int(avg_salary) if avg_salary else None,
        "sources": [dict(r) for r in sources],
        "top_skills": top_skills,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse("/jobs")


@app.get("/health")
async def health():
    try:
        with _conn() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=503)


@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(
    request: Request,
    q: str = "",
    remote: bool = False,
    source: str = "",
    min_salary: int = 0,
    days: int = 7,
    page: int = Query(default=1, ge=1),
):
    offset = (page - 1) * _PER_PAGE
    jobs, total = _jobs_query(q=q, remote=remote, source=source,
                               min_salary=min_salary, days=days,
                               offset=offset, limit=_PER_PAGE)
    total_pages = max(1, math.ceil(total / _PER_PAGE))
    return templates.TemplateResponse("jobs.html", {
        "request": request,
        "jobs": jobs,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "q": q,
        "remote": remote,
        "source": source,
        "min_salary": min_salary,
        "days": days,
    })


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def job_detail(request: Request, job_id: int):
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM job_postings WHERE id=?", (job_id,)
        ).fetchone()
    if not row:
        return HTMLResponse("<h1>Job not found</h1>", status_code=404)
    d = dict(row)
    d["matched_keywords"] = json.loads(d.get("matched_keywords") or "[]")
    d["red_flags"] = json.loads(d.get("red_flags") or "[]")
    d["posted_str"] = _relative(d["created_utc"])
    d["salary_str"] = _salary_str(d)
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": d})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "stats": _stats(),
    })


# JSON API endpoints (for programmatic access)
@app.get("/api/jobs")
async def api_jobs(
    q: str = "",
    remote: bool = False,
    source: str = "",
    min_salary: int = 0,
    days: int = 7,
    page: int = Query(default=1, ge=1),
):
    offset = (page - 1) * _PER_PAGE
    jobs, total = _jobs_query(q=q, remote=remote, source=source,
                               min_salary=min_salary, days=days,
                               offset=offset, limit=_PER_PAGE)
    return {"total": total, "page": page, "per_page": _PER_PAGE, "jobs": jobs}


@app.get("/api/stats")
async def api_stats():
    return _stats()
