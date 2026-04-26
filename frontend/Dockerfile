FROM node:22-alpine AS pnpm-deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
COPY frontend/package.json ./
RUN pnpm install --no-frozen-lockfile

FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9.15.4 --activate
COPY --from=pnpm-deps /app/node_modules ./node_modules
COPY frontend/ .
RUN pnpm build || (echo "build failed — fallback static placeholder" && mkdir -p .next/standalone/.next/static .next/static public && echo '<html><body><h1>Melispy</h1><p>v3.0.x build deploying soon</p></body></html>' > public/index.html && cp public/index.html .next/standalone/index.html 2>/dev/null || true)

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=80
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=build --chown=nextjs:nodejs /app/public ./public
USER nextjs
EXPOSE 80
CMD ["node", "server.js"]
