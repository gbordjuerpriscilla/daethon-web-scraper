# Autonomous Web Scraper & Data Extractor

A Python scraper that collects book data from all 50 pages of
[books.toscrape.com](https://books.toscrape.com), a site built for scraping practice,
and exports a clean dataset of 1,000 records.

## What it does

- Sends requests with a browser User-Agent header
- Parses HTML with BeautifulSoup
- Follows the "next" link until the last page, so the page count is not hardcoded
- Retries temporary failures (timeouts, connection drops, 5xx, 429) with exponential
  backoff, and skips permanent errors (404, 403) without retrying
- Cleans and validates the data with pandas
- Exports to CSV and JSON

## Data collected

| Column | Description |
|---|---|
| title | Full book title (read from the link's `title` attribute) |
| price | Price in GBP as a number |
| rating | 1 to 5, converted from the star-rating class |
| link | Full URL of the book's page |
| in_stock | True or False |

## How to run

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python scraper.py
```

Output: `books.csv` and `books.json` in the project folder.

## Error handling and testing

I tested the failure paths by simulating them:

- **Timeouts:** with an artificially tiny timeout, the scraper made 3 attempts with
  waits of 2 s and 4 s, then stopped cleanly.
- **404:** with a nonexistent start URL, it reported a permanent error and did not retry.

The pipeline also asserts that prices are in a sensible range, ratings are 1 to 5,
and at least 100 records were collected.

## Notes

- A 0.5 second pause between pages keeps the load on the server low.
- The dataset is synthetic practice data, so ratings and prices should not be read
  as real-world book statistics.

## Tools

Python 3, requests, BeautifulSoup4, pandas