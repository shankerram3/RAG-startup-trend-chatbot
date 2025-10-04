import requests
from bs4 import BeautifulSoup
import logging
import re
import spacy
import csv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://techcrunch.com/category/startups/"
nlp = spacy.load("en_core_web_sm")

# --- Utility: Extract structured info ---
def extract_entities(content: str):
    doc = nlp(content)

    people = list({ent.text for ent in doc.ents if ent.label_ == "PERSON"})
    orgs = list({ent.text for ent in doc.ents if ent.label_ == "ORG"})

    # Funding pattern ($20M, $3.5B, etc.)
    funding_pattern = r"\$\d+(?:\.\d+)?\s?(?:M|B|million|billion)?"
    funding = re.findall(funding_pattern, content, flags=re.IGNORECASE)

    # Hiring pattern
    hiring_keywords = re.findall(
        r"\b(hiring|expanding team|recruiting|job openings)\b", 
        content, flags=re.IGNORECASE
    )

    # Sector keywords (expand this list later)
    sector_keywords = ["AI", "fintech", "crypto", "gaming", "healthtech", "biotech", "SaaS"]
    sectors = [kw for kw in sector_keywords if kw.lower() in content.lower()]

    return {
        "people": people,
        "organizations": orgs,
        "funding_mentions": funding,
        "hiring_signals": hiring_keywords,
        "sectors": sectors
    }

# --- Scraper ---
def scrape_articles(pages=3):
    url = BASE_URL
    articles = []

    for page in range(1, pages + 1):
        logging.info(f"Fetching page {page}: {url}")
        resp = requests.get(url)
        if resp.status_code != 200:
            logging.error(f"Failed to fetch page {page}, status {resp.status_code}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        posts = soup.select("a.loop-card__title-link")
        logging.info(f"Found {len(posts)} article links on page {page}")

        for i, post in enumerate(posts, start=1):
            title = post.get_text(strip=True)
            link = post["href"]
            logging.info(f"[Page {page} - {i}] Scraping article: {title} ({link})")

            art_resp = requests.get(link)
            if art_resp.status_code != 200:
                logging.warning(f"Skipping {link}, status {art_resp.status_code}")
                continue
            art_soup = BeautifulSoup(art_resp.text, "lxml")

            author_tag = art_soup.select_one("a.loop-card__author")
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"

            date_tag = art_soup.select_one("time")
            date = date_tag["datetime"] if date_tag else "Unknown"

            paragraphs = [p.get_text(" ", strip=True) for p in art_soup.select("p.wp-block-paragraph")]
            content = " ".join(paragraphs)

            entities = extract_entities(content)

            article_data = {
                "title": title,
                "url": link,
                "author": author,
                "date": date,
                "content": content,
                "signals": entities
            }
            articles.append(article_data)

        # --- next page ---
        next_btn = soup.select_one("a.wp-block-query-pagination-next")
        if not next_btn or "href" not in next_btn.attrs:
            logging.info("No more pages found, stopping early.")
            break
        url = next_btn["href"]

    return articles

# --- Save to CSV ---
def save_to_csv(articles, filename="techcrunch_articles.csv"):
    fieldnames = ["title", "url", "author", "date", "content", 
                  "people", "organizations", "funding_mentions", "hiring_signals", "sectors"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for art in articles:
            writer.writerow({
                "title": art["title"],
                "url": art["url"],
                "author": art["author"],
                "date": art["date"],
                "content": art["content"],  
                "people": ", ".join(art["signals"]["people"]),
                "organizations": ", ".join(art["signals"]["organizations"]),
                "funding_mentions": ", ".join(art["signals"]["funding_mentions"]),
                "hiring_signals": ", ".join(art["signals"]["hiring_signals"]),
                "sectors": ", ".join(art["signals"]["sectors"]),
            })
    print(f"✅ Saved {len(articles)} articles to {filename}")

# --- Main ---
if __name__ == "__main__":
    data = scrape_articles(pages=3)
    logging.info(f"Scraped {len(data)} articles.")
    save_to_csv(data)
    for art in data[:3]:
        print("\n---")
        print(f"📰 {art['title']}")
        print(f"📑 Summary: {art['summary'][:150]}...")
        print(f"🔗 Link: {art['url']}")