"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { z } from "zod";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { InvoiceSchema, type Invoice } from "@/lib/schemas";

export type PaginatedInvoices = {
  items: Invoice[];
  page: number;
  has_next: boolean;
};

const PaginatedInvoicesSchema = z.union([
  InvoiceSchema.array().transform((items) => ({ items, page: 1, has_next: false })),
  z.object({
    items: InvoiceSchema.array(),
    page: z.number().int().default(1),
    has_next: z.boolean().default(false)
  })
]);

export function useInvoices(page: number, limit = 10): UseQueryResult<PaginatedInvoices> {
  return useQuery({
    queryKey: ["billing", "invoices", page, limit],
    queryFn: async () =>
      PaginatedInvoicesSchema.parse(
        await apiFetch<unknown>(`/billing/invoices?page=${page}&limit=${limit}`, {
          headers: authHeaders()
        })
      )
  });
}
