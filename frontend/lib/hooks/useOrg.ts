"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { OrgSchema, type Org } from "@/lib/schemas";

export function useOrg(orgId: string): UseQueryResult<Org> {
  return useQuery({
    queryKey: ["orgs", orgId],
    queryFn: async () => OrgSchema.parse(await apiFetch<unknown>(`/orgs/${orgId}`)),
    enabled: Boolean(orgId)
  });
}
