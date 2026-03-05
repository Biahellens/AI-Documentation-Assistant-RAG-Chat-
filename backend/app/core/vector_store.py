import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
from functools import lru_cache
from typing import Optional


@lru_cache(maxsize=1)
def get_chroma_client():
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False)
    )


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}  # cosine distance for normalized embeddings
    )


def upsert_chunks(chunks, embeddings: list, ids: list[str]):
    """Insert or update chunks in the vector store."""
    collection = get_collection()
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks]
    )


def query_similar(embedding: list, n_results: int = 5, where: Optional[dict] = None) -> dict:
    """Find top-N most similar chunks to a query embedding."""
    collection = get_collection()
    kwargs = {
        "query_embeddings": [embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def delete_by_doc_id(doc_id: str):
    """Remove all chunks belonging to a document."""
    collection = get_collection()
    collection.delete(where={"doc_id": doc_id})
