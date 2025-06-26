hey -n 10000 -c 1000 \
    -m POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwMSIsInRlbmFudCI6ImFiYyIsInJvbGUiOiJhZG1pbiIsImF1ZCI6ImxvZ3NlcnZlciIsImlzcyI6Imlzc3VlciJ9.QHBRCx9wYl0Nml07N54kCWKOV07dl2uN4o77vdWdFtU" \
    -d '{
"action": "update",
"resource_type": "user",
"resource_id": "123",
"timestamp": "2025-06-26T01:23:45.678Z",
"ip_address": "192.168.0.1",
"user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
"before": {
    "email": "old@example.com",
    "name": "Old Name"
},
"after": {
    "email": "new@example.com",
    "name": "New Name"
},
"metadata": {
    "editor": "admin",
    "source": "dashboard"
},
"severity": "WARNING"
}' \
    http://ingress-nginx-controller.ingress-nginx.svc.cluster.local/api/v1/logs
