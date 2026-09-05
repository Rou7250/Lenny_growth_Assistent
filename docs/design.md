# Design

## UI layout
Two-pane layout: chat on the left, artifact viewer on the right (collapsible to a thin rail).
Header bar holds the app title plus provider/mode selectors. A horizontally scrollable session
strip sits below the header for switching between conversations or starting a new one.

## Chat states
- **Empty state**: centered helper text inviting a first question or Ship 30 mode.
- **Streaming**: assistant bubble grows token-by-token; "Assistant is thinking…" hint shown;
  input is disabled until the stream completes.
- **Answered**: assistant bubble shows final content plus a citations block
  (`[Episode: Guest, Timestamp]` · similarity%) when sources exist.
- **Insufficient context**: same bubble styling, fixed copy, no citations block.
- **Error**: red inline banner below the message list with a plain-language error.

## Artifact states
- **Empty**: placeholder text ("Generated Markdown or HTML ... will appear here").
- **Markdown artifact**: rendered via `react-markdown`/`remark-gfm` inside a `prose` container.
- **HTML artifact**: rendered inside the sandboxed iframe (see architecture.md).
- **Collapsed**: viewer shrinks to a narrow vertical rail with a rotated "Artifact" label/button.

## Provider selection
A single `<select>` in the header toggles `Ollama — Local` / `Groq — Cloud`. This value is sent
as `provider` on every `POST /api/chat` call — no page reload or session reset required.

## Responsive behavior
- Session strip scrolls horizontally on narrow viewports instead of wrapping.
- On small screens, the artifact panel can be collapsed to reclaim width for chat; both panels
  use `min-w-0`/flex sizing so content truncates/scrolls instead of overflowing.
- Chat input is a single-line-growing textarea; Enter sends, Shift+Enter inserts a newline.

## Error/loading states
- Network/API failures when listing or loading sessions surface as a dismissable-by-navigation
  red banner under the header, without blocking the rest of the UI.
- Provider failures mid-stream surface inline in the chat pane via the `error` SSE event, and the
  input re-enables immediately so the user can retry.
