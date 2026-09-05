import { SessionSummary } from "../../lib/api";

interface Props {
  sessions: SessionSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export default function SessionSelector({ sessions, activeId, onSelect, onNew }: Props) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto p-2 border-b border-gray-200 bg-white">
      <button
        onClick={onNew}
        className="shrink-0 px-3 py-1.5 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
      >
        + New conversation
      </button>
      {sessions.map((s) => (
        <button
          key={s.id}
          onClick={() => onSelect(s.id)}
          className={`shrink-0 px-3 py-1.5 text-sm rounded-md border ${
            activeId === s.id
              ? "bg-indigo-50 border-indigo-400 text-indigo-700"
              : "border-gray-200 text-gray-600 hover:bg-gray-50"
          }`}
        >
          {s.title}
        </button>
      ))}
    </div>
  );
}
