import { useMemo } from "react";
import DOMPurify from "dompurify";

/**
 * Renders untrusted generated HTML inside a sandboxed iframe.
 * - Content is sanitized with DOMPurify before ever reaching the iframe.
 * - sandbox="allow-scripts" ONLY — deliberately excludes "allow-same-origin" so the
 *   iframe is placed in an opaque, unique origin and cannot reach the parent app's
 *   cookies, localStorage, DOM, or origin.
 */
export default function SandboxedIframe({ html }: { html: string }) {
  const safeHtml = useMemo(() => {
    const clean = DOMPurify.sanitize(html, {
      WHOLE_DOCUMENT: true,
      ADD_TAGS: ["style"],
    });
    return clean;
  }, [html]);

  return (
    <iframe
      title="Generated artifact preview"
      srcDoc={safeHtml}
      sandbox="allow-scripts"
      className="w-full h-full min-h-[400px] bg-white border-0"
    />
  );
}
