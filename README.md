# JoulesRAG

## Getting Started

**1. Clone the repository**
```bash
git clone https://github.com/jou/joule-rag
cd joule-rag
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your API key**

Create a `.env` file in the root of the project:
```
joule-rag/
└── .env          <-- create this file
```

Add the following line to it:
```
ANTHROPIC_API_KEY=your-api-key-here
```

You can get your API key at [console.anthropic.com](https://console.anthropic.com/).
Or get a free one from OpenAPI at https://platform.openai.com/api-keys

**5. Run the project**
```bash
python main.py


## Dependencies

| Library | Purpose |
|---|---|
| `anthropic` | Python SDK for accessing Anthropic's AI models via the API |
| `langchain` | Core framework for building LLM-powered applications and chains |
| `langchain-anthropic` | LangChain integration for Anthropic models |
| `langchain-community` | Community-contributed loaders, tools, and integrations for LangChain |
| `langchain-text-splitters` | Utilities for splitting documents into chunks for embedding and retrieval |
| `langgraph` | Library for building stateful, multi-step agent workflows as graphs |
| `chromadb` | Embedded vector database for storing and querying document embeddings |
| `beautifulsoup4` | HTML and XML parsing for web scraping and document ingestion |
| `huggingface_hub` | Client for downloading models and datasets from the Hugging Face Hub |
| `python-dotenv` | Loads environment variables from a `.env` file into the process environment |
| `pydantic` | Data validation and parsing using Python type annotations |
| `pydantic-settings` | Settings management built on Pydantic, supporting `.env` and environment variables |
| `requests` | Synchronous HTTP client for making web requests |
| `aiohttp` | Asynchronous HTTP client/server for non-blocking web requests |
