import sys
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import get_connection
from report_data import getReportData
from render_pdf import render_pdf_to_path, OUT_DIR
from render_report import build_html

app = FastAPI()

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}

class ReportRequest(BaseModel):
    force: bool = False

@app.post("/reports")
async def create_report(req: ReportRequest | None = None):
    """Run the whole pipeline: query, render to PDF, store the row."""
    OUT_DIR.mkdir(exist_ok=True)

    conn = get_connection()
    cur = conn.cursor()

    if not (req and req.force):
        today_start = _today_start_iso()
        existing = cur.execute(
            "SELECT id, path, created_at FROM reports "
            "WHERE created_at >= ? ORDER BY id DESC LIMIT 1",
            (today_start,),
        ).fetchone()
        if existing is not None and existing[1]:
            conn.close()
            return JSONResponse(
                status_code=200,
                content={
                    "id": existing[0],
                    "file": f"/reports/{existing[0]}/file",
                },
            )

    report = getReportData()
    html = build_html(report)

    created_at = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO reports (path, created_at) VALUES (?, ?)",
        ("", created_at),
    )
    report_id = cur.lastrowid
    conn.commit()

    pdf_name = f"{report_id}.pdf"
    pdf_path = OUT_DIR / pdf_name
    await render_pdf_to_path(html, pdf_path)

    cur.execute(
        "UPDATE reports SET path = ? WHERE id = ?",
        (str(pdf_path), report_id),
    )
    conn.commit()
    conn.close()

    return JSONResponse(
        status_code=201,
        content={
            "id": report_id,
            "file": f"/reports/{report_id}/file",
        },
    )

def _today_start_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

@app.get("/reports/{report_id}")
async def get_report(report_id: int):
    """Return the report row including the file link."""
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, path, created_at FROM reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": row[0],
        "path": row[1],
        "created_at": row[2],
        "file": f"/reports/{row[0]}/file",
    }

@app.get("/reports/{report_id}/file")
async def get_report_file(report_id: int):
    """Serve the PDF file from disk."""
    conn = get_connection()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT path FROM reports WHERE id = ?",
        (report_id,),
    ).fetchone()
    conn.close()

    if row is None or not row[0]:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_path = Path(row[0])
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(pdf_path, media_type="application/pdf")
