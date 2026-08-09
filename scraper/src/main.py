import os
import time
import requests
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, HttpUrl, ValidationError, field_validator

URL = "https://books.toscrape.com/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, "cache")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
BOOKS_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "books.json")
ERRORS_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "errors.json")
RUN_REPORT_PATH = os.path.join(OUTPUT_DIR, "run-report.json")

header = {
    "User-Agent": "FlyRankInternshipA9/1.0 https://github.com/Mhd-Khaled-Helwany/FlyRankAI-Internship/tree/main/scraper"   
}

@dataclass
class RunStats:
    pages_fetched: int = 0       
    cache_hits: int = 0          
    failed_pages: int = 0        
    failed_page_details: list = field(default_factory=list)

class BookRecord(BaseModel):
    title: str = Field(..., description="Book title as shown on the page")
    product_url: HttpUrl = Field(..., description="Canonical absolute URL of the book's detail page")
    price_text: str = Field(..., description="Raw price string as displayed on the site, e.g. '£51.77'")
    price_gbp: float = Field(..., ge=0, description="Price parsed into a plain number, in GBP")
    availability_text: str = Field(..., description="Raw availability string, e.g. 'In stock (22 available)'")
    rating_text: str = Field(..., description="Star rating as a word, e.g. 'Three'")
    description: str | None = Field(default=None, description="Book description, or null if the page has none")
    source_page: HttpUrl = Field(..., description="Catalogue page URL this book was discovered on")
    fetched_at: str = Field(..., description="UTC ISO 8601 timestamp of when the detail page was fetched")

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_https(cls, value):
        if str(value).startswith("http://"):
            raise ValueError("URL must use https://, not http://")
        return value

def fetch_page(url:str) -> tuple[requests.Response | None, str | None]:
    """
    Fetches the content of a webpage.
    """
    last_error = None
    for attempt in range(1, 3):
        try:
            resp = requests.get(url, headers=header, timeout=10)
        except requests.exceptions.Timeout:
            last_error = "timeout"
            if attempt < 2:
                time.sleep(1)
                continue
            return None, last_error
        except requests.exceptions.RequestException as e:
            return None, f"request_error: {e}"

        if resp.status_code == 200:
            return resp, None

        if resp.status_code == 404 or resp.status_code == 403:
            return None, f"http_{resp.status_code}"

        if 500 <= resp.status_code < 600:
            last_error = f"http_{resp.status_code}"
            if attempt < 2:
                time.sleep(1)
                continue
            return None, last_error

        return None, f"http_{resp.status_code}"

    return None, last_error

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

def get_page_html(url: str, filename: str, stats: RunStats) -> tuple[str | None, bool]:
    """
    Fetches the cached HTML content of a webpage.
    """
    cached_html = load_from_cache(filename)
    if cached_html is not None:
        stats.cache_hits += 1
        return cached_html, False
    
    resp, error = fetch_page(url)
    if resp is not None:
        save_to_cache(resp.text, filename)
        print(f"Fetched and cached: {os.path.join(CACHE_DIR, filename)}")
        stats.pages_fetched += 1
        return resp.text, True

    print(f"Failed to fetch page ({error}): {url}")
    stats.failed_pages += 1
    stats.failed_page_details.append({"url": url, "reason": error})
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

def crawl_catalogue(start_url: str, max_pages: int, stats: RunStats) -> list[tuple[str, str]]:
    """
    Crawls the catalogue pages and extracts book URLs.
    """
    book_entries: list[tuple[str, str]] = []
    current_url = start_url
    page_number = 1

    while current_url and page_number <= max_pages:
        filename = f"catalogue-page-{page_number}.html"
        html, was_fetched = get_page_html(current_url, filename, stats)
        try:
            html, was_fetched = get_page_html(current_url, filename, stats)
        except Exception as e:
            print(f"Unexpected error on catalogue page {current_url}: {e}")
            stats.failed_pages += 1
            stats.failed_page_details.append({"url": current_url, "reason": str(e)})
            break
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

def fetch_book_details(entries: list[tuple[str, str]], stats: RunStats) -> list[dict]:
    """
    Fetches book details for each book entry.
    """
    records = []
    for url, source_page in entries:
        filename = book_filename_from_url(url)
        try:
            html, was_fetched = get_page_html(url, filename, stats)
        except Exception as e:
            print(f"Unexpected error on detail page {url}: {e}")
            stats.failed_pages += 1
            stats.failed_page_details.append({"url": url, "reason": str(e)})
            continue

        if html is None:
            continue
        try:
            records.append(extract_book_details(html, url, source_page))
        except Exception as e:
            # Page fetched fine but had unexpected structure — log and skip.
            print(f"Failed to parse detail page {url}: {e}")
            stats.failed_pages += 1
            stats.failed_page_details.append({"url": url, "reason": f"parse_error: {e}"})
            continue
        if was_fetched:
            time.sleep(0.5)

    return records

def parse_price_gbp(price_text: str) -> float:
    """
    Parses the price text and returns the price in GBP as a float.
    """
    match = re.search(r"\d+\.?\d*", price_text)
    if not match:
        raise ValueError(f"Could not parse a numeric price from: {price_text!r}")
    return float(match.group())

def build_records(raw_records: list[dict]) -> tuple[list[BookRecord], list[dict]]:
    valid_by_url: dict[str, BookRecord] = {}
    errors: list[dict] = []
    for raw in raw_records:
        try:
            candidate = dict(raw)
            candidate["price_gbp"] = parse_price_gbp(raw["price_text"])
            record = BookRecord(**candidate)
        except (ValidationError, ValueError, KeyError) as e:
            errors.append({"raw_record": raw, "reason": str(e)})
            continue

        canonical_url = str(record.product_url)
        if canonical_url not in valid_by_url:
            valid_by_url[canonical_url] = record
    ordered_records = sorted(valid_by_url.values(), key=lambda r: str(r.product_url))
    return ordered_records, errors

def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    run_started_at = datetime.now(timezone.utc)
    start_time = time.monotonic()
    stats = RunStats()
    book_entries = crawl_catalogue(URL, 3, stats)
    unique_entries = remove_duplicates(book_entries)

    unique_entries.append((
        "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
        URL,
    ))
    records = fetch_book_details(unique_entries, stats)
    print(f"detail_pages={len(records)}")
    valid_records, errors = build_records(records)
    write_json(BOOKS_OUTPUT_PATH, [r.model_dump(mode="json") for r in valid_records])
    write_json(ERRORS_OUTPUT_PATH, errors)

    duration_seconds = round(time.monotonic() - start_time, 3)
    run_report = {
        "start_time": run_started_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": duration_seconds,
        "pages_fetched": stats.pages_fetched,
        "cache_hits": stats.cache_hits,
        "valid_records": len(valid_records),
        "invalid_records": len(errors),
        "failed_pages": stats.failed_pages,
        "failed_page_details": stats.failed_page_details,
    }
    write_json(RUN_REPORT_PATH, run_report)
    print("\nRun report:")
    print(json.dumps(run_report, indent=2))
    print(
        f"valid_records={len(valid_records)} , errors={len(errors)} , "
        f"failed_pages={stats.failed_pages}"
    )