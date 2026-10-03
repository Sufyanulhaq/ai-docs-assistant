"use client";

import { useState } from "react";
import type { ChatMessage } from "@/lib/types";
import { RichText } from "./RichText";
import { SourceList } from "./SourceList";

export function Message({ message }: { message: ChatMessage }) {
  const [openSource, setOpenSource] = useState<number | null>(null);

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-4 py-2.5 whitespace-pre-wrap text-accent-ink">
          {message.content}
        </p>
      </div>
    );
  }

  const streaming = message.status === "streaming";
  const waiting = streaming && message.content === "";

  function cite(id: number) {
    setOpenSource(id);
    requestAnimationFrame(() =>
      document
        .getElementById(`source-${message.id}-${id}`)
        ?.scrollIntoView({ block: "nearest", behavior: "smooth" }),
    );
  }

  return (
    <div className="flex gap-3">
      <div
        aria-hidden
        className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-xs font-bold text-accent"
      >
        AI
      </div>
      <div className="min-w-0 max-w-[92%] flex-1">
        {waiting ? (
          <p className="flex items-center gap-2 text-muted" role="status">
            <span className="inline-flex gap-1" aria-hidden>
              <span className="dot" />
              <span className="dot [animation-delay:150ms]" />
              <span className="dot [animation-delay:300ms]" />
            </span>
            Searching the docs
          </p>
        ) : (
          <div className={streaming ? "caret" : ""}>
            <RichText text={message.content} sources={message.sources} onCite={cite} />
          </div>
        )}

        {message.status === "done" && !message.grounded && message.sources.length === 0 && (
          <p className="mt-2 text-xs text-muted">
            Nothing in the documentation matched, so no model call was made.
          </p>
        )}

        {message.status === "error" && (
          <p
            role="alert"
            className="mt-2 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger"
          >
            {message.error ?? "Something went wrong."}
          </p>
        )}

        <SourceList
          messageId={message.id}
          sources={message.sources}
          answer={message.content}
          finished={message.status !== "streaming"}
          openId={openSource}
          onOpen={setOpenSource}
        />
      </div>
    </div>
  );
}
