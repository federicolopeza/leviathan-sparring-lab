"use client";

import { Eye, Send, Trash2 } from "lucide-react";
import { useState } from "react";
import { DeliveriesTable } from "@/components/features/webhooks/deliveries-table";
import { WebhookForm } from "@/components/features/webhooks/webhook-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Modal } from "@/components/ui/modal";
import { Skeleton } from "@/components/ui/skeleton";
import { useWebhookDeliveries, useWebhooks } from "@/lib/hooks/useWebhooks";

export default function WebhooksPage() {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedWebhookId, setSelectedWebhookId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<string | null>(null);
  const { webhooks, createWebhook, deleteWebhook, testWebhook } = useWebhooks();
  const deliveries = useWebhookDeliveries(selectedWebhookId);

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Webhooks</p>
          <h1 className="mt-2 text-4xl font-semibold tracking-tight">Eventos salientes</h1>
        </div>
        <Button type="button" onClick={() => setModalOpen(true)}>
          Nuevo webhook
        </Button>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Endpoints</h2>
          <p className="text-sm text-muted-foreground">Destinos firmados para eventos operativos.</p>
        </CardHeader>
        <CardContent>
          {webhooks.isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <DataTable
              rows={webhooks.data ?? []}
              getRowId={(webhook) => webhook.id}
              emptyLabel="Todavia no hay webhooks configurados."
              page={1}
              hasNextPage={false}
              onPageChange={() => undefined}
              columns={[
                { key: "url", header: "URL", cell: (webhook) => <span className="break-all">{webhook.url}</span> },
                { key: "events", header: "Eventos", cell: (webhook) => webhook.events.join(", ") },
                { key: "status", header: "Estado", cell: (webhook) => <Badge variant={webhook.deleted_at ? "muted" : "success"}>{webhook.deleted_at ? "eliminado" : "activo"}</Badge> },
                { key: "deliveries", header: "Entregas", cell: (webhook) => (selectedWebhookId === webhook.id ? deliveries.data?.length ?? 0 : "-") },
                {
                  key: "test",
                  header: "Test",
                  cell: (webhook) => (
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      disabled={testWebhook.isPending}
                      onClick={async () => {
                        const result = await testWebhook.mutateAsync(webhook.id);
                        setTestResult(result.message ?? (result.ok ? "Webhook probado correctamente" : "El test fallo"));
                      }}
                    >
                      <Send className="h-4 w-4" />
                      Probar
                    </Button>
                  )
                },
                {
                  key: "view",
                  header: "Ver entregas",
                  cell: (webhook) => (
                    <Button type="button" variant="secondary" size="sm" onClick={() => setSelectedWebhookId(webhook.id)}>
                      <Eye className="h-4 w-4" />
                      Ver
                    </Button>
                  )
                },
                {
                  key: "delete",
                  header: "Eliminar",
                  cell: (webhook) => (
                    <Button type="button" variant="destructive" size="sm" disabled={deleteWebhook.isPending} onClick={() => void deleteWebhook.mutateAsync(webhook.id)}>
                      <Trash2 className="h-4 w-4" />
                      Eliminar
                    </Button>
                  )
                }
              ]}
            />
          )}
          {testResult ? <p className="mt-4 rounded-lg border border-border bg-muted p-3 text-sm text-muted-foreground">{testResult}</p> : null}
        </CardContent>
      </Card>

      {selectedWebhookId ? (
        <Card>
          <CardHeader>
            <h2 className="text-xl font-semibold">Entregas recientes</h2>
            <p className="text-sm text-muted-foreground">{selectedWebhookId}</p>
          </CardHeader>
          <CardContent>{deliveries.isLoading ? <Skeleton className="h-48 w-full" /> : <DeliveriesTable deliveries={deliveries.data ?? []} />}</CardContent>
        </Card>
      ) : null}

      <Modal open={modalOpen} title="Nuevo webhook" onClose={() => setModalOpen(false)}>
        <WebhookForm
          pending={createWebhook.isPending}
          onSubmit={async (payload) => {
            await createWebhook.mutateAsync(payload);
            setModalOpen(false);
          }}
        />
      </Modal>
    </section>
  );
}
