import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_URL = "https://www.joule.be"

PAGES = [
    "/",
    "/werkgever",
    "/werknemer",
    "/zelfstandige",
    "/overheid",
    "/joule-mobiel",
    "/joule-lokaal",
    "/faq",
    "/jobs/ai-expert",
    "/fietsleasepartner-vergelijken",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def get_soup(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def extract_page_content(soup: BeautifulSoup, url: str) -> dict:
    """Extract title and heading-grouped sections from a page."""
    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    # Group content under the heading it falls beneath.
    # Content before the first heading goes into an implicit intro section.
    sections = []
    current: dict = {"heading": "", "level": 0, "blocks": []}
    seen_blocks: set = set()

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if not text or len(text) <= 20:
            continue

        if tag.name in ("h1", "h2", "h3", "h4"):
            if current["blocks"] or current["heading"]:
                sections.append(current)
            current = {"heading": text, "level": int(tag.name[1]), "blocks": []}
            seen_blocks = set()
        else:
            if text not in seen_blocks:
                seen_blocks.add(text)
                current["blocks"].append(text)

    if current["blocks"] or current["heading"]:
        sections.append(current)

    return {
        "url": url,
        "title": title,
        "sections": sections,
    }


def scrape_blog_articles(max_pages: int = 5) -> list[dict]:
    """Scrape blog article listings and their full content."""
    articles = []

    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            listing_url = f"{BASE_URL}/content-hub/blog"
        else:
            listing_url = f"{BASE_URL}/content-hub/blog?0f59f9c3_page={page_num}"

        print(f"  Scraping blog listing page {page_num}...")
        soup = get_soup(listing_url)
        if not soup:
            break

        # Find all blog card links
        links = soup.select("a.blog_item-link-stretch")
        if not links:
            break

        for link in links:
            href = link.get("href", "")
            if not href:
                continue
            article_url = href if href.startswith("http") else BASE_URL + href

            print(f"    Scraping article: {article_url}")
            article_soup = get_soup(article_url)
            if not article_soup:
                continue

            data = extract_page_content(article_soup, article_url)

            # Try to extract publish date and category if present
            date_tag = article_soup.select_one(".blog_date, .post-date, time")
            category_tag = article_soup.select_one(".blog_category, .category-tag")
            data["date"] = date_tag.get_text(strip=True) if date_tag else ""
            data["category"] = category_tag.get_text(strip=True) if category_tag else ""

            articles.append(data)
            time.sleep(0.5)

        time.sleep(1)

    return articles


def scrape_faq(soup: BeautifulSoup) -> list[dict]:
    """Extract FAQ question/answer pairs."""
    faqs = []
    items = soup.select(".faq_item, .faq_question_wrapper")
    for item in items:
        question_tag = item.select_one(".faq_question, h3, h4")
        answer_tag = item.select_one(".faq_item-content, .faq_answer, p")
        if question_tag and answer_tag:
            faqs.append({
                "question": question_tag.get_text(strip=True),
                "answer": answer_tag.get_text(separator=" ", strip=True),
            })
    return faqs


def save(data: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "joule_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved to {output_file}")


def scrape() -> None:
    output_dir = Path("data")
    result = {
        "pages": [],
        "faq": [],
        "blog_articles": [],
    }

    # Scrape main pages
    for path in PAGES:
        url = BASE_URL + path
        print(f"Scraping {url}...")
        soup = get_soup(url)
        if not soup:
            continue

        page_data = extract_page_content(soup, url)
        result["pages"].append(page_data)

        # Extract FAQ separately from the FAQ page
        if path == "/faq":
            result["faq"] = scrape_faq(soup)
            print(f"  Extracted {len(result['faq'])} FAQ items")

        time.sleep(0.5)

    # Scrape blog articles
    print("\nScraping blog articles...")
    result["blog_articles"] = scrape_blog_articles(max_pages=5)
    print(f"Scraped {len(result['blog_articles'])} blog articles")

    save(result, output_dir)


if __name__ == "__main__":
    scrape()
