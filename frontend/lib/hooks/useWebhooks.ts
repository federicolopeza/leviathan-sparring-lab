"use client";

import { useMutation, useQuery, useQueryClient, type UseMutationResult, type UseQueryResult } from "@tanstack/react-query";
import { z } from "zod";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { WebhookDeliverySchema, WebhookSchema, type Webhook, type WebhookDelivery } from "@/lib/schemas";

export type WebhookInput = {
  url: string;
  events: string[];
};

export type WebhookTestResult = {
  ok: boolean;
  status?: number;
  message?: string;
};

const WebhookTestResultSchema = z.object({
  ok: z.boolean(),
  status: z.number().int().optional(),
  message: z.string().optional()
});

export function useWebhooks(): {
  webhooks: UseQueryResult<Webhook[]>;
  createWebhook: UseMutationResult<Webhook, Error, WebhookInput>;
  updateWebhook: UseMutationResult<Webhook, Error, WebhookInput & { id: string }>;
  deleteWebhook: UseMutationResult<void, Error, string>;
  testWebhook: UseMutationResult<WebhookTestResult, Error, string>;
} {
  const queryClient = useQueryClient();
  const invalidateWebhooks = () => {
    void queryClient.invalidateQueries({ queryKey: ["webhooks"] });
  };

  const webhooks = useQuery({
    queryKey: ["webhooks"],
    queryFn: async () => WebhookSchema.array().parse(await apiFetch<unknown>("/webhooks", { headers: authHeaders() }))
  });

  const createWebhook = useMutation({
    mutationFn: async (payload: WebhookInput) =>
      WebhookSchema.parse(
        await apiFetch<unknown>("/webhooks", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: invalidateWebhooks
  });

  const updateWebhook = useMutation({
    mutationFn: async ({ id, ...payload }: WebhookInput & { id: string }) =>
      WebhookSchema.parse(
        await apiFetch<unknown>(`/webhooks/${id}`, {
          method: "PATCH",
          headers: authHeaders(),
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: invalidateWebhooks
  });

  const deleteWebhook = useMutation({
    mutationFn: async (webhookId: string) =>
      apiFetch<void>(`/webhooks/${webhookId}`, {
        method: "DELETE",
        headers: authHeaders()
      }),
    onSuccess: invalidateWebhooks
  });

  const testWebhook = useMutation({
    mutationFn: async (webhookId: string) =>
      WebhookTestResultSchema.parse(
        await apiFetch<unknown>(`/webhooks/${webhookId}/test`, {
          method: "POST",
          headers: authHeaders()
        })
      )
  });

  return { webhooks, createWebhook, updateWebhook, deleteWebhook, testWebhook };
}

export function useWebhookDeliveries(webhookId: string | null): UseQueryResult<WebhookDelivery[]> {
  return useQuery({
    queryKey: ["webhooks", webhookId, "deliveries"],
    enabled: Boolean(webhookId),
    queryFn: async () =>
      WebhookDeliverySchema.array().parse(
        await apiFetch<unknown>(`/webhooks/${webhookId}/deliveries`, {
          headers: authHeaders()
        })
      )
  });
}
