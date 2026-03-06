from sentence_transformers import SentenceTransformer
from app.core.config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Singleton embedding model — loaded once on first call, reused after."""
    print(f"[embeddings] Loading model: {settings.EMBEDDING_MODEL}")
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate normalized embeddings for a batch of texts."""
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        normalize_embeddings=True,   # cosine similarity = dot product
        batch_size=32
    )
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Generate embedding for a single query string."""
    return embed_texts([query])[0]
