# JoulesRAG

A Retrieval-Augmented Generation (RAG) pipeline built on top of [joule.be](https://www.joule.be). It scrapes the Joule website, chunks the content intelligently, embeds it with a free multilingual model, and stores the vectors locally — ready to power a grounded Q&A chatbot.

---

## Pipeline overview

```
scraper.py  →  chunker.py  →  rag.py  →  (query / chat)
  scrape        chunk          embed
  & save        & structure    & index
```

---

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/KennethPython/rag_joule.git
cd rag_joule
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install sentence-transformers   # for embeddings (free, runs locally)
```

### 4. Add your API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-api-key-here
```

Get a key at [console.anthropic.com](https://console.anthropic.com/) or a free OpenAI key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

### 5. Run the pipeline

```bash
python scraper.py   # scrape joule.be → data/joule_data.json
python chunker.py   # chunk the data  → data/joule_chunks.json
python rag.py       # embed & index   → data/chroma/
python main.py      # start the chat
```

---

## Scraping

`scraper.py` fetches the following pages from joule.be and saves everything to `data/joule_data.json`:

| Page | Notes |
|---|---|
| `/` | Homepage |
| `/werkgever` | For employers |
| `/werknemer` | For employees |
| `/zelfstandige` | For the self-employed |
| `/overheid` | For government |
| `/joule-mobiel` | Joule Mobile |
| `/joule-lokaal` | Joule Local |
| `/faq` | Frequently asked questions |
| `/jobs` | Job listings — not covered by the current Joule chatbot |
| `/fietsleasepartner-vergelijken` | Partner comparison — not covered by the current Joule chatbot |
| `/content-hub/blog` | Blog articles (up to 5 listing pages) |

The output has three sections:

<details>
<summary><strong>Main pages</strong></summary>

| Field | Description |
|---|---|
| `url` | Page URL |
| `title` | Page `<title>` tag |
| `sections` | Heading-grouped content: each entry has `heading`, `level`, and `blocks` (body paragraphs) |

</details>

<details>
<summary><strong>FAQ</strong></summary>

| Field | Description |
|---|---|
| `question` | Question text |
| `answer` | Answer text |

</details>

<details>
<summary><strong>Blog articles</strong></summary>

| Field | Description |
|---|---|
| `url` | Article URL |
| `title` | Page `<title>` tag |
| `sections` | Same heading-grouped structure as main pages |
| `date` | Publish date |
| `category` | Category tag |

</details>

---

## Chunking

`chunker.py` reads `data/joule_data.json` and writes `data/joule_chunks.json`.

Two strategies are used — one for structured page content, one for FAQ pairs.

### Strategy 1 — HTML-aware chunking

Applied to all main pages and blog articles.

Content is grouped by heading: each heading and the paragraphs beneath it become one chunk. This keeps document structure intact so the retriever always knows which section an answer came from. The heading is prepended to every chunk so it is self-contained even after splitting.

Sections longer than **1500 characters** are split with a **150-character overlap** to avoid cutting off mid-sentence while preserving context across boundaries.

| Metadata field | Description |
|---|---|
| `chunk_type` | `"section"` |
| `url` | Source page URL |
| `page_title` | Page `<title>` |
| `section_heading` | Heading this content falls under |
| `heading_level` | Heading depth (1–4) |
| `text` | Heading + body text |
| `date` / `category` | Blog articles only |

### Strategy 2 — FAQ-aware chunking

Applied to all Q&A pairs from `/faq`.

Each question and its answer are kept together as a **single atomic chunk — never split**. This ensures the retriever always returns a complete answer with the question that contextualises it.

| Metadata field | Description |
|---|---|
| `chunk_type` | `"faq"` |
| `url` | Source page URL (`/faq`) |
| `page_title` | Page `<title>` |
| `question` | Question text |
| `answer` | Answer text |
| `text` | `Vraag: <question>\nAntwoord: <answer>` |

---

## Embeddings & indexing

`rag.py` reads `data/joule_chunks.json`, embeds every chunk, and persists the vectors to ChromaDB at `data/chroma/`.

**Embedding model:** [`paraphrase-multilingual-MiniLM-L12-v2`](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)

HuggingFace is used for demo purposes — the model is completely free and runs locally with no API key required. It supports 50+ languages, making it a good fit for the Dutch content on joule.be. The model (~400 MB) is downloaded once on first run and cached by HuggingFace.

**Vector store:** ChromaDB (embedded, no server needed). The collection is named `joule` and persisted to disk so the index survives restarts. Re-running `rag.py` drops and recreates the collection to stay comparably the same.

---

## Dependencies

| Library | Purpose |
|---|---|
| `anthropic` | Python SDK for Claude (Anthropic API) |
| `langchain` | Framework for building LLM-powered applications |
| `langchain-anthropic` | LangChain integration for Anthropic models |
| `langchain-community` | Community integrations: embeddings, vector stores, tools |
| `langchain-text-splitters` | Utilities for splitting documents into chunks |
| `langgraph` | Stateful multi-step agent workflows |
| `chromadb` | Embedded vector database for storing and querying embeddings |
| `beautifulsoup4` | HTML parsing for web scraping |
| `sentence-transformers` | Free local embedding models from HuggingFace |
| `huggingface_hub` | Downloading and caching HuggingFace models |
| `python-dotenv` | Loads environment variables from `.env` |
| `pydantic` | Data validation using Python type annotations |
| `pydantic-settings` | Settings management with `.env` support |
| `requests` | HTTP client for web scraping |
| `aiohttp` | Async HTTP client |
