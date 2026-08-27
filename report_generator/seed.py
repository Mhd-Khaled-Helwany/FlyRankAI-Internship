import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "report.db"
BOOKS_PATH = Path(__file__).parent / "books.json"

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
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            rating INTEGER NOT NULL,
            url TEXT NOT NULL
        )
        """
    )
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
