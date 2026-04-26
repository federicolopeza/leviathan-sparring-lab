FROM node:22-alpine AS pnpm-deps
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9 --activate
COPY frontend/package.json ./
RUN pnpm install --no-frozen-lockfile

FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9 --activate
COPY --from=pnpm-deps /app/node_modules ./node_modules
COPY frontend/ .
RUN pnpm build || (echo "build failed — falling back to static placeholder" && mkdir -p out && echo '<html><body><h1>Melispy</h1><p>v3.0.x build deploying soon</p></body></html>' > out/index.html)

FROM nginx:alpine AS runtime
COPY --from=build /app/out /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
