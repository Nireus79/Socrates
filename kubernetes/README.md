# Socrates Kubernetes Deployment

Complete Kubernetes manifests for deploying Socrates API and frontend to production.

## Directory Structure

```
kubernetes/
├── README.md                      # This file
├── namespace.yaml                 # Kubernetes namespace configuration
├── configmap.yaml                 # ConfigMaps and Secrets template
├── postgres-deployment.yaml       # PostgreSQL database
├── redis-deployment.yaml          # Redis cache and rate limiting
├── chromadb-deployment.yaml       # ChromaDB vector database
├── api-deployment.yaml            # Socrates API backend
├── frontend-deployment.yaml       # Socrates frontend (React/Vue)
└── ingress.yaml                   # Ingress controller and network policies
```

## Prerequisites

### Required Tools
- `kubectl` (1.24+)
- `helm` (optional, for Helm deployments)
- Access to a Kubernetes cluster (1.24+)
- Container registry credentials (for private images)

### Required Container Images
- `ghcr.io/your-org/socrates-api:latest` (push from docker build)
- `ghcr.io/your-org/socrates-frontend:latest` (push from docker build)
- `postgres:15-alpine` (public)
- `redis:7-alpine` (public)
- `chromadb/chroma:latest` (public)

### Storage Requirements
- PostgreSQL: 20 Gi PersistentVolume
- Redis: 10 Gi PersistentVolume
- ChromaDB: 50 Gi PersistentVolume

### Cluster Requirements
- Storage provisioner (default StorageClass or manual PVs)
- Ingress controller (nginx-ingress recommended)
- Cert-manager (for TLS certificates)
- Network policies support

## Deployment Steps

### 1. Create Namespace and ConfigMaps

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create ConfigMaps (non-sensitive configuration)
kubectl apply -f configmap.yaml

# Verify
kubectl get namespace socrates-prod
kubectl get configmap -n socrates-prod
```

### 2. Create Secrets (IMPORTANT: Use Actual Values)

```bash
# Generate strong passwords and keys
JWT_SECRET=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)
ANTHROPIC_KEY="sk-ant-xxx"  # Your actual API key

# Create secret
kubectl create secret generic socrates-secrets \
  --from-literal=database-user=socrates_user \
  --from-literal=database-password=$DB_PASSWORD \
  --from-literal=jwt-secret-key=$JWT_SECRET \
  --from-literal=anthropic-api-key=$ANTHROPIC_KEY \
  -n socrates-prod

# Verify (shows only key names, not values)
kubectl get secret socrates-secrets -n socrates-prod
kubectl describe secret socrates-secrets -n socrates-prod
```

### 3. Deploy Database Services

```bash
# Deploy PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Deploy Redis
kubectl apply -f redis-deployment.yaml

# Deploy ChromaDB
kubectl apply -f chromadb-deployment.yaml

# Wait for readiness
kubectl wait --for=condition=ready pod -l app=postgres -n socrates-prod --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n socrates-prod --timeout=300s
kubectl wait --for=condition=ready pod -l app=chromadb -n socrates-prod --timeout=300s

# Verify
kubectl get pods -n socrates-prod
kubectl get svc -n socrates-prod
```

### 4. Run Database Migrations

```bash
# Get a pod name
POD=$(kubectl get pods -l app=socrates-api -n socrates-prod -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $POD -n socrates-prod -- alembic upgrade head

# Verify schema
kubectl exec -it $(kubectl get pods -l app=postgres -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- psql -U socrates_user -d socrates -c "\dt"
```

### 5. Deploy API Backend

```bash
# Update image if using custom registry
kubectl set image deployment/socrates-api socrates-api=ghcr.io/your-org/socrates-api:latest \
  -n socrates-prod

# Deploy
kubectl apply -f api-deployment.yaml

# Wait for readiness
kubectl wait --for=condition=ready pod -l app=socrates-api -n socrates-prod --timeout=300s

# Check logs
kubectl logs -l app=socrates-api -n socrates-prod -f

# Verify API health
kubectl exec -it $(kubectl get pods -l app=socrates-api -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- curl http://localhost:8000/health
```

### 6. Deploy Frontend

```bash
# Update image if using custom registry
kubectl set image deployment/socrates-frontend socrates-frontend=ghcr.io/your-org/socrates-frontend:latest \
  -n socrates-prod

# Deploy
kubectl apply -f frontend-deployment.yaml

# Wait for readiness
kubectl wait --for=condition=ready pod -l app=socrates-frontend -n socrates-prod --timeout=300s

# Verify
kubectl get pods -n socrates-prod
```

### 7. Configure Ingress and TLS

```bash
# Install cert-manager if not already installed
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Update ingress.yaml with your domain
# Replace 'yourdomain.com' with your actual domain
sed -i 's/yourdomain\.com/your-actual-domain.com/g' ingress.yaml

# Deploy ingress and network policies
kubectl apply -f ingress.yaml

# Verify
kubectl get ingress -n socrates-prod
kubectl get networkpolicies -n socrates-prod

# Wait for TLS certificate (may take 1-2 minutes)
kubectl get certificate -n socrates-prod -w
```

### 8. Verify Deployment

```bash
# Check all resources
kubectl get all -n socrates-prod

# Check PVCs
kubectl get pvc -n socrates-prod

# Check services
kubectl get svc -n socrates-prod

# Port forward for testing (if not using ingress)
kubectl port-forward -n socrates-prod svc/socrates-api 8000:80 &
curl http://localhost:8000/health/detailed | jq .

# Check pod logs
kubectl logs -n socrates-prod -l app=socrates-api --tail=100

# Get API endpoint
kubectl get ingress -n socrates-prod -o wide
```

## Configuration

### Environment Variables

Edit `configmap.yaml` before deployment to customize:

```yaml
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  ALLOWED_ORIGINS: "https://yourdomain.com"
  RATE_LIMIT_CHAT: "30"
  CACHE_TTL_PROJECT: "1800"
  # ... etc
```

### Secrets Management

Secrets are stored in Kubernetes Secret objects:

```bash
# View secret keys (not values)
kubectl get secret socrates-secrets -n socrates-prod -o yaml | grep '    [a-z-]*:'

# Update a secret
kubectl patch secret socrates-secrets -n socrates-prod \
  -p '{"data":{"anthropic-api-key":"'$(echo -n 'new-key' | base64)'"}}'

# Rotate JWT secret (requires API restart)
kubectl patch secret socrates-secrets -n socrates-prod \
  -p '{"data":{"jwt-secret-key":"'$(openssl rand -hex 32 | base64)'"}}'
kubectl rollout restart deployment socrates-api -n socrates-prod
```

### Database Backups

```bash
# Manual backup
BACKUP_FILE="postgres_backup_$(date +%s).sql"
kubectl exec -it $(kubectl get pods -l app=postgres -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- pg_dump -U socrates_user socrates > $BACKUP_FILE

# Store in cloud storage
gsutil cp $BACKUP_FILE gs://your-backup-bucket/

# Restore from backup
gunzip -c $BACKUP_FILE | kubectl exec -it $(kubectl get pods -l app=postgres -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- psql -U socrates_user socrates
```

## Scaling

### Horizontal Scaling

```bash
# Scale API to 5 replicas
kubectl scale deployment socrates-api --replicas=5 -n socrates-prod

# Scale frontend to 3 replicas
kubectl scale deployment socrates-frontend --replicas=3 -n socrates-prod

# Monitor scaling
kubectl get hpa -n socrates-prod -w

# Auto-scaling is configured in deployment manifests
# Min/max replicas based on CPU/memory utilization
```

### Vertical Scaling

Edit `api-deployment.yaml` and update resource requests/limits:

```yaml
resources:
  requests:
    memory: "1Gi"      # Increase from 512Mi
    cpu: "500m"        # Increase from 250m
  limits:
    memory: "2Gi"      # Increase from 1Gi
    cpu: "2000m"       # Increase from 1000m
```

Apply changes:

```bash
kubectl apply -f api-deployment.yaml
kubectl rollout status deployment socrates-api -n socrates-prod
```

## Monitoring

### Health Checks

```bash
# Quick health check
kubectl exec -it $(kubectl get pods -l app=socrates-api -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- curl http://localhost:8000/health

# Detailed health check
kubectl exec -it $(kubectl get pods -l app=socrates-api -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- curl http://localhost:8000/health/detailed | jq .

# Metrics
kubectl exec -it $(kubectl get pods -l app=socrates-api -n socrates-prod -o jsonpath='{.items[0].metadata.name}') \
  -n socrates-prod -- curl http://localhost:8000/metrics
```

### Logs

```bash
# View API logs
kubectl logs -n socrates-prod -l app=socrates-api --tail=100 -f

# View PostgreSQL logs
kubectl logs -n socrates-prod -l app=postgres --tail=50

# View Redis logs
kubectl logs -n socrates-prod -l app=redis --tail=50

# Get logs from all pods
kubectl logs -n socrates-prod -l app=socrates-api --all-containers=true
```

### Pod Status

```bash
# View pod details
kubectl describe pod <pod-name> -n socrates-prod

# Get previous logs (if crashed)
kubectl logs <pod-name> -n socrates-prod --previous

# Check events
kubectl get events -n socrates-prod --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pod won't start

```bash
# Check pod events
kubectl describe pod <pod-name> -n socrates-prod

# Check resource availability
kubectl top nodes
kubectl top pods -n socrates-prod

# Check PVC status
kubectl get pvc -n socrates-prod
kubectl describe pvc <pvc-name> -n socrates-prod
```

### Database connection errors

```bash
# Verify database pod is running
kubectl get pods -l app=postgres -n socrates-prod

# Test connection from API pod
kubectl exec -it <api-pod> -n socrates-prod -- \
  psql -h postgres -U socrates_user -d socrates -c "SELECT 1"

# Check database logs
kubectl logs -l app=postgres -n socrates-prod
```

### Network connectivity issues

```bash
# Test DNS resolution
kubectl exec -it <pod> -n socrates-prod -- nslookup postgres

# Test network policies
kubectl get networkpolicies -n socrates-prod

# Test connectivity between pods
kubectl exec -it <api-pod> -n socrates-prod -- \
  curl http://postgres:5432

# Verify service endpoints
kubectl get endpoints -n socrates-prod
```

### Performance issues

```bash
# Check resource usage
kubectl top pods -n socrates-prod
kubectl top nodes

# Check slow queries
kubectl logs -l app=socrates-api -n socrates-prod | grep "Slow query"

# Check metrics
kubectl exec -it <api-pod> -n socrates-prod -- curl http://localhost:8000/metrics
```

## Rollback

### Rollback to previous version

```bash
# View rollout history
kubectl rollout history deployment socrates-api -n socrates-prod

# Rollback to previous version
kubectl rollout undo deployment socrates-api -n socrates-prod

# Rollback to specific revision
kubectl rollout undo deployment socrates-api --to-revision=2 -n socrates-prod

# Monitor rollback
kubectl rollout status deployment socrates-api -n socrates-prod -w
```

## Cleanup

### Delete all resources

```bash
# Delete entire namespace (careful!)
kubectl delete namespace socrates-prod

# Or delete specific resources
kubectl delete deployment,statefulset,service,ingress -n socrates-prod
kubectl delete pvc -n socrates-prod
kubectl delete pv -n socrates-prod
```

## Security Considerations

### RBAC

- Service accounts are created with minimal permissions
- Roles restricted to reading ConfigMaps and Secrets
- No cluster-admin or excessive privileges

### Network Policies

- Default deny all traffic
- Only allow ingress from ingress controller
- Only allow internal service communication
- DNS traffic allowed for lookups

### Pod Security

- Pods run as non-root users
- Read-only root filesystem
- No privilege escalation
- Dropped all Linux capabilities

### Secrets Management

- Secrets stored in Kubernetes Secret objects
- Never commit secrets to git
- Use external secret managers (Vault, AWS Secrets Manager) for production
- Rotate secrets regularly

## Production Checklist

- [ ] Update domain names in ingress.yaml
- [ ] Update container image registries
- [ ] Generate strong database password
- [ ] Generate strong JWT secret key
- [ ] Set actual Anthropic API key
- [ ] Configure backup storage
- [ ] Test backup/restore procedures
- [ ] Set up monitoring and logging
- [ ] Configure alerts
- [ ] Test failover procedures
- [ ] Review and update CORS origins
- [ ] Enable audit logging
- [ ] Set up log aggregation
- [ ] Test load balancing
- [ ] Verify TLS certificates
- [ ] Test scaling policies
- [ ] Document emergency procedures
- [ ] Plan disaster recovery

## Support & Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Helm Chart for Socrates](../helm/) (optional)
- [Docker Build Instructions](../docs/DEPLOYMENT.md#docker-deployment)
