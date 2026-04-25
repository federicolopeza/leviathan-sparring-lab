# Melispy Frontend

Next.js 16 App Router frontend for the Melispy fintech SaaS lab.

## Local dev

```bash
pnpm install
pnpm dev
```

Quality gates:

```bash
pnpm typecheck
pnpm lint
pnpm test
pnpm build
```

The app expects `NEXT_PUBLIC_API_URL` to point at the Melispy API gateway.

## Static export

Production builds use `output: "export"` and emit static files to `out/`.
The Docker image serves that folder through `nginx:alpine`.
App Router route handlers under `app/api/` are available in local Next.js
runtime, but a pure nginx static export does not execute server-side route
handlers. Production deployments that need the auth proxy must route those
requests to the API gateway or run a Node/edge frontend runtime.

## Threat model

### V-T1-004: production source maps

`next.config.mjs` intentionally enables `productionBrowserSourceMaps`.
This exposes compiled frontend source maps in production so lab operators and
attackers can fingerprint client code paths during reconnaissance. This is a
deliberate Tier 1 information disclosure challenge, not an accidental hardening
miss. Remove it only when patching or advancing the lab version that mitigates
`V-T1-004`.
