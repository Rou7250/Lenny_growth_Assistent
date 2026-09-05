import { ChatMessage } from "../../lib/api";

export default function MessageItem({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
          isUser ? "bg-indigo-600 text-white" : "bg-white border border-gray-200 text-gray-800"
        }`}
      >
        <p>{message.content || (isUser ? "" : "…")}</p>
        {!isUser && message.sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100 space-y-1">
            {message.sources.map((s, i) => (
              <div key={i} className="text-xs text-gray-500">
                [Episode: {s.guest_name}, {s.timestamp_ref || s.episode_title}] · {(s.similarity * 100).toFixed(0)}% match
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
