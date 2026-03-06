import uuid
import io
from typing import Optional
import pypdf
from app.core.chunker import chunk_text
from app.core.embeddings import embed_texts
from app.core.vector_store import upsert_chunks, delete_by_doc_id, get_collection


class IngestionService:
    async def ingest(self, filename: str, content: bytes, content_type: str) -> dict:
        """Full ingestion pipeline: parse → chunk → embed → store."""
        doc_id = str(uuid.uuid4())

        # 1. Extract raw text
        if content_type == "application/pdf":
            text = self._extract_pdf(content)
        else:
            text = content.decode("utf-8")

        # 2. Chunk with sliding window
        chunks = chunk_text(text, filename=filename, doc_id=doc_id)
        if not chunks:
            return {"doc_id": doc_id, "filename": filename, "chunks_created": 0, "status": "empty"}

        # 3. Batch embed
        texts = [c.text for c in chunks]
        embeddings = embed_texts(texts)

        # 4. Upsert into Chroma
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        upsert_chunks(chunks, embeddings, ids)

        return {
            "doc_id": doc_id,
            "filename": filename,
            "chunks_created": len(chunks),
            "status": "indexed"
        }

    def _extract_pdf(self, content: bytes) -> str:
        reader = pypdf.PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    async def list_documents(self) -> list:
        """Return unique documents stored in the vector index."""
        collection = get_collection()
        results = collection.get(include=["metadatas"])
        seen = {}
        for meta in results["metadatas"]:
            doc_id = meta["doc_id"]
            if doc_id not in seen:
                seen[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta["filename"]
                }
        return list(seen.values())

    async def delete_document(self, doc_id: str):
        delete_by_doc_id(doc_id)
