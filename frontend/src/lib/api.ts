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
export async function sendMessageStream(
  question: string,
  history: Message[],
  onToken: (token: string) => void,
  onSources: (sources: any[]) => void,
  onDone: (usage: any) => void,
  docFilter?: string
): Promise<void> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/stream`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history, doc_filter: docFilter }),
    }
  );

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = JSON.parse(line.slice(6));

      if (data.type === "token") onToken(data.content);
      else if (data.type === "sources") onSources(data.content);
      else if (data.type === "done") onDone(data.token_usage);
      else if (data.type === "error") throw new Error(data.content);
    }
  }
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
