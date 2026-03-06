import os
from typing import Optional
from app.core.embeddings import embed_query
from app.core.vector_store import query_similar
from app.core.config import settings

# In-memory session store — swap for Redis in production
_sessions: dict[str, list] = {}


class RAGService:
    async def answer(self, question: str, history: list, doc_filter: Optional[str] = None) -> dict:
        """
        RAG pipeline:
        1. Embed the query
        2. Retrieve top-K similar chunks from vector store
        3. Apply memory window to conversation history
        4. Build prompt with context + history
        5. Generate answer via LLM
        """
        # 1. Embed query
        query_embedding = embed_query(question)

        # 2. Retrieve relevant context
        where = {"doc_id": doc_filter} if doc_filter else None
        try:
            results = query_similar(query_embedding, n_results=settings.TOP_K_RESULTS, where=where)
            context_chunks = results["documents"][0] if results["documents"] else []
            sources = results["metadatas"][0] if results["metadatas"] else []
        except Exception:
            context_chunks = []
            sources = []

        if not context_chunks:
            return {
                "answer": "Nenhum documento indexado ainda. Faça upload de um PDF ou Markdown primeiro.",
                "sources": [],
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "context_used": 0
            }

        # 3. Apply memory window (last N turns)
        windowed_history = history[-(settings.MEMORY_WINDOW * 2):]

        # 4. Build prompt
        context = "\n\n---\n\n".join(context_chunks)
        prompt = self._build_prompt(question, context, windowed_history)

        # 5. Generate
        answer, token_usage = await self._generate(prompt)

        return {
            "answer": answer,
            "sources": sources,
            "token_usage": token_usage,
            "context_used": len(context_chunks)
        }

    def _build_prompt(self, question: str, context: str, history: list) -> str:
        history_str = "\n".join(
            f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in history
        )
        return f"""You are a helpful assistant that answers questions based strictly on the provided documentation context.

## CONTEXT (retrieved documentation chunks):
{context}

## CONVERSATION HISTORY:
{history_str if history_str else "(no previous turns)"}

## USER QUESTION:
{question}

## INSTRUCTIONS:
- Answer based only on the context above
- If the answer is not in the context, say "I couldn't find this in the provided documentation"
- Be concise; cite the source filename when relevant
- Do not hallucinate or add information not present in the context

ANSWER:"""

    async def _generate(self, prompt: str) -> tuple[str, dict]:
        from app.core.config import settings
        api_key = settings.OPENAI_API_KEY
        if api_key:
            return await self._openai_generate(prompt, api_key)
        return (
            "⚠️ No LLM configured. Set OPENAI_API_KEY in .env to enable answers.",
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

    async def _openai_generate(self, prompt: str, api_key: str) -> tuple[str, dict]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,   # low temp = more factual, less creative
        )
        usage = response.usage
        return response.choices[0].message.content, {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }

    async def get_history(self, session_id: str) -> list:
        return _sessions.get(session_id, [])

    async def clear_history(self, session_id: str):
        _sessions.pop(session_id, None)
