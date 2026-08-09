# Target classification

The code in this directory will scrape the website:

```
https://toscrape.com/
```

This specific site was chosen because it is a good starting ground for beginners in website scraping and developers wishing to test their scraping technology. For this implementation, The scraping will target the first three catalogue pages of the website. The collected data will consist of clean and organized JSON records. Although requesting the robots.txt endpoint from the site returns a 404 error, there is explicit permisision provided on the home page of the site for developers to practice scraping. Therefore the implementation does not go against any rules the website has.

## Requirements & Installation

This project requires Python 3.10+ (for `str | None` type syntax) and three packages:

```bash
pip install requests beautifulsoup4 pydantic
```

## Running the scraper

```bash
python src/main.py
```

This will crawl the first 3 catalogue pages, fetch all discovered book detail pages, validate and clean the data, and write results to `output/books.json`, `output/errors.json`, and `output/run-report.json`.

## Record schema

Each validated book is stored as a JSON object with the following shape:

| Field | Type | Description |
|---|---|---|
| `title` | string | Book title as shown on the page |
| `product_url` | string (https URL) | Canonical absolute URL of the book's detail page |
| `price_text` | string | Raw price string as displayed on the site, e.g. `"£51.77"` |
| `price_gbp` | number | Price parsed into a plain number, in GBP |
| `availability_text` | string | Raw availability string, e.g. `"In stock (22 available)"` |
| `rating_text` | string | Star rating as a word, e.g. `"Three"` |
| `description` | string or null | Book description, or `null` if the page has none |
| `source_page` | string (https URL) | Catalogue page URL this book was discovered on |
| `fetched_at` | string | UTC ISO 8601 timestamp of when the detail page was fetched |

The schema is enforced with a Pydantic model before any record is written, so `output/books.json` only ever contains data that matches this shape.

## Politeness rules

This scraper follows several courtesy practices when talking to the target site:

- **Identifying User-Agent** — every request sends a User-Agent naming the project and linking back to its source repository, so the site owner can identify the traffic and reach out if needed.
- **Delay between requests** — a minimum 0.5 second pause after every real network request (not applied to cache hits, since those never touch the site).
- **Timeouts** — every request has a 10 second timeout, so a hung connection can't stall the run indefinitely.
- **Local caching** — every page fetched is saved to `cache/` and reused on subsequent runs, so re-running the scraper (or fixing a bug downstream) doesn't mean re-requesting pages the site has already served once.

## Limitation

The retry logic currently distinguishes failures by HTTP status code and exception type, but it does not implement exponential backoff — a page that fails twice in a row (e.g. during a genuine outage) is marked failed rather than retried further, which is a reasonable tradeoff for a small practice site but wouldn't be robust enough for a production scraper working against a less predictable target.

## Proof of a working run

```json
Run report:
{
  "start_time": "2026-08-09T13:13:48Z",
  "duration_seconds": 1.403,
  "pages_fetched": 0,
  "cache_hits": 66,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failed_page_details": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "http_404"
    }
  ]
}
```

This run was served entirely from cache (`pages_fetched: 0`, `cache_hits: 66` — 3 catalogue pages + 60 book pages + 3 retry attempts on the intentionally broken URL are not counted as fetches since they came from `fetch_page`'s own retry loop, not the cache), correctly recovered all 60 real books, and correctly logged the one deliberately-injected fake URL as a failed page rather than letting it crash the run.

## Why no browser was needed

All of the data this scraper collects — title, price, availability, rating, and description — is already present in the raw HTML the server sends back on the initial request, with nothing rendered or loaded in afterward by JavaScript, so a headless browser would only add startup cost and complexity without unlocking any additional data.

## Ethics note

Where a site offers an official API, that should be preferred over scraping its HTML, since it's the access method the site owner explicitly built and supports. This scraper never attempts to bypass logins, paywalls, CAPTCHAs, or explicit blocks — encountering one of those is treated as a signal to stop, not a problem to work around. Only the fields actually needed for this project's records were collected, rather than pulling and storing full page contents.