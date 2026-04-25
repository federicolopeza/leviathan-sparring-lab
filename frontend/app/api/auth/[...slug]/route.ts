import { NextResponse, type NextRequest } from "next/server";

type RouteContext = {
  params: Promise<{
    slug?: string[];
  }>;
};

async function proxyAuth(request: NextRequest, context: RouteContext): Promise<Response> {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!baseUrl) {
    return NextResponse.json({ message: "Auth backend no configurado" }, { status: 500 });
  }

  const { slug = [] } = await context.params;
  const upstreamUrl = new URL(`/v1/auth/${slug.join("/")}`, baseUrl);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");

  if (cookie) {
    headers.set("cookie", cookie);
  }
  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (accept) {
    headers.set("accept", accept);
  }

  headers.set("X-Request-Id", crypto.randomUUID());

  try {
    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: request.method === "GET" ? undefined : await request.text(),
      cache: "no-store"
    });

    const responseHeaders = new Headers();
    const upstreamContentType = upstream.headers.get("content-type");
    const setCookie = upstream.headers.get("set-cookie");

    if (upstreamContentType) {
      responseHeaders.set("content-type", upstreamContentType);
    }
    if (setCookie) {
      responseHeaders.set("set-cookie", setCookie);
    }

    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: responseHeaders
    });
  } catch {
    return NextResponse.json({ message: "Auth upstream no disponible" }, { status: 502 });
  }
}

export async function GET(request: NextRequest, context: RouteContext): Promise<Response> {
  return proxyAuth(request, context);
}

export async function POST(request: NextRequest, context: RouteContext): Promise<Response> {
  return proxyAuth(request, context);
}
