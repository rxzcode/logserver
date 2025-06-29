#!/bin/bash

set -e

POD_NAME="benchmark-pod"

echo "Checking if $POD_NAME exists..."
if ! kubectl get pod "$POD_NAME" &>/dev/null; then
    echo "Creating new benchmark pod..."
    kubectl run "$POD_NAME" \
        --image=alpine:latest \
        --restart=Never \
        --command -- tail -f /dev/null
else
    echo "$POD_NAME already exists. Reusing it."
fi

echo "Waiting for pod to be in Running state..."
kubectl wait --for=jsonpath='{.status.phase}'=Running pod/"$POD_NAME" --timeout=30s

echo "Installing curl and hey inside pod if not already installed..."
kubectl exec "$POD_NAME" -- sh -c '
  if ! command -v curl > /dev/null || ! command -v hey > /dev/null; then
    echo "Installing curl and hey..."
    apk add --no-cache curl hey
  else
    echo "curl and hey already installed"
  fi
'

echo "Running hey benchmark..."
kubectl exec "$POD_NAME" -- sh -c "
  hey -n 10000 -c 1000 \
    -m POST \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwMSIsInRlbmFudCI6ImFiYyIsInJvbGUiOiJhZG1pbiIsImF1ZCI6ImxvZ3NlcnZlciIsImlzcyI6Imlzc3VlciJ9.QHBRCx9wYl0Nml07N54kCWKOV07dl2uN4o77vdWdFtU' \
    -d '{
      \"action\": \"update\",
      \"resource_type\": \"user\",
      \"resource_id\": \"123\",
      \"timestamp\": \"2025-06-23T01:23:45.678Z\",
      \"ip_address\": \"192.168.0.1\",
      \"user_agent\": \"Mozilla/5.0 (Windows NT 10.0; Win64; x64)\",
      \"before\": {\"email\": \"old@example.com\", \"name\": \"Old Name\"},
      \"after\": {\"email\": \"new@example.com\", \"name\": \"New Name\"},
      \"metadata\": {\"editor\": \"admin\", \"source\": \"dashboard\"},
      \"severity\": \"ERROR\"
    }' \
    http://ingress-nginx-controller.ingress-nginx.svc.cluster.local/api/v1/logs
"
