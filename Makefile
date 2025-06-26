# Start minikube if not already running
minikube-start:
	@minikube status | grep -q "Running" || minikube start --driver=docker --cpus=4 --memory=1000 --addons=ingress

# Start tunnel in background (for LoadBalancer services)
minikube-config:
	@nohup minikube tunnel > /dev/null 2>&1 &

# Launch Tilt (foreground)
tilt:
	@kubectl config use-context minikube
	tilt up

# Stop Tilt (but keep minikube running)
tilt-down:
	tilt down

# Full startup
up: minikube-start tilt minikube-config

# Optional: Cleanup everything
down:
	tilt down
	minikube stop
	minikube delete

# Restart services
restart:
	kubectl rollout restart deployment/auth-service
	kubectl rollout restart deployment/data-service

benchmark:
	bash scripts/run_benchmark.sh