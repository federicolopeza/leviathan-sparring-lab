"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export const webhookEvents = ["org.created", "member.added", "invoice.issued", "invoice.paid", "upload.complete", "webhook.test"] as const;

export type WebhookEvent = (typeof webhookEvents)[number];

type WebhookFormProps = {
  pending?: boolean;
  onSubmit: (payload: { url: string; events: string[] }) => void;
};

export function nextWebhookEvents(current: string[], eventName: string, checked: boolean): string[] {
  if (checked) {
    return current.includes(eventName) ? current : [...current, eventName];
  }
  return current.filter((item) => item !== eventName);
}

export function WebhookForm({ pending, onSubmit }: WebhookFormProps) {
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<string[]>(["invoice.issued"]);

  function submit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit({ url, events });
  }

  return (
    <form className="grid gap-5" onSubmit={submit}>
      <Input label="URL" type="url" value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://ops.example.com/webhook" required />
      <fieldset className="grid gap-3">
        <legend className="text-sm font-medium">Eventos</legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {webhookEvents.map((eventName) => (
            <label key={eventName} className="flex min-h-12 items-center gap-3 rounded-lg border border-border bg-card px-3 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 accent-primary"
                checked={events.includes(eventName)}
                onChange={(event) => setEvents((current) => nextWebhookEvents(current, eventName, event.target.checked))}
              />
              {eventName}
            </label>
          ))}
        </div>
      </fieldset>
      <Button type="submit" disabled={pending || events.length === 0 || !url.trim()}>
        {pending ? "Guardando..." : "Crear webhook"}
      </Button>
    </form>
  );
}
