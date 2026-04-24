import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.config import settings


# Global retriever instance
_vectorstore = None


def get_vectorstore() -> Chroma | None:
    """
    Get or initialize the ChromaDB vector store.
    Returns None if no vector store exists yet.
    """
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    # Check if ChromaDB directory exists with data
    if not os.path.exists(settings.CHROMA_DIR):
        print("[WARN] No ChromaDB directory found. Please ingest documents first.")
        return None

    try:
        embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        _vectorstore = Chroma(
            persist_directory=settings.CHROMA_DIR,
            embedding_function=embeddings,
            collection_name="life_insurance_docs",
        )
        print("[OK] ChromaDB vector store loaded successfully.")
        return _vectorstore

    except Exception as e:
        print(f"[ERROR] Error loading vector store: {e}")
        return None


def reset_vectorstore():
    """Reset the cached vector store (used after re-ingestion)."""
    global _vectorstore
    _vectorstore = None


def retrieve_context(query: str, top_k: int = None) -> list[dict]:
    """
    Retrieve relevant document chunks for a given query.

    Args:
        query: The user's question
        top_k: Number of results to return (defaults to settings.TOP_K_RESULTS)

    Returns:
        List of dicts with keys: content, source, page, score
    """
    if top_k is None:
        top_k = settings.TOP_K_RESULTS

    vectorstore = get_vectorstore()
    if vectorstore is None:
        return []

    try:
        # Use similarity search with scores
        results = vectorstore.similarity_search_with_relevance_scores(
            query, k=top_k
        )

        references = []
        for doc, score in results:
            source = doc.metadata.get("source", "Unknown")
            filename = doc.metadata.get("filename", os.path.basename(source))
            page = doc.metadata.get("page", None)

            references.append({
                "content": doc.page_content,
                "source": filename,
                "source_path": source,
                "page": page,
                "score": round(float(score), 4),
            })

        return references

    except Exception as e:
        print(f"[ERROR] Error retrieving context: {e}")
        return []


def get_document_count() -> int:
    """Get the number of documents stored in the vector database."""
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return 0
    try:
        collection = vectorstore._collection
        return collection.count()
    except Exception:
        return 0
