import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DATA_FILE = Path("data/joule_data.json")
CHUNKS_FILE = Path("data/joule_chunks.json")
CHROMA_DIR = Path("data/chroma")
COLLECTION_NAME = "joule"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K = 5

# Pipeline initialiseren — zelfde logica als main.py
@st.cache_resource
def initialize():
    from main import run_pipeline, get_collection, get_embedder
    import groq

    run_pipeline()
    collection = get_collection()
    embedder = get_embedder()
    client = groq.Groq()
    return collection, embedder, client

# UI
st.title("Joule Fietsleasing Chatbot")
st.caption("Stel een vraag over Joule's producten en diensten")

with st.spinner("Chatbot aan het laden..."):
    collection, embedder, groq_client = initialize()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Wat wil je weten over fietsleasing?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Aan het zoeken..."):
            from main import ask
            answer, sources = ask(prompt, collection, embedder, groq_client)
        st.markdown(answer)
        with st.expander(f"Bronnen ({len(sources)} chunks gebruikt)"):
            for i, chunk in enumerate(sources, 1):
                st.caption(f"**Chunk {i}:**")
                st.markdown(chunk[:300] + "..." if len(chunk) > 300 else chunk)
                st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })