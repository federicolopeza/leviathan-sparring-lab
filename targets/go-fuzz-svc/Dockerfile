# Leviathan Sparring Lab — go-fuzz-svc — Go HTTP service (panic on bad input, pprof, no rate limit)
FROM golang:1.22-bookworm AS build

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -o /go-fuzz-svc .

# --- runtime stage ---
FROM debian:12-slim

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="Go HTTP service — panic on malformed input, /debug/pprof, no rate limiting"

COPY --from=build /go-fuzz-svc /go-fuzz-svc

EXPOSE 8090

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8090/health || exit 1

ENTRYPOINT ["/go-fuzz-svc"]
