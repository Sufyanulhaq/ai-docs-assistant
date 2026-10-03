"use client";

import { useEffect, useState } from "react";
import type { DocSummary, Health } from "@/lib/types";

const PROVIDER_LABEL: Record<Health["provider"], string> = {
  anthropic: "Claude",
  openai: "OpenAI",
  offline: "Offline mode",
};

export function useBackendInfo() {
  const [health, setHealth] = useState<Health | null>(null);
  const [docs, setDocs] = useState<DocSummary[]>([]);
  const [down, setDown] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetch("/api/health").then((r) => (r.ok ? r.json() : Promise.reject(r))),
      fetch("/api/sources").then((r) => (r.ok ? r.json() : Promise.reject(r))),
    ])
      .then(([h, d]) => {
        if (cancelled) return;
        setHealth(h);
        setDocs(d);
      })
      .catch(() => !cancelled && setDown(true));
    return () => {
      cancelled = true;
    };
  }, []);

  return { health, docs, down };
}

export function ModeBadge({ health, down }: { health: Health | null; down: boolean }) {
  if (down) {
    return (
      <span className="rounded-full bg-danger-soft px-2.5 py-1 text-xs font-medium text-danger">
        Backend offline
      </span>
    );
  }
  if (!health) return <span className="h-6 w-24 animate-pulse rounded-full bg-surface-2" />;
  const label = PROVIDER_LABEL[health.provider];
  return (
    <span
      title={
        health.provider === "offline"
          ? "No LLM key configured: answers quote the docs directly"
          : `Answers written by ${health.model}`
      }
      className="rounded-full bg-accent-soft px-2.5 py-1 text-xs font-medium text-accent"
    >
      {label}
      {health.model ? ` · ${health.model}` : ""}
    </span>
  );
}

export function KnowledgePanel({ health, docs }: { health: Health | null; docs: DocSummary[] }) {
  return (
    <aside className="hidden w-72 shrink-0 flex-col gap-4 overflow-y-auto border-l border-border bg-surface p-5 lg:flex">
      <div>
        <h2 className="text-sm font-semibold">Knowledge base</h2>
        <p className="mt-1 text-xs leading-relaxed text-muted">
          Sample help docs for <strong>Fernhill Cloud</strong>, a fictional company. Drop your own
          markdown files into the <code className="font-mono">docs/</code> folder to answer from
          your content instead.
        </p>
      </div>
      {health && (
        <p className="text-xs text-muted">
          {health.documents} documents · {health.chunks} passages indexed
        </p>
      )}
      <ul className="space-y-1.5">
        {docs.map((doc) => (
          <li
            key={doc.file}
            className="flex items-center justify-between gap-2 rounded-lg bg-surface-2 px-3 py-2 text-sm"
          >
            <span className="truncate">{doc.title}</span>
            <span className="shrink-0 text-xs text-muted">{doc.chunks}</span>
          </li>
        ))}
      </ul>
      <div className="mt-auto rounded-lg border border-border p-3 text-xs leading-relaxed text-muted">
        <p className="font-medium text-text">How answers are made</p>
        <ol className="mt-1.5 list-decimal space-y-1 pl-4">
          <li>Your question is matched against the docs (BM25 search).</li>
          <li>Questions with no relevant passage never reach the model.</li>
          <li>The model may only use the passages it is given, and cites them.</li>
        </ol>
      </div>
    </aside>
  );
}
