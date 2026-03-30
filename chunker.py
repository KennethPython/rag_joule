import json
from pathlib import Path

BASE_URL = "https://www.joule.be"
MAX_CHARS = 1500
OVERLAP_CHARS = 150


# ---------------------------------------------------------------------------
# Text splitting
# ---------------------------------------------------------------------------

def _split_text(text: str) -> list[str]:
    """Split text that exceeds MAX_CHARS into overlapping sub-chunks."""
    if len(text) <= MAX_CHARS:
        return [text]
    parts = []
    start = 0
    while start < len(text):
        end = start + MAX_CHARS
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = end - OVERLAP_CHARS
    return parts


# ---------------------------------------------------------------------------
# HTML-aware chunking  (one chunk per heading section)
# ---------------------------------------------------------------------------

def chunk_page(page: dict) -> list[dict]:
    """
    Produce one chunk per section (heading + its body blocks).
    Sections longer than MAX_CHARS are split with overlap.
    """
    chunks = []
    url = page["url"]
    page_title = page.get("title", "")
    extra_meta = {k: page[k] for k in ("date", "category") if k in page and page[k]}

    for section in page.get("sections", []):
        heading = section.get("heading", "")
        level = section.get("level", 0)
        body = " ".join(section.get("blocks", []))

        # Prepend the heading so each chunk is self-contained
        full_text = f"{heading}\n{body}".strip() if heading else body
        if not full_text:
            continue

        for i, text in enumerate(_split_text(full_text)):
            chunk = {
                "chunk_type": "section",
                "url": url,
                "page_title": page_title,
                "section_heading": heading,
                "heading_level": level,
                "text": text,
            }
            if i > 0:
                chunk["split_index"] = i
            chunk.update(extra_meta)
            chunks.append(chunk)

    return chunks


# ---------------------------------------------------------------------------
# FAQ-aware chunking  (each Q&A pair is one atomic chunk)
# ---------------------------------------------------------------------------

def chunk_faq(faq_items: list[dict], faq_url: str, faq_page_title: str = "FAQ") -> list[dict]:
    """
    Each FAQ item becomes a single self-contained chunk.
    The text contains both the question and the answer so the LLM
    never sees one without the other.
    """
    chunks = []
    for item in faq_items:
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        if not question and not answer:
            continue

        # Self-contained: question + answer together in one text block
        text = f"Vraag: {question}\nAntwoord: {answer}"

        chunks.append({
            "chunk_type": "faq",
            "url": faq_url,
            "page_title": faq_page_title,
            "question": question,
            "answer": answer,
            "text": text,
        })
    return chunks


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def chunk_all(data: dict) -> list[dict]:
    chunks: list[dict] = []

    # Collect FAQ page title for use in FAQ chunks
    faq_page_title = "FAQ"
    for page in data.get("pages", []):
        if page["url"] == BASE_URL + "/faq":
            faq_page_title = page.get("title", "FAQ")

    # Main pages (section chunks)
    for page in data.get("pages", []):
        chunks.extend(chunk_page(page))

    # FAQ pairs (self-contained Q&A chunks)
    chunks.extend(chunk_faq(data.get("faq", []), BASE_URL + "/faq", faq_page_title))

    # Blog articles (section chunks with date/category metadata)
    for article in data.get("blog_articles", []):
        chunks.extend(chunk_page(article))

    return chunks


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    data_file = Path("data/joule_data.json")
    output_file = Path("data/joule_chunks.json")

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    chunks = chunk_all(data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"Created {len(chunks)} chunks → {output_file}")

    by_type: dict[str, int] = {}
    for chunk in chunks:
        t = chunk["chunk_type"]
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")


if __name__ == "__main__":
    main()
