"use client";

import { useMutation, useQueryClient, type UseMutationResult } from "@tanstack/react-query";
import { z } from "zod";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { InvoiceSchema, type Invoice } from "@/lib/schemas";

const CheckoutInvoiceResponseSchema = z.union([InvoiceSchema, z.object({ invoice: InvoiceSchema })]);

export function useCheckout(): UseMutationResult<Invoice, Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const parsed = CheckoutInvoiceResponseSchema.parse(
        await apiFetch<unknown>("/billing/checkout", {
          method: "POST",
          headers: authHeaders()
        })
      );
      return "invoice" in parsed ? parsed.invoice : parsed;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["billing", "cart"] });
      void queryClient.invalidateQueries({ queryKey: ["billing", "invoices"] });
    }
  });
}
