import json
from db import get_connection

def getReportData():
    conn = get_connection()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    avg_price = cur.execute("SELECT AVG(price) FROM books").fetchone()[0]
    top5 = cur.execute(
        "SELECT title, price FROM books ORDER BY price DESC LIMIT 5"
    ).fetchall()
    top5 = [{"title": title, "price": price} for title, price in top5]
    per_rating = cur.execute(
        "SELECT rating, COUNT(*) FROM books GROUP BY rating ORDER BY rating"
    ).fetchall()
    per_rating = {rating: count for rating, count in per_rating}
    conn.close()

    return {
        "total_books": total,
        "average_price": avg_price,
        "top_5_most_expensive": top5,
        "books_per_rating": per_rating,
    }

if __name__ == "__main__":
    report = getReportData()
    print(json.dumps(report, indent=2))
