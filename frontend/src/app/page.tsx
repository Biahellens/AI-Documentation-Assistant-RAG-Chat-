"use client";
import { useState, useRef, useEffect } from "react";
import { sendMessage, uploadDocument, listDocuments, deleteDocument } from "../lib/api";
import type { Message, Document } from "../lib/api";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [activeDoc, setActiveDoc] = useState<string | undefined>();
  const [tokenTotal, setTokenTotal] = useState(0);
  const [uploading, setUploading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listDocuments().then(setDocuments).catch(console.error);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    const newMessages: Message[] = [...messages, { role: "user", content: question }];
    setMessages(newMessages);
    setLoading(true);
    try {
      const res = await sendMessage(question, newMessages, activeDoc);
      setMessages([...newMessages, { role: "assistant", content: res.answer }]);
      setTokenTotal((t) => t + res.token_usage.total_tokens);
    } catch (e) {
      setMessages([...newMessages, { role: "assistant", content: "❌ Error reaching backend." }]);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(file);
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      alert("Upload failed");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function handleDelete(docId: string) {
    await deleteDocument(docId);
    setDocuments((d) => d.filter((doc) => doc.doc_id !== docId));
    if (activeDoc === docId) setActiveDoc(undefined);
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-sans">
      {/* Sidebar */}
      <aside className="w-72 h-full bg-gray-900 border-r border-gray-800 flex flex-col p-5">
        <h1 className="text-xl font-bold text-indigo-400 mb-6">
          🤖 RAG AI
        </h1>

        {/* Upload */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg py-2 px-3 text-sm font-medium mb-4"
        >
          {uploading ? "Indexing..." : "+ Upload Document"}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.txt"
          onChange={handleUpload}
          className="hidden"
        />

        {/* Documents */}
        <div className="flex-1 overflow-y-auto">
          <p className="text-xs text-gray-500 uppercase mb-2">Documents</p>

          {documents.length === 0 && (
            <p className="text-xs text-gray-600">
              Upload a PDF or Markdown file.
            </p>
          )}

          <div className="space-y-1">
            {documents.map((doc) => (
              <div
                key={doc.doc_id}
                onClick={() =>
                  setActiveDoc(
                    activeDoc === doc.doc_id ? undefined : doc.doc_id
                  )
                }
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm cursor-pointer transition
                ${activeDoc === doc.doc_id
                    ? "bg-indigo-700 text-white"
                    : "hover:bg-gray-800 text-gray-300"
                  }`}
              >
                <span className="truncate">{doc.filename}</span>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(doc.doc_id);
                  }}
                  className="text-gray-400 hover:text-red-400"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Tokens */}
        <div className="border-t border-gray-800 pt-4 mt-4">
          <p className="text-xs text-gray-500">Tokens used</p>
          <p className="text-sm font-mono text-indigo-300">
            {tokenTotal.toLocaleString()}
          </p>
        </div>
      </aside>

      {/* Chat */}
      <main className="flex-1 flex flex-col">
        {/* Active doc */}
        {activeDoc && (
          <div className="bg-indigo-900/40 text-indigo-300 text-xs px-4 py-2 border-b border-indigo-800">
            🔍 Filtering by:{" "}
            {documents.find((d) => d.doc_id === activeDoc)?.filename}
            <button
              onClick={() => setActiveDoc(undefined)}
              className="ml-2 text-indigo-400 hover:text-white"
            >
              clear
            </button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center mt-32 text-center text-gray-400">
              <div className="text-5xl mb-4">📄</div>
              <h2 className="text-lg font-semibold text-gray-200">
                AI Documentation Assistant
              </h2>
              <p className="text-sm text-gray-500 mt-2">
                Upload a document and ask anything about it.
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${msg.role === "user" ? "justify-end" : ""
                }`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 flex items-center justify-center rounded-full bg-indigo-600 text-white text-sm">
                  AI
                </div>
              )}

              <div
                className={`max-w-2xl px-4 py-3 rounded-2xl text-sm leading-relaxed shadow
                ${msg.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-800 text-gray-100 border border-gray-700"
                  }`}
              >
                {msg.content}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-700 text-white text-xs">
                  You
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm">
                AI
              </div>
              <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-gray-400 animate-pulse">
                Thinking...
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 p-6 bg-gray-950">
          <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-2xl px-4 py-3 shadow-lg">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !e.shiftKey && handleSend()
              }
              placeholder="Ask something about your documents..."
              className="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 focus:outline-none"
            />

            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl px-4 py-2 text-sm font-medium transition"
            >
              Send
            </button>
          </div>

          <p className="text-xs text-gray-600 mt-2 text-center">
            {messages.length > 0 &&
              `${messages.length} messages · memory window: ${Math.min(
                messages.length,
                6
              )} turns`}
          </p>
        </div>
      </main>
    </div>
  );
}
