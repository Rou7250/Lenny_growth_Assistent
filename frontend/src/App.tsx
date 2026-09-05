import { useEffect, useState } from "react";
import ChatPane from "./components/Chat/ChatPane";
import SessionSelector from "./components/Chat/SessionSelector";
import ModelSelector from "./components/Chat/ModelSelector";
import ArtifactViewer from "./components/Artifact/ArtifactViewer";
import { useChatStream } from "./hooks/useChatStream";
import {
  ArtifactPayload,
  createSession,
  getSession,
  listSessions,
  Mode,
  Provider,
  SessionSummary,
} from "./lib/api";

export default function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>("groq");
  const [mode, setMode] = useState<Mode>("default");
  const [artifact, setArtifact] = useState<ArtifactPayload | null>(null);
  const [artifactCollapsed, setArtifactCollapsed] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const { messages, isStreaming, error, send, loadMessages } = useChatStream({
    sessionId: activeSessionId,
    onArtifact: (a) => {
      setArtifact(a);
      setArtifactCollapsed(false);
    },
  });

  const refreshSessions = async () => {
    try {
      const list = await listSessions();
      setSessions(list);
      return list;
    } catch {
      setLoadError("Could not reach the backend API. Is it running?");
      return [];
    }
  };

  const startNewSession = async () => {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      loadMessages([]);
      setArtifact(null);
      setLoadError(null);
    } catch {
      setLoadError("Could not create a new conversation.");
    }
  };

  const selectSession = async (id: string) => {
    setActiveSessionId(id);
    try {
      const detail = await getSession(id);
      loadMessages(detail.messages);
    } catch {
      setLoadError("Could not load that conversation.");
    }
  };

  useEffect(() => {
    (async () => {
      const list = await refreshSessions();
      if (list.length > 0) {
        await selectSession(list[0].id);
      } else {
        await startNewSession();
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="h-screen flex flex-col">
      <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <h1 className="text-lg font-semibold text-gray-900">Lenny Growth Assistant</h1>
        <ModelSelector provider={provider} mode={mode} onProviderChange={setProvider} onModeChange={setMode} />
      </header>

      <SessionSelector
        sessions={sessions}
        activeId={activeSessionId}
        onSelect={selectSession}
        onNew={startNewSession}
      />

      {loadError && (
        <div className="text-xs text-red-600 bg-red-50 border-b border-red-200 px-4 py-2">{loadError}</div>
      )}

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 min-w-0">
          <ChatPane
            messages={messages}
            isStreaming={isStreaming}
            error={error}
            onSend={(message) => send(message, mode, provider)}
          />
        </div>
        <div className={artifactCollapsed ? "w-10" : "w-full max-w-md"}>
          <ArtifactViewer
            artifact={artifact}
            collapsed={artifactCollapsed}
            onToggleCollapse={() => setArtifactCollapsed((c) => !c)}
          />
        </div>
      </div>
    </div>
  );
}
