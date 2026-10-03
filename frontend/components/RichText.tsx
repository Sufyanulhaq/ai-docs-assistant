import type { ReactNode } from "react";
import type { Source } from "@/lib/types";

type Props = {
  text: string;
  sources: Source[];
  onCite?: (id: number) => void;
};

const INLINE = /(\*\*[^*\n]+\*\*|`[^`\n]+`|(?:\[\d+\])+)/g;
const LIST_ITEM = /^\s*(?:[-•*]|\d+\.)\s+/;

function inline(text: string, sources: Source[], onCite?: (id: number) => void): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={index} className="rounded bg-surface-2 px-1 py-0.5 font-mono text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (/^(?:\[\d+\])+$/.test(part)) {
      const ids = [...part.matchAll(/\[(\d+)\]/g)].map((m) => Number(m[1]));
      return (
        <span key={index} className="whitespace-nowrap">
          {ids.map((id) =>
            sources.some((s) => s.id === id) ? (
              <button
                key={id}
                type="button"
                onClick={() => onCite?.(id)}
                aria-label={`Show source ${id}`}
                className="mx-px inline-flex h-[1.25em] min-w-[1.25em] -translate-y-0.5 items-center justify-center rounded bg-accent-soft px-1 text-[0.72em] font-semibold text-accent hover:bg-accent hover:text-accent-ink focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent"
              >
                {id}
              </button>
            ) : (
              <span key={id}>[{id}]</span>
            ),
          )}
        </span>
      );
    }
    return part;
  });
}

export function RichText({ text, sources, onCite }: Props) {
  const blocks = text.trim().split(/\n{2,}/).filter(Boolean);
  return (
    <div className="space-y-3 leading-relaxed">
      {blocks.map((block, index) => {
        const lines = block.split("\n");
        if (lines.every((line) => LIST_ITEM.test(line))) {
          return (
            <ul key={index} className="list-disc space-y-1 pl-5 marker:text-muted">
              {lines.map((line, i) => (
                <li key={i}>{inline(line.replace(LIST_ITEM, ""), sources, onCite)}</li>
              ))}
            </ul>
          );
        }
        return (
          <p key={index}>
            {lines.map((line, i) => (
              <span key={i}>
                {i > 0 && <br />}
                {inline(line, sources, onCite)}
              </span>
            ))}
          </p>
        );
      })}
    </div>
  );
}
