import json
import sqlite3
from pathlib import Path

from db import DB_PATH, init_db

ROOT = Path(__file__).resolve().parent.parent
BOOKS_PATH = ROOT / "books.json"

RATING = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    init_db(conn)
    cur.execute("DELETE FROM books")
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    rows = [
        (
            book["title"],
            book["price_gbp"],
            RATING[book["rating_text"]],
            book["product_url"],
        )
        for book in records
    ]
    cur.executemany(
        "INSERT INTO books (title, price, rating, url) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    inserted = cur.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    conn.close()

    print(f"Seeded {inserted} books into books table.")

if __name__ == "__main__":
    main()
