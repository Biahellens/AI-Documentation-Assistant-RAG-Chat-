import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function ChatInput({ input, setInput, onSend }: any) {
  return (
    <div className="border-t border-gray-800 p-6 bg-gray-950">
      <div className="flex items-center gap-3 bg-gray-900 border border-gray-800 rounded-2xl px-4 py-3 shadow-lg">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
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
          `${messages.length} messages · memory window: ${Math.min(messages.length, 6)} turns`}
      </p>
    </div>
  )
}