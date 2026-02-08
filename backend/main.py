"""
Catalog Insight — Async Market Data API.

Standalone FastAPI service for "Fire & Forget" analysis jobs.
Designed to receive CSV uploads from n8n / Tencent webhooks,
process them through the V2 Engine pipeline, and POST results
back to a callback URL.

Usage:
    uvicorn backend.main:app --port 8000 --reload
    (from 008-Auto-Pilot/)
"""

from __future__ import annotations

import glob
import logging
import os
import sys
import tempfile
import uuid
from datetime import datetime

import httpx
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Path setup — ensure V2_Engine is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from V2_Engine.knowledge_base.converters import snapshot_to_markdown
from V2_Engine.knowledge_base.manager import KnowledgeManager
from V2_Engine.processors.source_0_market_data.analyzer import MarketAnalyzer
from V2_Engine.processors.source_0_market_data.h10_ingestor import H10Ingestor

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("catalog_insight_api")

# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Catalog Insight — Async API",
    description="Fire & Forget market data analysis for the V2 Engine.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job status tracker (lightweight, no DB needed)
_jobs: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------
def process_market_data_job(
    job_id: str,
    tmp_paths: list[str],
    category: str,
    callback_url: str | None,
) -> None:
    """
    Background worker — runs the full V2 Engine pipeline.

    1. Ingest CSVs → cleaned DataFrame
    2. Analyze → Market Snapshot dict
    3. Convert → Markdown (USB Protocol)
    4. Save Markdown + raw CSV to Knowledge Base
    5. POST result to callback URL (if provided)
    """
    _jobs[job_id]["status"] = "processing"
    logger.info("Job %s: started (%d files)", job_id, len(tmp_paths))

    try:
        # Step 1 — Ingest
        ingestor = H10Ingestor()
        df = ingestor.ingest(tmp_paths)
        logger.info("Job %s: ingested %d rows", job_id, len(df))

        # Step 2 — Analyze
        snapshot = MarketAnalyzer().analyze(df)

        # Step 3 — Convert to Markdown
        title = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        md_content = snapshot_to_markdown(title, snapshot)

        # Step 4 — Save to Knowledge Base
        kb = KnowledgeManager()
        filename = kb.make_filename(title)
        kb.save_insight(category, filename, md_content)

        # Also save the raw cleaned CSV
        csv_filename = filename.replace(".md", ".csv")
        csv_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "V2_Engine",
            "knowledge_base",
            "storage",
            category,
        )
        os.makedirs(csv_dir, exist_ok=True)
        df.to_csv(os.path.join(csv_dir, csv_filename), index=False)

        # Build cloud-safe download URL
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        base_url = base_url.rstrip("/")
        download_url = f"{base_url}/storage/{category}/{filename}"

        result = {
            "status": "completed",
            "job_id": job_id,
            "category": category,
            "filename": filename,
            "csv_filename": csv_filename,
            "download_url": download_url,
            "rows_processed": len(df),
            "total_brands": snapshot.get("brands", {}).get("total_brands"),
            "total_sellers": snapshot.get("sellers", {}).get("total_sellers"),
            "completed_at": datetime.now().isoformat(),
        }
        _jobs[job_id] = result
        logger.info("Job %s: completed — saved %s/%s", job_id, category, filename)

        # Step 5 — POST to callback URL
        if callback_url:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(callback_url, json=result)
                    logger.info(
                        "Job %s: callback POST %s → %d",
                        job_id,
                        callback_url,
                        resp.status_code,
                    )
            except Exception as cb_err:
                logger.warning("Job %s: callback failed — %s", job_id, cb_err)

    except Exception as exc:
        _jobs[job_id] = {
            "status": "failed",
            "job_id": job_id,
            "error": str(exc),
            "failed_at": datetime.now().isoformat(),
        }
        logger.error("Job %s: FAILED — %s", job_id, exc, exc_info=True)

    finally:
        # Cleanup temp files
        for p in tmp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/v1/market/analyze_async")
async def analyze_async(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    category: str = Form(default="0_catalog_insight"),
    callback_url: str = Form(default=""),
):
    """
    Fire & Forget — queue a market data analysis job.

    Accepts multiple CSV uploads, saves them to temp files,
    then processes them in the background.
    """
    job_id = str(uuid.uuid4())[:8]

    # Save uploaded files to temp directory
    tmp_paths: list[str] = []
    for f in files:
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".csv", prefix=f"h10_{job_id}_"
        )
        content = await f.read()
        tmp.write(content)
        tmp.close()
        tmp_paths.append(tmp.name)

    _jobs[job_id] = {
        "status": "queued",
        "job_id": job_id,
        "category": category,
        "files": [f.filename for f in files],
        "queued_at": datetime.now().isoformat(),
    }

    cb = callback_url.strip() if callback_url else None
    background_tasks.add_task(process_market_data_job, job_id, tmp_paths, category, cb)

    logger.info("Job %s: queued (%d files → %s)", job_id, len(files), category)

    return {
        "status": "queued",
        "job_id": job_id,
        "files": [f.filename for f in files],
        "category": category,
        "callback_url": cb,
    }


@app.get("/api/v1/market/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of a queued/running job."""
    if job_id not in _jobs:
        return {"status": "not_found", "job_id": job_id}
    return _jobs[job_id]


@app.get("/api/v1/knowledge/latest/catalog_insight")
async def get_latest_catalog_insight():
    """
    Pull Model — returns the most recently created analysis
    from the Catalog Insight folder (both Markdown and CSV data).

    Designed for n8n to consume: "What was the last analysis?"
    """
    catalog_dir = os.path.join(
        _PROJECT_ROOT, "V2_Engine", "knowledge_base", "storage", "Catalog Insight",
    )
    if not os.path.isdir(catalog_dir):
        return JSONResponse(
            status_code=404,
            content={"status": "empty", "message": "No analyses found yet."},
        )

    # Find the most recent .md file by modification time
    md_files = glob.glob(os.path.join(catalog_dir, "*.md"))
    if not md_files:
        return JSONResponse(
            status_code=404,
            content={"status": "empty", "message": "No analyses found yet."},
        )

    latest_md = max(md_files, key=os.path.getmtime)
    md_filename = os.path.basename(latest_md)

    with open(latest_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Look for matching CSV
    csv_filename = md_filename.replace(".md", ".csv")
    csv_path = os.path.join(catalog_dir, csv_filename)
    csv_data = None
    csv_rows = 0
    if os.path.exists(csv_path):
        csv_df = pd.read_csv(csv_path)
        csv_rows = len(csv_df)
        csv_data = csv_df.to_dict(orient="records")

    return {
        "status": "ok",
        "filename": md_filename,
        "csv_filename": csv_filename if csv_data else None,
        "csv_rows": csv_rows,
        "markdown": md_content,
        "csv_data": csv_data,
        "retrieved_at": datetime.now().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "Catalog Insight Async API"}


@app.get("/")
async def root():
    return {
        "service": "Catalog Insight — Async API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "POST /api/v1/market/analyze_async",
            "job_status": "GET /api/v1/market/jobs/{job_id}",
            "latest_analysis": "GET /api/v1/knowledge/latest/catalog_insight",
            "health": "GET /health",
        },
    }


# ---------------------------------------------------------------------------
# Direct run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
