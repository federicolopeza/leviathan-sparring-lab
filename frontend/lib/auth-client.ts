"use client";

import { apiFetch } from "@/lib/api";
import type { LoginInput, SignupInput } from "@/lib/schemas";

type LoginResponse = {
  access_token: string;
  refresh_token?: string;
  expires_in?: number;
};

// Access token held in module closure only — never persisted to localStorage/sessionStorage
// where injected JS could read it. Trade-off: lost on full page reload, user re-logs.
// Phase 5 will move to silent cookie-based refresh so the token never touches client JS.
let cachedAccessToken: string | null = null;

export function getAccessToken(): string | null {
  return cachedAccessToken;
}

export function setAccessToken(token: string | null): void {
  cachedAccessToken = token;
}

export function authHeaders(): HeadersInit {
  return cachedAccessToken ? { Authorization: `Bearer ${cachedAccessToken}` } : {};
}

export async function loginAction(payload: LoginInput): Promise<LoginResponse> {
  const response = await apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
  cachedAccessToken = response.access_token;
  return response;
}

export async function signupAction(
  payload: SignupInput
): Promise<{ user_id: string; email_verify_required: boolean }> {
  return apiFetch("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function logoutAction(): Promise<void> {
  try {
    // Cookie carries refresh_token; no Bearer header needed (and persisting one would re-introduce XSS exposure).
    await apiFetch<void>("/auth/logout", { method: "POST" });
  } finally {
    cachedAccessToken = null;
  }
}

export async function forgotAction(email: string): Promise<{ ok: boolean }> {
  return apiFetch("/auth/forgot", {
    method: "POST",
    body: JSON.stringify({ email })
  });
}

export async function verifyAction(token: string): Promise<{ ok: boolean }> {
  return apiFetch("/auth/verify", {
    method: "POST",
    body: JSON.stringify({ token })
  });
}

// TODO Phase 5: silent cookie-based refresh. Phase 1 keeps user re-login on access expiry (15 min).
export async function refreshAction(): Promise<never> {
  throw new Error("refresh_not_implemented_in_phase_1");
}
