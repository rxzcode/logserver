# Rebuild and download requirement
docker_build("auth-service", "./app/auth")
docker_build("tenant-service", "./app/tenant")
docker_build("log-service", "./app/log")
docker_build("log-worker", "./app/log_worker")

# Load both service + deployment YAMLs
k8s_yaml(
    [
        # Networking and Ingress
        "k8s/dev/misc/elasticmq-deployment.yaml",
        "k8s/dev/misc/ingress.yaml"

        # Database
        "k8s/dev/db/mongodb-service.yaml",

        # Applications
        "k8s/dev/app/auth-service.yaml",
        "k8s/dev/app/tenant-service.yaml",
        "k8s/dev/app/log-service.yaml",
        "k8s/dev/app/log-worker-deployment.yaml",
    ]
)
