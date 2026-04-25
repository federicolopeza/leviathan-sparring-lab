"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { ConversationSchema, MessageSchema, type Conversation, type Message } from "@/lib/schemas";

type UseConversationsResult = {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  createConversation: () => Promise<Conversation>;
  sendMessage: (convId: string, content: string) => Promise<Message>;
  refresh: () => Promise<void>;
};

async function fetchConversations(): Promise<Conversation[]> {
  return ConversationSchema.array().parse(await apiFetch<unknown>("/llm/conversations", { headers: authHeaders() }));
}

export function useConversations(): UseConversationsResult {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      setConversations(await fetchConversations());
    } catch (currentError) {
      setError(currentError instanceof Error ? currentError.message : "No se pudieron cargar las conversaciones");
    } finally {
      setLoading(false);
    }
  }, []);

  const createConversation = useCallback(async (): Promise<Conversation> => {
    const conversation = ConversationSchema.parse(
      await apiFetch<unknown>("/llm/conversations", {
        method: "POST",
        headers: authHeaders()
      })
    );
    setConversations((current) => [conversation, ...current]);
    return conversation;
  }, []);

  const sendMessage = useCallback(async (convId: string, content: string): Promise<Message> => {
    return MessageSchema.parse(
      await apiFetch<unknown>(`/llm/conversations/${convId}/messages`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ content })
      })
    );
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { conversations, loading, error, createConversation, sendMessage, refresh };
}
