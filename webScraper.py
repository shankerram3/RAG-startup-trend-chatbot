import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://techcrunch.com/category/startups/"

def scrape_articles():
    logging.info("Fetching TechCrunch homepage...")
    resp = requests.get(BASE_URL)
    logging.info(f"Status code: {resp.status_code}")
    
    if resp.status_code != 200:
        logging.error("Failed to fetch TechCrunch homepage.")
        return []
    
    soup = BeautifulSoup(resp.text, "lxml")

    posts = soup.select("a.loop-card__title-link")
    logging.info(f"Found {len(posts)} article links on homepage.")

    articles = []
    for i, post in enumerate(posts[:5], start=1):  # just first 5 for debug
        title = post.get_text(strip=True)
        link = post["href"]
        logging.info(f"[{i}] Scraping article: {title} ({link})")

        art_resp = requests.get(link)
        if art_resp.status_code != 200:
            logging.warning(f"Skipping {link}, status {art_resp.status_code}")
            continue
        art_soup = BeautifulSoup(art_resp.text, "lxml")

        author_tag = art_soup.select_one("a.loop-card__author")
        author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        date_tag = art_soup.select_one("time")
        date = date_tag["datetime"] if date_tag else "Unknown"

        paragraphs = [p.get_text(" ", strip=True) for p in art_soup.select("div.article-content p")]
        content = " ".join(paragraphs)

        articles.append({
            "title": title,
            "url": link,
            "author": author,
            "date": date,
            "content": content[:300] + "..."  # preview
        })

    return articles

if __name__ == "__main__":
    data = scrape_articles()
    logging.info(f"Scraped {len(data)} articles.")
    for art in data:
        logging.info(f"---\n{art['title']} | {art['author']} | {art['date']}\n{art['url']}")
