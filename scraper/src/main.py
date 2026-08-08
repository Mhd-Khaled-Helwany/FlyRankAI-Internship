import os
import time
import requests
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

URL = "https://books.toscrape.com/"
CACHE_DIR = "cache"
PAGE1_FILENAME = "catalogue-page-1.html"

header = {
    "User-Agent": "FlyRankInternshipA9/1.0 https://github.com/Mhd-Khaled-Helwany/FlyRankAI-Internship/tree/main/scraper"   
}

def fetch_page(url:str) -> requests.Response:
    """
    Fetches the content of a webpage.
    """
    response = requests.get(url, headers=header, timeout=10)
    response.raise_for_status()  # Raise an error for bad responses
    return response

def save_to_cache(html: str, filename: str) -> str:
    """
    Saves the HTML content to a cache file.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    filepath = os.path.join(CACHE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(html)
    return filepath

def load_from_cache(filename: str) -> str | None:
    """
    Loads the HTML content from a cache file if it exists."""
    filepath = os.path.join(CACHE_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return None

def get_page_html(url: str, filename: str) -> str | None:
    """
    Fetches the cached HTML content of a webpage.
    """
    cached_html = load_from_cache(filename)
    if cached_html is not None:
        return cached_html, False
    
    resp = fetch_page(url)
    if resp.status_code == 200:
        save_to_cache(resp.text, filename)
        return resp.text, True
    else:
        return None, True

def extract_book_urls(html: str, page_url: str) -> list[str]:
    """
    Extracts book URLs from the HTML content of a webpage.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_links = soup.select("article.product_pod h3 a")
    return [urljoin(page_url, link["href"]) for link in book_links]

def extract_next_page_url(html: str, page_url: str) -> str | None:
    """
    Extracts the URL of the next page from the HTML content of a webpage.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link is None:
        return None
    return urljoin(page_url, next_link["href"])

def crawl_catalogue(start_url: str, max_pages: int) -> list[tuple[str, str]]:
    """
    Crawls the catalogue pages and extracts book URLs.
    """
    book_entries: list[tuple[str, str]] = []
    current_url = start_url
    page_number = 1

    while current_url and page_number <= max_pages:
        filename = f"catalogue-page-{page_number}.html"
        html, was_fetched = get_page_html(current_url, filename)
        if html is None:
            break

        for book_url in extract_book_urls(html, current_url):
            book_entries.append((book_url, current_url))
        if was_fetched:
            time.sleep(0.5)

        current_url = extract_next_page_url(html, current_url)
        page_number += 1

    return book_entries

def remove_duplicates(entries: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Removes duplicate book entries while preserving the order.
    """
    seen: dict[str, str] = {}
    for url, source_page in entries:
        if url not in seen:
            seen[url] = source_page
    return list(seen.items())

def book_filename_from_url(url: str) -> str:
    """
    Generates a filename for a book based on its URL.
    """
    path_parts = [p for p in urlparse(url).path.split("/") if p]
    slug = path_parts[-2] if len(path_parts) >= 2 else path_parts[-1]
    return f"{slug}.html"

def clean_text(text: str) -> str:
    """
    Cleans the text by removing extra whitespace and newlines.
    """
    return " ".join(text.split())

def extract_book_details(html: str, product_url: str, source_page: str) -> dict:
    """
    Extracts book details from the HTML content of a book page.
    """
    soup = BeautifulSoup(html, "html.parser")
    product_main = soup.select_one("div.product_main")

    title = clean_text(product_main.select_one("h1").get_text())
    price_text = clean_text(product_main.select_one("p.price_color").get_text())
    availability_text = clean_text(product_main.select_one("p.availability").get_text())
    rating_tag = product_main.select_one("p.star-rating")
    rating_classes = rating_tag.get("class", [])
    rating_text = next((c for c in rating_classes if c != "star-rating"), None)
    description_tag = soup.select_one("#product_description ~ p")
    description = clean_text(description_tag.get_text()) if description_tag else None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

def fetch_book_details(entries: list[tuple[str, str]]) -> list[dict]:
    """
    Fetches book details for each book entry.
    """
    records = []
    for url, source_page in entries:
        filename = book_filename_from_url(url)
        html, was_fetched = get_page_html(url, filename)
        if html is None:
            continue

        records.append(extract_book_details(html, url, source_page))
        if was_fetched:
            time.sleep(0.5)

    return records

if __name__ == "__main__":
    book_entries = crawl_catalogue(URL, 3)
    unique_entries = remove_duplicates(book_entries)
    records = fetch_book_details(unique_entries)
    if records:
        print(json.dumps(records[0], indent=2))
    print(f"detail_pages={len(records)}")