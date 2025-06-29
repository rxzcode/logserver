# 🚀 Python Log Server

A high-performance, multi-tenant log server built with **Python** and **FastAPI**.

🔗 [**Live Demo**](http://k8s-ingressn-nginxing-224a407861-0fde472c69e54cd3.elb.ap-southeast-1.amazonaws.com/api/v1/logs)

```bash
# On staging machine AWS-EKS, don't worry i will shutdown it soon
# Try to get log stats, it tenant scoped
curl --location 'http://k8s-ingressn-nginxing-224a407861-0fde472c69e54cd3.elb.ap-southeast-1.amazonaws.com/api/v1/logs/stats' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwMSIsInRlbmFudCI6ImFiYyIsInJvbGUiOiJhZG1pbiIsImF1ZCI6ImxvZ3NlcnZlciIsImlzcyI6Imlzc3VlciJ9.QHBRCx9wYl0Nml07N54kCWKOV07dl2uN4o77vdWdFtU'

# Open websocket for streaming logs
wscat -c "ws://k8s-ingressn-nginxing-224a407861-0fde472c69e54cd3.elb.ap-southeast-1.amazonaws.com/api/v1/logs/stream?token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwMSIsInRlbmFudCI6ImFiYyIsInJvbGUiOiJhZG1pbiIsImF1ZCI6ImxvZ3NlcnZlciIsImlzcyI6Imlzc3VlciJ9.QHBRCx9wYl0Nml07N54kCWKOV07dl2uN4o77vdWdFtU"

# Add a logs for watch stream
curl --location 'http://k8s-ingressn-nginxing-224a407861-0fde472c69e54cd3.elb.ap-southeast-1.amazonaws.com/api/v1/logs' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwMSIsInRlbmFudCI6ImFiYyIsInJvbGUiOiJhZG1pbiIsImF1ZCI6ImxvZ3NlcnZlciIsImlzcyI6Imlzc3VlciJ9.QHBRCx9wYl0Nml07N54kCWKOV07dl2uN4o77vdWdFtU' \
--data-raw '{
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
}'
```

---

## 📘 API Endpoints

| Method | Endpoint                     | Description                           | Tenant Scoped |
|--------|------------------------------|---------------------------------------|----------------|
| POST   | `/api/v1/logs`               | Create a log entry                    | ✅ Yes         |
| GET    | `/api/v1/logs`               | Search/filter logs                    | ✅ Yes         |
| GET    | `/api/v1/logs/{id}`          | Get a specific log entry              | ✅ Yes         |
| GET    | `/api/v1/logs/export`        | Export logs                           | ✅ Yes         |
| GET    | `/api/v1/logs/stats`         | Retrieve log statistics               | ✅ Yes         |
| POST   | `/api/v1/logs/bulk`          | Bulk log creation                     | ✅ Yes         |
| DELETE | `/api/v1/logs/cleanup`       | Clean up old logs                     | ✅ Yes         |
| WS     | `/api/v1/logs/stream`        | Real-time log streaming (WebSocket)   | ✅ Yes         |
| GET    | `/api/v1/tenants`            | List tenants (Admin only)             | ❌ No          |
| POST   | `/api/v1/tenants`            | Create a tenant (Admin only)          | ❌ No          |

---

## 📁 Project Structure

```text
logserver/
├── app/
│   ├── auth/         # Auth service (embedded or AWS Lambda behind ALB)
│   ├── log/          # Log API service
│   ├── log_worker/   # Background SQS log processing
│   └── tenant/       # Tenant management
│
├── k8s/
│   └── app/          # Kubernetes deployment YAMLs
│
└── scripts/          # Benchmarking and utility scripts
```

---

## ✅ Todo Summary

- [x] Core audit log APIs
- [x] Database setup (PostgreSQL, MongoDB, or DynamoDB)
- [x] Gateway/ALB configuration
- [x] Search and filter capabilities
- [x] Multi-tenant DB schema
- [x] JWT-based auth with role scoping
- [x] Security and validation
- [x] SQS for async processing
- [x] Tenant management

- [x] Unit test coverage 95% log service
- [x] Latency < 100ms
- [x] Scale up 1000 CCU
- [x] Websocket realtime stream log
- [x] CubeJS dashboard + Clickhouse (bigdata) - cube.localhost
- [x] Optimize stats API with mongo index

---

## 🧱 High-Level Architecture

### 🔹 Microservices

| Service       | Responsibility |
|---------------|----------------|
| `auth`        | JWT authentication, RBAC, tenant isolation. Runs as FastAPI or AWS Lambda. |
| `log`         | Handles all log CRUD, filtering, exporting, and statistics. |
| `log_worker`  | Background processor (SQS/ElasticMQ consumer). |
| `tenant`      | Tenant creation and listing (admin access). |

---

### 🔹 Key Features

- **Multi-Tenancy**: Isolates data per `tenant_id`, supports roles: `admin`, `auditor`, `viewer`.
- **Event-Driven**: Logs sent via API → SQS → async `log_worker`.
- **Real-Time Streaming**: WebSocket `/logs/stream` for tenant-specific updates.
- **RBAC Authentication**: Role-based access via JWT.

---

## ⚙️ Deployment Overview

| Layer         | Local (Minikube)                | Production (AWS)                     |
|---------------|----------------------------------|--------------------------------------|
| Gateway       | `ingress-nginx`                 | AWS ALB                              |
| Auth          | FastAPI microservice            | AWS Lambda (RBAC handler)            |
| Messaging     | `ElasticMQ`                     | AWS SQS                              |
| Database      | Local MongoDB container         | MongoDB Atlas or EC2                 |
| K8s Infra     | Tilt, Makefile, Minikube        | EKS, ArgoCD, Terraform               |

---

## 🔁 Request Flow (Textual)

```text
Client
  ↓
Ingress (nginx or ALB)
  ↓
Auth Service (JWT + RBAC)
  ├─ [✅ OK] → Log Service → MongoDB
  ├─ [✅ OK] → Tenant Service
  └─ [❌ Not OK] → 401 Unauthorized
```

## 🔁 Request Flow (Mermaid Diagram)

```mermaid
---
config:
  flowchart:
    htmlLabels: false
  layout: dagre
---
flowchart LR
  A["Client"] --> B["Ingress / ALB"]
  B --> C{"Auth RBAC"}
  C -- ✅ OK --> D["Log Service"] & E["Tenant Service"]
  D --> SQS["SQS Queue"] & WS["WebSocket Broadcast"]
  SQS --> LW["Log Worker"]
  LW --> DB["MongoDB"]
  C -- ❌ Not OK --> F["401 Unauthorized"]
```

---

## 🧪 Installation & Development

### 1. Clone and Run Locally

> Requires: [Tilt](https://tilt.dev), [Docker](https://www.docker.com/), [Minikube](https://minikube.sigs.k8s.io/)

```bash
git clone https://github.com/rxzcode/logserver.git
cd logserver
make up             # Starts Minikube and runs services via Tilt
minikube tunnel     # Opens access to http://localhost/api/v1/logs
```

### 2. Run Benchmark

```bash
make benchmark      # Launches a benchmarking pod inside Minikube using hey
```

### 3. Local Python Development

```bash
# At root folder
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Deploy to AWS (Production)

```bash
# Spin up production infrastructure and deploy using Tilt
make up-prod
```

### 5. Unit test and coverage

```bash
# Run unit test coverage and combine, with html server
make test
```

---

## 📜 License

This project is licensed under the **MIT License**.
Contributions welcome — Happy Coding! 😊

---

## 📊 Benchmark Results, Others

> Postman API:

- [📥 Download Postman Collection](./extra/LogServer.postman_collection.v1.1.json)
- [📥 Download Postman Local Env](./extra/log-localhost.postman_environment.json)
- [📥 Download Postman Stage Env](./extra/log-aws.postman_environment.json)

> Postman pics:
![Postman](./extra/PostmanAPI.png)
> Unit test coverage (make test):
![Websocket](./extra/UnitTest.png)
> Websocket:
![Websocket](./extra/Websocket.png)
> Load Test: 10,000 requests, 1,000 concurrent (hey -n 10000 -c 1000)
> It on local docker + minikube (cause aws fee 😃)
![Benchmark Result](./extra/benchmark.png)
> CUBEJS Dashboard cube.localhost: Example with 10_000_000 rows of logs (<1s query)
![Benchmark Result](./extra/CubeJS.png)

```json
{
  "measures": ["logs.count"],
  "dimensions": ["logs.severity"],
  "timeDimensions": [
    {
      "dimension": "logs.timestamp",
      "granularity": "day",
      "dateRange": "last 30 days"
    }
  ],
  "order": {
    "logs.timestamp": "asc"
  },
  "pivotConfig": {
    "x": ["logs.timestamp.day"],
    "y": ["logs.severity"],
    "fillMissingDates": true,
    "joinDateRange": false
  }
}
```

- With [ClickHouse](https://clickhouse.com/) and an index like `ENGINE = MergeTree ORDER BY (tenant_id, timestamp, ...)`, you can **query and aggregate billions of rows in seconds**. There’s a [ClickHouse Cloud](https://clickhouse.com/cloud) option as well — it’s often **significantly cheaper than [Snowflake](https://www.snowflake.com/)**.
- It works perfectly with [CubeJS](https://cube.dev/) [pre-aggregations](https://cube.dev/docs/pre-aggregations/introduction) for high-performance analytics.

👉 [See this public demo of querying 1 billion rows](https://play.clickhouse.com/play?file=billion-row-log-query) using ClickHouse.
