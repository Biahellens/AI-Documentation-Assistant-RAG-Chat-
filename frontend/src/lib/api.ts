import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  answer: string;
  sources: Array<{ filename: string; chunk_index: number }>;
  token_usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
  context_used: number;
}

export interface Document {
  doc_id: string;
  filename: string;
}

// ── Chat ──────────────────────────────────────────────────────────
export async function sendMessage(
  question: string,
  history: Message[],
  docFilter?: string
): Promise<ChatResponse> {
  const { data } = await api.post("/api/chat/", { question, history, doc_filter: docFilter });
  return data;
}

// ── Documents ─────────────────────────────────────────────────────
export async function uploadDocument(file: File): Promise<{ doc_id: string; filename: string; chunks_created: number }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/documents/upload", form);
  return data;
}

export async function listDocuments(): Promise<Document[]> {
  const { data } = await api.get("/api/documents/");
  return data.documents;
}

export async function deleteDocument(docId: string): Promise<void> {
  await api.delete(`/api/documents/${docId}`);
}
