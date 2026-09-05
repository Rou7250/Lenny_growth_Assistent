import { Mode, Provider } from "../../lib/api";

interface Props {
  provider: Provider;
  mode: Mode;
  onProviderChange: (p: Provider) => void;
  onModeChange: (m: Mode) => void;
}

export default function ModelSelector({ provider, mode, onProviderChange, onModeChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md px-2.5 py-1 flex items-center gap-1.5 shadow-sm">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        Groq Cloud
      </span>
      <select
        value={mode}
        onChange={(e) => onModeChange(e.target.value as Mode)}
        className="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white"
      >
        <option value="default">Chat</option>
        <option value="ship30">Ship 30 for 30</option>
      </select>
    </div>
  );
}
