"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { MembershipSchema, type Membership } from "@/lib/schemas";

export function useMembers(orgId: string): UseQueryResult<Membership[]> {
  return useQuery({
    queryKey: ["orgs", orgId, "members"],
    queryFn: async () => MembershipSchema.array().parse(await apiFetch<unknown>(`/orgs/${orgId}/members`)),
    enabled: Boolean(orgId)
  });
}
