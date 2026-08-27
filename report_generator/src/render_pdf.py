import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from report_data import getReportData
from render_report import build_html

OUT_DIR = Path(__file__).resolve().parent.parent / "reports"

async def render_pdf_to_path(html, pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        await page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )
        await browser.close()

def render_pdf_sync(html, pdf_path):
    return asyncio.run(render_pdf_to_path(html, pdf_path))

def main():
    OUT_DIR.mkdir(exist_ok=True)
    html = build_html(getReportData())
    pdf_path = OUT_DIR / "test.pdf"
    render_pdf_sync(html, pdf_path)
    print(f"Wrote {pdf_path}")

if __name__ == "__main__":
    main()
