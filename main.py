"""
Entry point for the Joule RAG chatbot.

Runs the full pipeline if needed, then starts an interactive Q&A loop.
    python main.py
"""

from pathlib import Path

DATA_FILE = Path("data/joule_data.json")
CHUNKS_FILE = Path("data/joule_chunks.json")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "joule"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5


def run_pipeline() -> None:
    if not DATA_FILE.exists():
        print("No scraped data found — running scraper...")
        from scraper import scrape
        scrape()

    if not CHUNKS_FILE.exists():
        print("No chunks found — running chunker...")
        from chunker import main as chunk
        chunk()

    if not CHROMA_DIR.exists() or not any(CHROMA_DIR.iterdir()):
        print("No index found — building index...")
        from rag import build_index
        build_index()


def get_collection():
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_collection(COLLECTION_NAME)


def get_embedder():
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)


def retrieve(query: str, collection, embedder) -> list[str]:
    vector = embedder.embed_query(query)
    results = collection.query(query_embeddings=[vector], n_results=TOP_K)
    return results["documents"][0]


def ask(question: str, collection, embedder, client) -> str:
    chunks = retrieve(question, collection, embedder)
    context = "\n\n---\n\n".join(chunks)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": (
                    "Je bent een behulpzame assistent voor Joule, een Belgisch fietsleasebedrijf. "
                    "Beantwoord vragen uitsluitend op basis van de onderstaande context. "
                    "Als het antwoord niet in de context staat, zeg dat dan eerlijk."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nVraag: {question}",
            },
        ],
    )
    return response.choices[0].message.content


def main() -> None:
    import openai
    from dotenv import load_dotenv

    load_dotenv()

    run_pipeline()

    print("\nLoading index and embedding model...")
    collection = get_collection()
    embedder = get_embedder()
    client = openai.OpenAI()

    print(f"\nJoule chatbot ready ({collection.count()} chunks indexed).")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit"):
            print("Bye!")
            break

        answer = ask(question, collection, embedder, client)
        print(f"\nJoule: {answer}\n")


if __name__ == "__main__":
    main()
