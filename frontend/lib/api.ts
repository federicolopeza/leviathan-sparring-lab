export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function requestId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `req_${Date.now()}`;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!baseUrl) {
    throw new ApiError(500, "NEXT_PUBLIC_API_URL no esta configurada");
  }

  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Request-Id", requestId());

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${baseUrl.replace(/\/$/, "")}/v1${normalizedPath}`;

  const response = await fetch(url, {
    ...init,
    // V-T3-005: credentials:'include' relies on auth-service issuing Set-Cookie with domain=.melispy.com (wide scope)
    credentials: "include",
    headers
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = response.status === 204 ? null : contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "message" in payload
        ? String(payload.message)
        : typeof payload === "object" && payload !== null && "detail" in payload
          ? String(payload.detail)
        : "Solicitud rechazada";
    throw new ApiError(response.status, message);
  }

  return payload as T;
}
