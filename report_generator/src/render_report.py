import html
from datetime import date
from report_data import getReportData

def build_html(report):
    today = date.today().isoformat()
    top5_rows = "".join(
        f"<tr><td>{i}</td><td>{html.escape(b['title'])}</td>"
        f"<td class='num'>{b['price']:.2f}</td></tr>"
        for i, b in enumerate(report["top_5_most_expensive"], start=1)
    )
    all_rows = "".join(
        f"<tr><td>{i}</td><td>{html.escape(b['title'])}</td>"
        f"<td class='num'>{rating}</td></tr>"
        for i, b in enumerate(
            _all_books(report), start=1
        )
        for rating in (b["rating"],)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Book Report</title>
<style>
  body {{ font-family: Helvetica, Arial, sans-serif; color: #222; margin: 40px; }}
  h1 {{ font-size: 24px; }}
  h2 {{ font-size: 18px; margin-top: 30px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
  th, td {{ border: 1px solid #999; padding: 6px 8px; text-align: left; }}
  th {{ background: #eee; }}
  thead {{ display: table-header-group; }}
  tr {{ break-inside: avoid; }}
  .num {{ text-align: right; }}
  .total {{ font-size: 14px; }}
</style>
</head>
<body>
  <h1>Book Report</h1>
  <p class="total">Date: {today} &mdash; Total books: {report['total_books']}</p>

  <h2>Top 5 Most Expensive Books</h2>
  <table>
    <thead>
      <tr><th>#</th><th>Title</th><th>Price</th></tr>
    </thead>
    <tbody>
      {top5_rows}
    </tbody>
  </table>

  <h2>All Books</h2>
  <table>
    <thead>
      <tr><th>#</th><th>Title</th><th>Rating</th></tr>
    </thead>
    <tbody>
      {all_rows}
    </tbody>
  </table>
</body>
</html>
"""

def _all_books(report):
    from db import get_connection

    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT title, rating FROM books ORDER BY id"
    ).fetchall()
    conn.close()
    return [{"title": title, "rating": rating} for title, rating in rows]

if __name__ == "__main__":
    print(build_html(getReportData()))
