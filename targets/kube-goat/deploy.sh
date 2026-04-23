#!/usr/bin/env bash
# deploy.sh — deploys kube-goat to the host k3s cluster
# KUBECONFIG must be mounted from host: -v /etc/rancher/k3s/k3s.yaml:/root/.kube/config:ro
set -e

KUBE_GOAT_VERSION="${KUBE_GOAT_VERSION:-v2.0}"
MANIFEST_URL="https://raw.githubusercontent.com/ksoclabs/kube-goat/${KUBE_GOAT_VERSION}/deployments/kubernetes"

echo "[kube-goat] Cloning manifests..."
git clone --depth 1 --branch "${KUBE_GOAT_VERSION}" https://github.com/ksoclabs/kube-goat.git /tmp/kube-goat 2>/dev/null || true

if [ -d /tmp/kube-goat/deployments/kubernetes ]; then
    echo "[kube-goat] Applying manifests..."
    kubectl apply -f /tmp/kube-goat/deployments/kubernetes/ --recursive
else
    echo "[kube-goat] Manifest directory not found — apply manually"
    exit 1
fi

echo "[kube-goat] Deployed. Waiting for pods..."
kubectl wait --for=condition=available --timeout=120s deployment --all -n kube-goat 2>/dev/null || true
kubectl get pods -n kube-goat 2>/dev/null || kubectl get pods --all-namespaces
echo "[kube-goat] Done."
