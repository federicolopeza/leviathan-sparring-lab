FROM node:22-alpine AS pnpm-deps
WORKDIR /app
RUN corepack enable
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS build
WORKDIR /app
RUN corepack enable
COPY --from=pnpm-deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

FROM nginx:alpine AS runtime
COPY --from=build /app/out /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
