import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MarkdownArtifact({ content }: { content: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-a:text-indigo-600 p-4">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
