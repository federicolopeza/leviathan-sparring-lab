"use client";

import { useMutation, useQueryClient, type UseMutationResult } from "@tanstack/react-query";
import { logoutAction } from "@/lib/auth-client";
import { apiFetch } from "@/lib/api";
import { InvitationSchema, OrgSchema, UserSchema, type Invitation, type Org, type User } from "@/lib/schemas";

type CreateOrgInput = {
  name: string;
  plan: Org["plan"];
  region: string;
};

type InviteInput = {
  email: string;
  role: "admin" | "member";
};

type PatchProfileInput = {
  name: string;
  bio: string | null;
  avatar_url: string | null;
};

type PatchOrgInput = Partial<CreateOrgInput>;

export function useCreateOrg(): UseMutationResult<Org, Error, CreateOrgInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) =>
      OrgSchema.parse(
        await apiFetch<unknown>("/orgs", {
          method: "POST",
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["orgs"] });
    }
  });
}

export function useInvite(orgId: string): UseMutationResult<Invitation, Error, InviteInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) =>
      InvitationSchema.parse(
        await apiFetch<unknown>(`/orgs/${orgId}/invitations`, {
          method: "POST",
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["orgs", orgId, "invitations"] });
      void queryClient.invalidateQueries({ queryKey: ["orgs", orgId, "members"] });
    }
  });
}

export function usePatchProfile(): UseMutationResult<User, Error, PatchProfileInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) =>
      UserSchema.parse(
        await apiFetch<unknown>("/users/me", {
          method: "PATCH",
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["me"] });
    }
  });
}

export function usePatchOrg(orgId: string): UseMutationResult<Org, Error, PatchOrgInput> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload) =>
      OrgSchema.parse(
        await apiFetch<unknown>(`/orgs/${orgId}`, {
          method: "PATCH",
          body: JSON.stringify(payload)
        })
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["orgs"] });
      void queryClient.invalidateQueries({ queryKey: ["orgs", orgId] });
    }
  });
}

export function useLogout(): UseMutationResult<void, Error, void> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logoutAction,
    onSuccess: () => {
      queryClient.clear();
    }
  });
}
