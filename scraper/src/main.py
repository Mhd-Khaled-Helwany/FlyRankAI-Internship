import os
import time
import requests
from urllib.parse import urljoin
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
        print(f"Cache hit: {os.path.join(CACHE_DIR, filename)}")
        return cached_html, False
    
    resp = fetch_page(url)
    if resp.status_code == 200:
        save_to_cache(resp.text, filename)
        print(f"Fetched: {os.path.join(CACHE_DIR, filename)}")
        return resp.text, True
    else:
        print(f"Failed to fetch page. Status code: {resp.status_code}")
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

def crawl_catalogue(start_url: str, max_pages: int) -> list[str]:
    """
    Crawls the catalogue pages and extracts book URLs.
    """
    current_url = start_url
    all_book_urls = []
    page_number = 1
    
    while current_url and page_number <= max_pages:
        filename =f"catalogue-page-{page_number}.html"
        html, was_fetched = get_page_html(current_url, filename)
        if html is None:
            print(f"Failed to retrieve page {page_number}. Stopping crawl.")
            break

        all_book_urls.extend(extract_book_urls(html, current_url))
        if was_fetched:
            time.sleep(0.5)
        
        current_url = extract_next_page_url(html, current_url)
        page_number += 1

    return all_book_urls


if __name__ == "__main__":
    book_urls = crawl_catalogue(URL, 3)
    unique_urls = list(dict.fromkeys(book_urls))  # de-dupe, preserve order

    print(
        f"catalogue_pages={min(3, len(book_urls) and 3)} , "
        f"discovered={len(book_urls)} , "
        f"unique_urls={len(unique_urls)}"
    )