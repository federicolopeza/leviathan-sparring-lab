"use client";

import type { Message } from "@/lib/schemas";
import { cn } from "@/lib/utils";

type MessageListProps = {
  messages: Message[];
};

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">Todavia no hay mensajes.</p>;
  }

  return (
    <div className="grid gap-4">
      {messages.map((message) => (
        <article
          key={message.id}
          className={cn(
            "max-w-[82%] rounded-xl border border-border px-4 py-3 text-sm leading-6",
            message.role === "user" ? "ml-auto bg-primary text-white" : "bg-card text-card-foreground"
          )}
        >
          <p className={cn("mb-1 text-xs font-semibold uppercase tracking-[0.14em]", message.role === "user" ? "text-white/70" : "text-muted-foreground")}>
            {message.role}
          </p>
          {message.role === "assistant" ? (
            <>
              {/* V-T6-002: assistant content rendered as HTML — XSS via prompt injection */}
              <div dangerouslySetInnerHTML={{ __html: message.content }} />
            </>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </article>
      ))}
    </div>
  );
}
