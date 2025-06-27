for name in auth-service tenant-service log-service log-worker; do
  aws ecr describe-repositories --repository-names "$name" >/dev/null 2>&1 ||
  aws ecr create-repository --repository-name "$name"
done
