"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { OrgSchema, type Org } from "@/lib/schemas";

export function useOrgs(): UseQueryResult<Org[]> {
  return useQuery({
    queryKey: ["orgs", "me"],
    queryFn: async () => OrgSchema.array().parse(await apiFetch<unknown>("/orgs/me"))
  });
}
