"use client";

import { Send } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { MessageList } from "@/components/features/chat/message-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { useConversations } from "@/lib/hooks/useConversations";
import { MessageSchema, type Message } from "@/lib/schemas";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const { conversations, loading, error, createConversation, sendMessage } = useConversations();
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const fetchMessages = useCallback(async (conversationId: string): Promise<void> => {
    setMessagesLoading(true);
    setChatError(null);
    try {
      setMessages(
        MessageSchema.array().parse(
          await apiFetch<unknown>(`/llm/conversations/${conversationId}/messages`, {
            headers: authHeaders()
          })
        )
      );
    } catch (currentError) {
      setChatError(currentError instanceof Error ? currentError.message : "No se pudieron cargar los mensajes");
    } finally {
      setMessagesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedConversationId && conversations.length > 0) {
      setSelectedConversationId(conversations[0].id);
    }
  }, [conversations, selectedConversationId]);

  useEffect(() => {
    if (selectedConversationId) {
      void fetchMessages(selectedConversationId);
    }
  }, [fetchMessages, selectedConversationId]);

  async function startConversation(): Promise<void> {
    setChatError(null);
    try {
      const conversation = await createConversation();
      setSelectedConversationId(conversation.id);
      setMessages([]);
    } catch (currentError) {
      setChatError(currentError instanceof Error ? currentError.message : "No se pudo crear la conversacion");
    }
  }

  async function submitMessage(): Promise<void> {
    if (!selectedConversationId || !messageInput.trim()) {
      return;
    }

    const content = messageInput.trim();
    setSending(true);
    setChatError(null);
    setMessageInput("");
    try {
      const message = await sendMessage(selectedConversationId, content);
      setMessages((current) => [...current, message]);
      await fetchMessages(selectedConversationId);
    } catch (currentError) {
      setMessageInput(content);
      setChatError(currentError instanceof Error ? currentError.message : "No se pudo enviar el mensaje");
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Chat</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">LLM conversations</h1>
      </div>

      <div className="grid min-h-[680px] gap-6 lg:grid-cols-[320px_1fr]">
        <Card className="h-full">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-xl font-semibold">Conversations</h2>
              <Button type="button" size="sm" onClick={() => void startConversation()}>
                New conversation
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <div className="grid gap-2">
                {conversations.map((conversation) => (
                  <button
                    key={conversation.id}
                    type="button"
                    className={cn(
                      "rounded-lg border px-3 py-3 text-left text-sm transition",
                      selectedConversationId === conversation.id
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-card text-card-foreground hover:bg-muted"
                    )}
                    onClick={() => setSelectedConversationId(conversation.id)}
                  >
                    <span className="block font-semibold">{conversation.title}</span>
                    <span className="mt-1 block text-xs text-muted-foreground">{conversation.model}</span>
                  </button>
                ))}
                {conversations.length === 0 ? <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">No conversations yet.</p> : null}
              </div>
            )}
            {error ? <p className="mt-4 text-sm text-destructive">{error}</p> : null}
          </CardContent>
        </Card>

        <Card className="flex min-h-[680px] flex-col">
          <CardHeader>
            <h2 className="text-xl font-semibold">{conversations.find((conversation) => conversation.id === selectedConversationId)?.title ?? "Select a conversation"}</h2>
          </CardHeader>
          <CardContent className="flex min-h-0 flex-1 flex-col gap-4">
            <div className="min-h-0 flex-1 overflow-y-auto rounded-lg border border-border bg-muted/40 p-4">
              {messagesLoading ? <Skeleton className="h-72 w-full" /> : <MessageList messages={messages} />}
            </div>
            {chatError ? <p className="text-sm text-destructive">{chatError}</p> : null}
            <form
              className="flex gap-3"
              onSubmit={(event) => {
                event.preventDefault();
                void submitMessage();
              }}
            >
              <Input
                aria-label="Message"
                value={messageInput}
                onChange={(event) => setMessageInput(event.target.value)}
                placeholder="Send a message"
                disabled={!selectedConversationId || sending}
              />
              <Button type="submit" disabled={!selectedConversationId || sending || !messageInput.trim()}>
                <Send className="h-4 w-4" />
                Send
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
