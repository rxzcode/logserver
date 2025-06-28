#############
# LOCAL DEV #
#############

# Start minikube if not already running
minikube-start:
	@minikube status | grep -q "Running" || minikube start --driver=docker --cpus=4 --addons=ingress
	@kubectl config use-context minikube

minikube-tunnel:
	@sudo pkill -f "minikube tunnel" || true
	@sudo nohup minikube tunnel > /dev/null 2>&1 &
	@sleep 3
	@echo "✅ Tunnel started (PID: $$(pgrep -f 'minikube tunnel'))"

# Launch Tilt (foreground)
tilt:
	tilt up

# Stop Tilt (but keep minikube running)
tilt-down:
	tilt down

# Full startup
up: minikube-start minikube-tunnel tilt

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


###########
# AWS K8S #
###########
up-prod:
	@kubectl config use-context YOUR_EKS_CONTEXT
	bash scripts/prepare_ecr.sh
	bash scripts/prepare_info.sh
	bash scripts/prepare_cluster.sh
	tilt up -f Tiltfile-production

tilt-prod:
	tilt up -f Tiltfile-production

cost:
	./scripts/aws_cost.sh

########
# TEST #
########
test:
	./scripts/test_all.sh
