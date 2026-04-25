import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
import type { WebhookDelivery } from "@/lib/schemas";

function deliveryVariant(status: string): "success" | "warning" | "destructive" | "muted" {
  if (status === "success" || status === "delivered") {
    return "success";
  }
  if (status === "pending" || status === "retrying") {
    return "warning";
  }
  if (status === "failed") {
    return "destructive";
  }
  return "muted";
}

export function DeliveriesTable({ deliveries }: { deliveries: WebhookDelivery[] }) {
  return (
    <DataTable
      rows={deliveries}
      getRowId={(delivery) => delivery.id}
      emptyLabel="Todavia no hay entregas para este webhook."
      page={1}
      hasNextPage={false}
      onPageChange={() => undefined}
      columns={[
        { key: "event", header: "Evento", cell: (delivery) => delivery.event_type },
        { key: "status", header: "Estado", cell: (delivery) => <Badge variant={deliveryVariant(delivery.status)}>{delivery.status}</Badge> },
        { key: "attempts", header: "Reintentos", cell: (delivery) => delivery.attempt_count },
        { key: "date", header: "Ultimo intento", cell: (delivery) => new Date(delivery.last_attempted_at).toLocaleString("es-UY") }
      ]}
    />
  );
}
