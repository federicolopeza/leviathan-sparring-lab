# Leviathan Sparring Lab — grpc-goat — Go gRPC (reflection on, insecure transport, no auth)
FROM golang:1.22-bookworm AS build

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT}

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /grpc-goat ./cmd/server

# --- runtime stage ---
FROM gcr.io/distroless/static-debian12

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="gRPC service — reflection enabled, insecure transport, no auth (proto enum leakage)"

COPY --from=build /grpc-goat /grpc-goat

EXPOSE 50051

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD ["/grpc-goat", "-healthcheck"]

ENTRYPOINT ["/grpc-goat"]
