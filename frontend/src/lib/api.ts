export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type Provider = "ollama" | "groq";
export type Mode = "default" | "ship30";

export interface SourceCitation {
  episode_title: string;
  guest_name: string;
  timestamp_ref?: string | null;
  similarity: number;
}

export interface SessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: SourceCitation[];
  created_at: string;
}

export interface SessionDetail extends SessionSummary {
  messages: ChatMessage[];
}

export async function createSession(title = "New conversation"): Promise<SessionSummary> {
  const res = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function listSessions(): Promise<SessionSummary[]> {
  const res = await fetch(`${API_BASE_URL}/api/sessions`);
  if (!res.ok) throw new Error("Failed to list sessions");
  return res.json();
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to load session");
  return res.json();
}

export interface ArtifactPayload {
  id: string;
  artifact_type: "markdown" | "html";
  title: string;
  content: string;
}

export interface StreamHandlers {
  onToken: (text: string) => void;
  onArtifact: (artifact: ArtifactPayload) => void;
  onDone: (sources: SourceCitation[]) => void;
  onError: (detail: string) => void;
}

export async function streamChat(
  params: { session_id: string; message: string; mode: Mode; provider: Provider },
  handlers: StreamHandlers,
  signal?: AbortSignal
) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    signal,
  });

  if (!res.ok || !res.body) {
    handlers.onError("Failed to reach the assistant. Please try again.");
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const raw of events) {
      const lines = raw.split("\n");
      const eventLine = lines.find((l) => l.startsWith("event: "));
      const dataLine = lines.find((l) => l.startsWith("data: "));
      if (!eventLine || !dataLine) continue;

      const eventType = eventLine.replace("event: ", "").trim();
      const data = JSON.parse(dataLine.replace("data: ", ""));

      if (eventType === "token") handlers.onToken(data.text);
      else if (eventType === "artifact") handlers.onArtifact(data);
      else if (eventType === "done") handlers.onDone(data.sources || []);
      else if (eventType === "error") handlers.onError(data.detail);
    }
  }
}
