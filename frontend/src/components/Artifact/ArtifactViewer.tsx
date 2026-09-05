import { useState } from "react";
import { ArtifactPayload } from "../../lib/api";
import MarkdownArtifact from "./MarkdownArtifact";
import SandboxedIframe from "./SandboxedIframe";

interface Props {
  artifact: ArtifactPayload | null;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function ArtifactViewer({ artifact, collapsed, onToggleCollapse }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!artifact) return;
    await navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (collapsed) {
    return (
      <div className="border-l border-gray-200 bg-gray-50 w-10 flex items-start justify-center pt-3">
        <button
          onClick={onToggleCollapse}
          className="text-gray-400 hover:text-gray-700 text-sm rotate-180 [writing-mode:vertical-rl]"
        >
          Artifact
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border-l border-gray-200 bg-gray-50">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 bg-white">
        <span className="text-sm font-medium text-gray-700 truncate">
          {artifact ? artifact.title : "Artifact"}
        </span>
        <div className="flex items-center gap-2">
          {artifact && (
            <button onClick={handleCopy} className="text-xs text-gray-500 hover:text-gray-800">
              {copied ? "Copied!" : "Copy"}
            </button>
          )}
          <button onClick={onToggleCollapse} className="text-xs text-gray-500 hover:text-gray-800">
            Collapse
          </button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {!artifact && (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm p-4 text-center">
            Generated Markdown or HTML — like a Ship 30 for 30 article — will appear here.
          </div>
        )}
        {artifact?.artifact_type === "markdown" && <MarkdownArtifact content={artifact.content} />}
        {artifact?.artifact_type === "html" && <SandboxedIframe html={artifact.content} />}
      </div>
    </div>
  );
}
