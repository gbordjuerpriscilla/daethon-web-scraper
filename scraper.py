import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "https://books.toscrape.com/"
MAX_RETRIES = 3

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def fetch(url):
    """Download a page, retrying temporary failures. Return response or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as error:
            status = error.response.status_code
            if status < 500 and status != 429:
                print(f"  Permanent error {status} for {url}. Not retrying.")
                return None
            print(f"  Server error {status} (attempt {attempt}/{MAX_RETRIES})")

        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as error:
            print(f"  {type(error).__name__} (attempt {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            print(f"  Waiting {wait}s before retrying...")
            time.sleep(wait)

    print(f"  Giving up on {url}")
    return None


def scrape_page(url):
    """Fetch one page. Return (list of records, url of next page or None)."""
    response = fetch(url)
    if response is None:
        return None, None
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    records = []
    for book in soup.find_all("article", class_="product_pod"):
        rating_word = book.find("p", class_="star-rating")["class"][1]
        price_text = book.find("p", class_="price_color").text
        records.append({
            "title": book.h3.a["title"],
            "price": float(price_text.replace("£", "")),
            "rating": RATING_MAP[rating_word],
            "availability": book.find("p", class_="availability").text.strip(),
            "link": urljoin(url, book.h3.a["href"]),
        })

    next_li = soup.find("li", class_="next")
    next_url = urljoin(url, next_li.a["href"]) if next_li else None
    return records, next_url


all_books = []
url = START_URL
page_number = 1

while url:
    records, url = scrape_page(url)
    if records is None:
        print("Stopping early: a page could not be fetched.")
        break
    all_books.extend(records)
    print(f"Page {page_number}: {len(records)} books (total {len(all_books)})")
    page_number += 1
    time.sleep(0.5)

print("Done. Total records:", len(all_books))

import pandas as pd

df = pd.DataFrame(all_books)
print("\nRaw rows:", len(df))

# 1. Remove duplicates (the same book link should appear only once)
df = df.drop_duplicates(subset="link")

# 2. Remove rows with missing essentials
df = df.dropna(subset=["title", "price", "link"])

# 3. Turn the availability text into a clean True/False column
df["in_stock"] = df["availability"].str.contains("In stock")
df = df.drop(columns=["availability"])

# 4. Sanity checks: fail loudly if the data looks wrong
assert df["price"].between(0, 1000).all(), "Price outside expected range"
assert df["rating"].between(1, 5).all(), "Rating outside 1-5"
assert len(df) >= 100, "Fewer than 100 records, deliverable not met"

print("Clean rows:", len(df))
print(df.head())
print("\nAverage price:", round(df["price"].mean(), 2))
print("Books per rating:\n", df["rating"].value_counts().sort_index())

# 5. Export
df.to_csv("books.csv", index=False, encoding="utf-8-sig")
df.to_json("books.json", orient="records", indent=2, force_ascii=False)
print("\nSaved books.csv and books.json")