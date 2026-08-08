import os
import requests

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
        return cached_html
    
    resp = fetch_page(url)
    if resp.status_code == 200:
        save_to_cache(resp.text, filename)
        print(f"Fetched: {os.path.join(CACHE_DIR, filename)}")
        return resp.text
    else:
        print(f"Failed to fetch page. Status code: {resp.status_code}")
        return None

if __name__ == "__main__":
    html = get_page_html(URL, PAGE1_FILENAME)
    if html is not None:
        print(f"HTML length: {len(html)} characters")