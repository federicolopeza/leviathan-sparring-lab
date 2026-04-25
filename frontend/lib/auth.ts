import "server-only";
import { cookies } from "next/headers";
import { apiFetch } from "@/lib/api";
import { UserSchema, type User } from "@/lib/schemas";

const sessionCookieName = "melispy_session";

export async function getCurrentUser(): Promise<User | null> {
  const cookieStore = await cookies();
  const refreshToken = cookieStore.get(sessionCookieName)?.value;

  if (!refreshToken) {
    return null;
  }

  try {
    const session = await apiFetch<{ access_token: string }>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
      cache: "no-store"
    });
    const user = await apiFetch<unknown>("/users/me", {
      headers: {
        Authorization: `Bearer ${session.access_token}`
      },
      cache: "no-store"
    });

    return UserSchema.parse(user);
  } catch {
    return null;
  }
}

export async function setSessionCookie(token: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(sessionCookieName, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7
  });
}

export async function clearSessionCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(sessionCookieName);
}
