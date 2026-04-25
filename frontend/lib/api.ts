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
  headers.set("X-Request-Id", requestId());

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(new URL(path, baseUrl), {
    ...init,
    headers
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "message" in payload
        ? String(payload.message)
        : "Solicitud rechazada";
    throw new ApiError(response.status, message);
  }

  return payload as T;
}
