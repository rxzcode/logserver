# Start minikube if not already running
minikube-start:
	@minikube status | grep -q "Running" || minikube start --driver=docker --cpus=6 --memory=4000 --addons=ingress

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

# Display useful URL for testing
url:
	@echo "Minikube IP: $$(minikube ip)"
	@echo "Try this in your browser or curl:"
	@echo "curl -X POST http://$$(minikube ip)/api/data -H 'Authorization: Bearer <jwt>' -d '{\"foo\":\"bar\"}' -H 'Content-Type: application/json'"
