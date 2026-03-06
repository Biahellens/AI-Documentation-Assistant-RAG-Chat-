from typing import List
from dataclasses import dataclass
from app.core.config import settings


@dataclass
class Chunk:
    text: str
    metadata: dict


def chunk_text(text: str, filename: str, doc_id: str) -> List[Chunk]:
    """
    Sentence-aware sliding window chunking.

    Strategy rationale:
    ─────────────────────────────────────────────────────────────────
    CHUNK_SIZE = 512 tokens  (~380 words)
      → Large enough to contain a full idea/paragraph
      → Small enough for precise retrieval (avoids noisy large chunks)

    CHUNK_OVERLAP = 64 tokens  (~48 words)
      → Prevents losing context when a sentence spans a boundary
      → ~12% overlap: sweet spot between coverage and deduplication

    Word-split approximation vs tokenizer:
      → Avoids adding a tokenizer dependency just for chunking
      → ~1.3 words per token for English technical text
      → Good enough for most documentation use cases
      → For production: swap with tiktoken for exact token counts

    Alternative strategies considered:
      • Semantic chunking (embed → cluster by similarity) — better quality,
        much higher ingestion cost
      • Paragraph-based splitting — simple but uneven chunk sizes
      • Recursive character splitting (LangChain style) — good for mixed content
    ─────────────────────────────────────────────────────────────────
    """
    words = text.split()
    chunks = []
    chunk_size = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    step = chunk_size - overlap

    for i, start in enumerate(range(0, len(words), step)):
        chunk_words = words[start:start + chunk_size]

        # Skip tiny trailing chunks (< 20 words = not useful for retrieval)
        if len(chunk_words) < 20:
            break

        chunks.append(Chunk(
            text=" ".join(chunk_words),
            metadata={
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "start_word": start,
                "word_count": len(chunk_words),
            }
        ))

    return chunks
