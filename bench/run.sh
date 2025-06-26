kubectl delete pod benchmark-pod
kubectl run benchmark-pod \
    --image=alpine:latest \
    --restart=Never \
    --command -- tail -f /dev/null \
    --overrides='
{
    "apiVersion": "v1",
    "spec": {
        "containers": [
        {
            "name": "benchmark-pod",
            "image": "alpine:latest",
            "resources": {
                "requests": {
                    "cpu": "2",
                    "memory": "1Gi"
                },
                "limits": {
                    "cpu": "4",
                    "memory": "2Gi"
                }
            }
        }
        ]
    }
}'

kubectl exec -it test-bench -- sh

# Prepare and install
apk add curl hey
