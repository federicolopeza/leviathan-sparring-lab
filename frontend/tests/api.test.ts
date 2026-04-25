import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/lib/api";

describe("apiFetch", () => {
  it("sets X-Request-Id and credentials include", async () => {
    process.env.NEXT_PUBLIC_API_URL = "https://api.melispy.com";
    const fetchMock = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({ ok: true }), {
      headers: { "content-type": "application/json" },
      status: 200
    }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("crypto", { randomUUID: () => "req-test-1" });

    await apiFetch<{ ok: boolean }>("/users/me");

    const [, init] = fetchMock.mock.calls[0];
    const headers = new Headers(init?.headers);
    expect(init?.credentials).toBe("include");
    expect(headers.get("X-Request-Id")).toBe("req-test-1");
    expect(headers.get("Content-Type")).toBe("application/json");
  });
});
