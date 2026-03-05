import { Avatar, AvatarFallback } from "@/components/ui/avatar"

export function ChatMessage({ role, content }: any) {
  const isUser = role === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <Avatar>
          <AvatarFallback>AI</AvatarFallback>
        </Avatar>
      )}

      <div
        className={`rounded-xl px-4 py-3 max-w-xl text-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        }`}
      >
        {content}
      </div>
    </div>
  )
}