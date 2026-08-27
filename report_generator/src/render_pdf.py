from pathlib import Path
from playwright.sync_api import sync_playwright
from render_report import build_html
from report_data import getReportData

OUT_DIR = Path(__file__).resolve().parent.parent / "reports"

def main():
    OUT_DIR.mkdir(exist_ok=True)
    html = build_html(getReportData())
    pdf_path = OUT_DIR / "test.pdf"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
        )
        browser.close()

    print(f"Wrote {pdf_path}")

if __name__ == "__main__":
    main()
