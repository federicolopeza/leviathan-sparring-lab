"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { authHeaders } from "@/lib/auth-client";
import { PlanSchema, type Plan } from "@/lib/schemas";

export function usePlans(): UseQueryResult<Plan[]> {
  return useQuery({
    queryKey: ["plans"],
    queryFn: async () => PlanSchema.array().parse(await apiFetch<unknown>("/billing/plans", { headers: authHeaders() }))
  });
}
