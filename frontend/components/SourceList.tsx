import type { Source } from "@/lib/types";

type Props = {
  messageId: string;
  sources: Source[];
  answer: string;
  finished: boolean;
  openId: number | null;
  onOpen: (id: number | null) => void;
};

function SourceCard({
  messageId,
  source,
  cited,
  open,
  onOpen,
}: {
  messageId: string;
  source: Source;
  cited: boolean;
  open: boolean;
  onOpen: (id: number | null) => void;
}) {
  return (
    <details
      id={`source-${messageId}-${source.id}`}
      open={open}
      onToggle={(event) => {
        const nowOpen = (event.currentTarget as HTMLDetailsElement).open;
        if (nowOpen !== open) onOpen(nowOpen ? source.id : null);
      }}
      className={`group rounded-lg border bg-surface text-sm ${
        cited ? "border-accent/50" : "border-border"
      }`}
    >
      <summary className="flex cursor-pointer list-none items-start gap-2.5 px-3 py-2 focus-visible:outline-2 focus-visible:outline-accent">
        <span
          className={`mt-px flex h-5 min-w-5 items-center justify-center rounded px-1 text-xs font-semibold ${
            cited ? "bg-accent text-accent-ink" : "bg-surface-2 text-muted"
          }`}
        >
          {source.id}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-medium">{source.section}</span>
          <span className="block truncate font-mono text-xs text-muted">{source.file}</span>
        </span>
        <span aria-hidden className="text-muted transition-transform group-open:rotate-90">
          ›
        </span>
      </summary>
      <p className="border-t border-border px-3 py-2 whitespace-pre-line text-muted">
        {source.snippet}
        {source.snippet.length >= 300 ? "…" : ""}
      </p>
    </details>
  );
}

export function SourceList({ messageId, sources, answer, finished, openId, onOpen }: Props) {
  if (sources.length === 0) return null;
  const citedIds = new Set([...answer.matchAll(/\[(\d+)\]/g)].map((m) => Number(m[1])));
  const highlight = finished && citedIds.size > 0;
  const primary = highlight ? sources.filter((s) => citedIds.has(s.id)) : sources;
  const others = highlight ? sources.filter((s) => !citedIds.has(s.id)) : [];

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium tracking-wide text-muted uppercase">
        {highlight ? "Sources cited" : "Sources retrieved"}
      </p>
      <div className="space-y-1.5">
        {primary.map((source) => (
          <SourceCard
            key={source.id}
            messageId={messageId}
            source={source}
            cited={highlight}
            open={openId === source.id}
            onOpen={onOpen}
          />
        ))}
      </div>
      {others.length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer text-xs text-muted hover:text-text">
            Also retrieved ({others.length})
          </summary>
          <div className="mt-1.5 space-y-1.5">
            {others.map((source) => (
              <SourceCard
                key={source.id}
                messageId={messageId}
                source={source}
                cited={false}
                open={openId === source.id}
                onOpen={onOpen}
              />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
