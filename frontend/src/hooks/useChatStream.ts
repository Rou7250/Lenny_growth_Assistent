import { useCallback, useRef, useState } from "react";
import { ArtifactPayload, ChatMessage, Mode, Provider, SourceCitation, streamChat } from "../lib/api";

interface UseChatStreamArgs {
  sessionId: string | null;
  onArtifact: (artifact: ArtifactPayload) => void;
}

export function useChatStream({ sessionId, onArtifact }: UseChatStreamArgs) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (message: string, mode: Mode, provider: Provider) => {
      if (!sessionId || !message.trim()) return;
      setError(null);

      const userMessage: ChatMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: message,
        sources: [],
        created_at: new Date().toISOString(),
      };
      const assistantId = `local-${Date.now()}-assistant`;
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      await streamChat(
        { session_id: sessionId, message, mode, provider },
        {
          onToken: (text) => {
            setMessages((prev) =>
              prev.map((m) => (m.id === assistantId ? { ...m, content: m.content + text } : m))
            );
          },
          onArtifact: (artifact) => onArtifact(artifact),
          onDone: (sources: SourceCitation[]) => {
            setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, sources } : m)));
            setIsStreaming(false);
          },
          onError: (detail) => {
            setError(detail);
            setIsStreaming(false);
          },
        },
        controller.signal
      );
    },
    [sessionId, onArtifact]
  );

  const loadMessages = useCallback((msgs: ChatMessage[]) => setMessages(msgs), []);

  return { messages, isStreaming, error, send, loadMessages };
}
