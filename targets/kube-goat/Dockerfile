# Leviathan Sparring Lab — kube-goat — Deployer image for kube-goat manifests to host k3s
# This image contains kubectl + helm and a deploy.sh that applies kube-goat to the host k3s cluster.
# The actual vulnerable workloads run inside k3s on the host, not inside this container.
FROM alpine:3.19

ARG BUILD_COMMIT=unset
ENV BUILD_COMMIT=${BUILD_COMMIT} \
    KUBECTL_VERSION=v1.29.3 \
    HELM_VERSION=v3.14.3

LABEL maintainer="leviathan-lab"
LABEL org.opencontainers.image.description="kube-goat deployer — installs kube-goat manifests to host k3s (permissive RBAC, weak secrets, pod escape)"

RUN apk add --no-cache curl bash git \
    && curl -sLO https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl \
    && chmod +x kubectl && mv kubectl /usr/local/bin/ \
    && curl -sL https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz | tar xz \
    && mv linux-amd64/helm /usr/local/bin/ && rm -rf linux-amd64

COPY deploy.sh /deploy.sh
RUN chmod +x /deploy.sh

HEALTHCHECK --interval=20s --timeout=5s --retries=3 \
    CMD kubectl version --client --short || exit 1

ENTRYPOINT ["/deploy.sh"]
