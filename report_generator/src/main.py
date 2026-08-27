import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

sys.path.insert(0, str(Path(__file__).resolve().parent))

from report_data import getReportData
from render_pdf import render_pdf_to_path, OUT_DIR
from render_report import build_html

app = FastAPI()

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "report.db"

@app.get("/health")
async def get_health():
    """Get the health of the API."""
    return {"status": "ok"}

@app.post("/reports", status_code=201)
async def create_report():
    """Run the whole pipeline: query, render to PDF, store the row."""
    OUT_DIR.mkdir(exist_ok=True)

    report = getReportData()
    html = build_html(report)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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

    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
    }

@app.get("/reports/{report_id}")
async def get_report(report_id: int):
    """Return the report row including the file link."""
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
