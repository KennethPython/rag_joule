"""
Indexing phase: embed all chunks and persist them in ChromaDB.

Run after scraper.py and chunker.py:
    python rag.py

Requires sentence-transformers:
    pip install sentence-transformers
"""

import json
import chromadb
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings

CHUNKS_FILE = Path("data/joule_chunks.json")
CHROMA_DIR = "data/chroma"
COLLECTION_NAME = "joule"

# Free multilingual model — good fit for Dutch content on joule.be.
# Downloads once (~400 MB) and is cached locally by HuggingFace.
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_chunks(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_index() -> None:
    # ------------------------------------------------------------------ load
    print(f"Loading chunks from {CHUNKS_FILE}...")
    chunks = load_chunks(CHUNKS_FILE)
    print(f"  {len(chunks)} chunks loaded")

    texts = [c["text"] for c in chunks]

    # Metadata: everything except the text field.
    # ChromaDB only accepts scalar values (str, int, float, bool).
    metadatas = [
        {k: v for k, v in c.items() if k != "text" and isinstance(v, (str, int, float, bool))}
        for c in chunks
    ]
    ids = [str(i) for i in range(len(chunks))]

    # ------------------------------------------------------- embed
    print(f"Loading embedding model: {MODEL_NAME}")
    embedder = HuggingFaceEmbeddings(model_name=MODEL_NAME)

    print("Computing embeddings (this may take a minute on first run)...")
    vectors = embedder.embed_documents(texts)
    print(f"  {len(vectors)} vectors computed (dim={len(vectors[0])})")

    # ------------------------------------------------------- store
    print(f"Persisting to ChromaDB at {CHROMA_DIR!r}...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Drop and recreate so re-runs stay idempotent
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # Add in batches to avoid memory spikes on large datasets
    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids=ids[start:end],
            embeddings=vectors[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Stored batch {start // batch_size + 1} ({min(end, len(chunks))}/{len(chunks)})")

    print(f"\nIndex ready: {collection.count()} vectors in collection '{COLLECTION_NAME}'")


if __name__ == "__main__":
    build_index()
