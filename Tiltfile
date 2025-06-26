# Rebuild and download requirement
docker_build("auth-service", "./app/auth")
docker_build("tenant-service", "./app/tenant")
docker_build("log-service", "./app/log")
docker_build("log-worker", "./app/log_worker")

# Load both service + deployment YAMLs
k8s_yaml(
    [
        # Database
        "k8s/db/mongodb-deployment.yaml",
        "k8s/db/mongodb-service.yaml",
        "k8s/misc/elasticmq-deployment.yaml",

        # Applications
        "k8s/app/auth-deployment.yaml",
        "k8s/app/auth-service.yaml",
        "k8s/app/tenant-deployment.yaml",
        "k8s/app/tenant-service.yaml",
        "k8s/app/log-deployment.yaml",
        "k8s/app/log-service.yaml",
        "k8s/app/log-worker-deployment.yaml",

        # Networking and Ingress
        "k8s/network/ingress.yaml"
    ]
)
