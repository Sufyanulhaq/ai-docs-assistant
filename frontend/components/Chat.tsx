"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { readEvents } from "@/lib/sse";
import type { ChatMessage, Source } from "@/lib/types";
import { KnowledgePanel, ModeBadge, useBackendInfo } from "./KnowledgePanel";
import { Message } from "./Message";

const SUGGESTIONS = [
  "How long do I have to ask for a refund?",
  "What is the rate limit on the Business plan?",
  "How do I verify a webhook signature?",
  "Which plan includes single sign on?",
];

const MAX_HISTORY = 6;

function newId() {
  return Math.random().toString(36).slice(2, 10);
}

export function Chat() {
  const { health, docs, down } = useBackendInfo();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end" });
  }, [messages]);

  const patch = useCallback((id: string, update: (m: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? update(m) : m)));
  }, []);

  const send = useCallback(
    async (raw: string) => {
      const question = raw.trim();
      if (!question || busy) return;

      const history = messages
        .filter((m) => m.status === "done" && m.content)
        .slice(-MAX_HISTORY)
        .map(({ role, content }) => ({ role, content }));

      const assistantId = newId();
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: "user", content: question, sources: [], status: "done", grounded: true },
        { id: assistantId, role: "assistant", content: "", sources: [], status: "streaming", grounded: true },
      ]);
      setInput("");
      setBusy(true);

      const controller = new AbortController();
      abortRef.current = controller;
      let finished = false;

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, history }),
          signal: controller.signal,
        });

        if (!response.ok || !response.body) {
          let message = "The assistant could not answer right now.";
          if (response.status === 429) {
            const wait = response.headers.get("retry-after");
            message = `Too many questions in a short time. Try again${wait ? ` in ${wait} seconds` : " shortly"}.`;
          } else if (response.status === 422) {
            message = "That question could not be processed. Keep it under 500 characters.";
          } else if (response.status === 502) {
            message = "The assistant backend is not reachable.";
          }
          patch(assistantId, (m) => ({ ...m, status: "error", error: message }));
          return;
        }

        for await (const { event, data } of readEvents(response.body)) {
          if (event === "sources") {
            patch(assistantId, (m) => ({ ...m, sources: data as Source[] }));
          } else if (event === "token") {
            const text = (data as { text: string }).text;
            patch(assistantId, (m) => ({ ...m, content: m.content + text }));
          } else if (event === "done") {
            finished = true;
            patch(assistantId, (m) => ({
              ...m,
              status: "done",
              grounded: Boolean((data as { grounded: boolean }).grounded),
            }));
          } else if (event === "error") {
            finished = true;
            patch(assistantId, (m) => ({
              ...m,
              status: "error",
              error: (data as { message: string }).message,
            }));
          }
        }
        if (!finished) {
          patch(assistantId, (m) => ({ ...m, status: "error", error: "The connection was interrupted." }));
        }
      } catch (error) {
        if ((error as Error).name === "AbortError") {
          patch(assistantId, (m) => ({ ...m, status: "done" }));
        } else {
          patch(assistantId, (m) => ({
            ...m,
            status: "error",
            error: "Could not reach the assistant. Check your connection.",
          }));
        }
      } finally {
        abortRef.current = null;
        setBusy(false);
      }
    },
    [busy, messages, patch],
  );

  return (
    <div className="flex min-h-0 flex-1">
      <section className="flex min-w-0 flex-1 flex-col" aria-label="Chat">
        <header className="flex items-center justify-between gap-3 border-b border-border bg-surface px-5 py-3">
          <div className="min-w-0">
            <h1 className="truncate text-base font-semibold">Docs Assistant</h1>
            <p className="truncate text-xs text-muted">Answers grounded in your documentation, with sources</p>
          </div>
          <ModeBadge health={health} down={down} />
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto" aria-live="polite">
          <div className="mx-auto flex max-w-3xl flex-col gap-6 px-5 py-6">
            {messages.length === 0 ? (
              <div className="mt-10 text-center">
                <h2 className="text-2xl font-semibold tracking-tight">Ask the docs anything</h2>
                <p className="mx-auto mt-2 max-w-md text-muted">
                  Every answer is built only from the documentation and shows exactly where it came
                  from.
                </p>
                <div className="mx-auto mt-6 grid max-w-xl gap-2 sm:grid-cols-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => send(suggestion)}
                      disabled={down}
                      className="rounded-xl border border-border bg-surface px-4 py-3 text-left text-sm transition-colors hover:border-accent hover:bg-accent-soft disabled:opacity-50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => <Message key={message.id} message={message} />)
            )}
            <div ref={endRef} />
          </div>
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            void send(input);
          }}
          className="border-t border-border bg-surface px-5 py-4"
        >
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <label htmlFor="question" className="sr-only">
              Your question
            </label>
            <textarea
              id="question"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault();
                  void send(input);
                }
              }}
              rows={1}
              maxLength={500}
              placeholder="Ask a question about the docs…"
              className="field-sizing-content max-h-40 min-h-11 flex-1 resize-none rounded-xl border border-border bg-bg px-4 py-2.5 outline-none placeholder:text-muted focus:border-accent focus:ring-2 focus:ring-accent/30"
            />
            {busy ? (
              <button
                type="button"
                onClick={() => abortRef.current?.abort()}
                className="h-11 rounded-xl border border-border px-4 text-sm font-medium hover:bg-surface-2"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim() || down}
                className="h-11 rounded-xl bg-accent px-5 text-sm font-semibold text-accent-ink transition-opacity disabled:opacity-40"
              >
                Ask
              </button>
            )}
          </div>
        </form>
      </section>
      <KnowledgePanel health={health} docs={docs} />
    </div>
  );
}
