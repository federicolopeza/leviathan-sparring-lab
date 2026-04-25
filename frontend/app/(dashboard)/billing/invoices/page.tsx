"use client";

import { Download } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { DataTable } from "@/components/ui/data-table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatMoney } from "@/components/features/billing/cart-summary";
import { useInvoices } from "@/lib/hooks/useInvoices";

function invoiceVariant(status: string): "success" | "warning" | "destructive" | "muted" {
  if (status === "paid" || status === "pagada") {
    return "success";
  }
  if (status === "open" || status === "pending") {
    return "warning";
  }
  if (status === "void" || status === "failed") {
    return "destructive";
  }
  return "muted";
}

export default function InvoicesPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useInvoices(page);

  return (
    <section className="mx-auto grid max-w-6xl gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">Billing</p>
        <h1 className="mt-2 text-4xl font-semibold tracking-tight">Invoices</h1>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold">Historial</h2>
          <p className="text-sm text-muted-foreground">Facturas emitidas por checkout mockeado.</p>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <DataTable
              rows={data?.items ?? []}
              getRowId={(invoice) => invoice.id}
              emptyLabel="Todavia no hay invoices emitidas."
              page={page}
              hasNextPage={data?.has_next ?? false}
              onPageChange={setPage}
              columns={[
                { key: "number", header: "Numero", cell: (invoice) => invoice.number },
                { key: "date", header: "Fecha", cell: (invoice) => new Date(invoice.issued_at).toLocaleDateString("es-UY") },
                { key: "total", header: "Total", cell: (invoice) => formatMoney(invoice.total_cents) },
                { key: "status", header: "Estado", cell: (invoice) => <Badge variant={invoiceVariant(invoice.status)}>{invoice.status}</Badge> },
                {
                  key: "download",
                  header: "Descargar",
                  cell: () => (
                    <Button type="button" variant="secondary" size="sm" disabled title="TODO Phase 3">
                      <Download className="h-4 w-4" />
                      PDF
                    </Button>
                  )
                }
              ]}
            />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
