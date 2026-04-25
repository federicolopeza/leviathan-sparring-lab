"use client";

import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { UserSchema, type User } from "@/lib/schemas";

export function useUser(): UseQueryResult<User> {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => UserSchema.parse(await apiFetch<unknown>("/users/me"))
  });
}
