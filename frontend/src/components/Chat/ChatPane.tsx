import { useEffect, useRef } from "react";
import { ChatMessage } from "../../lib/api";
import MessageItem from "./MessageItem";
import ChatInput from "./ChatInput";

interface Props {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  onSend: (message: string) => void;
}

export default function ChatPane({ messages, isStreaming, error, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center text-gray-400">
            <p className="text-sm">
              Ask a grounded product/growth question from Lenny's Podcast archive,
              <br />
              or switch to Ship 30 mode to generate an article.
            </p>
          </div>
        )}
        {messages.map((m) => (
          <MessageItem key={m.id} message={m} />
        ))}
        {isStreaming && (
          <div className="text-xs text-gray-400 pl-1">Assistant is thinking…</div>
        )}
        {error && (
          <div className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-md p-2 mt-2">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput disabled={isStreaming} onSend={onSend} />
    </div>
  );
}
