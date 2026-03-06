import json
import os
from typing import Optional
from app.core.embeddings import embed_query
from app.core.vector_store import query_similar
from app.core.config import settings

_sessions: dict[str, list] = {}


class RAGService:

    async def answer_stream(self, question: str, history: list, doc_filter=None):
        query_embedding = embed_query(question)
        where = {"doc_id": doc_filter} if doc_filter else None

        try:
            results = query_similar(query_embedding, n_results=settings.TOP_K_RESULTS, where=where)
            context_chunks = results["documents"][0] if results["documents"] else []
            sources = results["metadatas"][0] if results["metadatas"] else []
        except Exception:
            context_chunks, sources = [], []

        if not context_chunks:
            yield f"data: {json.dumps({'type': 'error', 'content': 'Nenhum documento indexado.'})}\n\n"
            return

        windowed_history = history[-(settings.MEMORY_WINDOW * 2):]
        context = "\n\n---\n\n".join(context_chunks)
        prompt = self._build_prompt(question, context, windowed_history)

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            yield f"data: {json.dumps({'type': 'error', 'content': 'OPENAI_API_KEY não configurada.'})}\n\n"
            return

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)

        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"

        completion_tokens = 0
        stream = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                completion_tokens += 1
                yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'token_usage': {'prompt_tokens': 0, 'completion_tokens': completion_tokens, 'total_tokens': completion_tokens}})}\n\n"

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
        api_key = settings.OPENAI_API_KEY
        if api_key:
            return await self._openai_generate(prompt, api_key)
        return (
            "⚠️ No LLM configured. Set OPENAI_API_KEY in .env.",
            {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

    async def _openai_generate(self, prompt: str, api_key: str) -> tuple[str, dict]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
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