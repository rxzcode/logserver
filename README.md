# Python log server
A log server write with Python and FastAPI
- [Live Demo](https://vue-dbml.devseason.com)

### 📘 Project APIs

| Method | Endpoint                       | Description                            | Tenant Scoped |
|--------|--------------------------------|----------------------------------------|----------------|
| POST   | `/api/v1/logs`                 | Create a log entry                     | ✅ Yes         |
| GET    | `/api/v1/logs`                 | Search/filter logs                     | ✅ Yes         |
| GET    | `/api/v1/logs/{id}`            | Get specific log entry                 | ✅ Yes         |
| GET    | `/api/v1/logs/export`          | Export logs                            | ✅ Yes         |
| GET    | `/api/v1/logs/stats`           | Get log statistics                     | ✅ Yes         |
| POST   | `/api/v1/logs/bulk`            | Bulk log creation                      | ✅ Yes         |
| DELETE | `/api/v1/logs/cleanup`         | Cleanup old logs                       | ✅ Yes         |
| WS     | `/api/v1/logs/stream`          | Real-time log streaming via WebSocket  | ✅ Yes         |
| GET    | `/api/v1/tenants`              | List accessible tenants (admin only)   | ❌ No (Admin)  |
| POST   | `/api/v1/tenants`              | Create a new tenant (admin only)       | ❌ No (Admin)  |

### Project structure folder

### FLow chart
![Flowchart](./extra/flowchart.png)
```mermaid
---
config:
  flowchart:
    htmlLabels: false
  layout: dagre
---
flowchart LR
 subgraph s1["Gateway and Auth"]
        C{"Auth RBAC"}
        B["Ingress ALB"]
  end
    B --> C
    A["Client"] --> s1
    s1 -- ✅ OK --> D["Log Service"] & E["Tenant Service"]
    D --> SQS["SQS Message"] & WS["Broadcast Service"]
    SQS --> LW["Log Worker"]
    LW --> DB["MongoDB"]
    s1 -- ❌ Not OK --> F["401 Unauthorized"]
```

---

## Todo
- [x] Core audit log creation and retrieval API endpoints
- [x] Database setup and configuration (PostgreSQL/MongoDB/DynamoDB)
- [x] API Gateway or ALB setup and configuration
- [x] Basic search and filtering functionality
- [x] Database schema design and implementation with multi-tenant support
- [x] Authentication and authorization system with tenant isolation
- [x] Basic security controls and data validation
- [x] AWS SQS setup for background processing
- [x] Multi-tenant implementation and tenant management

---

## Tools
- ⚡ **Fast Development**: Docker, Minikube, Tilt
- 🛠️ **Component-Based Architecture**:
    - App Services: auth, log, tenant, log-worker (Python, fastAPI)
    - Database: MongoDB (local), Atlas (AWS)
    - Gateway: ingress-nginx (local), ingress-alb (AWS)
    - Message: ElasticMQ (local), SQS (AWS)

---

## Installation

1. **Clone the Repository**
    Install tilt: https://tilt.dev/
    Install docker: https://www.docker.com/

    Run the following commands to clone and set up the project:
    Tilt will watch services code changes and reload service
    ```bash
    git clone https://github.com/rxzcode/logserver.git
    cd logserver
    make up # It bring up minikube K8S cluster, run all apps, services with tilt
    minikube tunnel # Use it to open port for K8S server: http://localhost/api/v1/logs
    ```

    Run benchmark, it bring a minikube pod to run Hey
    ```bash
    make benchmark
    ```

    For local dev IDE linting, linking libs
    ```bash
    # At root folder
    python -m .venv
    source .env/bin/activate
    pip install -r requirements.txt
    ```

2. **Deploy AWS K8S**:
    ```bash
    # Create cluster
    # Use tilt production
    make up-prod

3. **License**:
   - This project is licensed under the MIT License. Please provide attribution to @rxzcode.

# Extra: benchmark result
- With 10k total - 1k concurrent
![Benchmark](./extra/benchmark.png)