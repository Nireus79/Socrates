# Deployment Documentation

Complete deployment guides for Socrates AI v2.0 in both single-process and microservices modes

## Documents in This Directory

### 1. [DEPLOYMENT_TEMPLATES.md](DEPLOYMENT_TEMPLATES.md)
**Docker and Kubernetes configurations**
- Dockerfile with multi-stage optimization
- Docker Compose for development (single-process)
- Kubernetes manifests (15+ resources)
- ConfigMap and Secrets setup
- Service definitions
- StatefulSet for persistence
- Ingress configuration
- Horizontal Pod Autoscaling (HPA)
- Health checks and readiness probes
- Monitoring and logging setup

**Use this if**: You're deploying to Docker or Kubernetes

---

### 2. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
**Overview of entire transformation**
- Timeline and phases
- Architecture decisions
- Benefits for users/developers/enterprise
- Success metrics
- Risk mitigation
- Resource requirements

**Use this if**: You need a high-level overview of the project

---

## Deployment Modes

### Single-Process (Development)
**Best for**: Local development, testing, small deployments

**Features**:
- All services in one container
- Simple setup with Docker Compose
- Low resource requirements
- Easy debugging
- Quick iteration

**Command**:
```bash
docker-compose up -d
```

**Use Cases**:
- Development environment
- Testing new features
- Learning the system
- Small teams (< 5 users)

---

### Microservices (Production)
**Best for**: Production deployments, high availability, scaling

**Features**:
- 6 independent services
- Kubernetes orchestration
- Auto-scaling (2-10 replicas)
- Load balancing
- Service discovery
- Health checks & auto-healing
- Rolling updates
- Persistent storage

**Command**:
```bash
kubectl apply -f k8s/
```

**Components**:
- Agents Service (3 replicas)
- Learning Service (2 replicas)
- Knowledge Service (2 replicas)
- Workflow Service (2 replicas)
- Analytics Service (1 replica)
- Foundation Services (shared)

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Migrations prepared
- [ ] Backups created
- [ ] Deployment window scheduled

### Deployment
- [ ] Pull latest code
- [ ] Build Docker image
- [ ] Push to registry
- [ ] Apply Kubernetes manifests
- [ ] Verify services starting
- [ ] Check logs for errors
- [ ] Run health checks

### Post-Deployment
- [ ] Verify all endpoints responding
- [ ] Check database connections
- [ ] Run smoke tests
- [ ] Monitor metrics
- [ ] Alert team
- [ ] Document deployment

### Rollback Procedure
- [ ] Identify issue
- [ ] Get previous image tag
- [ ] Apply previous manifests
- [ ] Verify services restored
- [ ] Run health checks
- [ ] Update team
- [ ] Post-mortem

## Kubernetes Resources

### ConfigMap
- Service configuration
- Environment settings
- Feature flags

### Secrets
- Database credentials
- API keys
- TLS certificates

### Services
- ClusterIP for internal communication
- LoadBalancer for external access

### StatefulSet
- Persistent volume for data
- Stable network identity
- Ordered deployment

### HPA (Horizontal Pod Autoscaler)
- Scale based on CPU usage
- Scale based on memory usage
- Min and max replicas

### Ingress
- Route external traffic
- TLS termination
- Multiple backends

## Infrastructure Requirements

### Development
- 2 CPU cores
- 4 GB RAM
- 20 GB disk

### Production
- 8+ CPU cores
- 32+ GB RAM
- 100+ GB disk
- Load balancer
- Database backup

### High Availability
- 3+ Kubernetes nodes
- Auto-scaling setup
- Database replication
- Redundant storage
- Disaster recovery plan

## Monitoring & Observability

### Metrics
- Service response times
- Error rates
- CPU/memory usage
- Request throughput
- Database performance

### Logging
- Centralized log aggregation
- Log levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs for tracing
- Retention policy (30+ days)

### Alerting
- Service down
- High error rate (>5%)
- High latency (>1s)
- Disk space low
- Database issues

## Environment Configuration

### Development
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DEBUG=true
DATABASE_URL=sqlite:///local.db
```

### Production
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false
DATABASE_URL=postgresql://prod.example.com/socrates
```

## Common Deployment Scenarios

### Scenario 1: Fresh Deployment
1. Create Kubernetes cluster
2. Create ConfigMap and Secrets
3. Apply all manifests
4. Wait for services to be ready
5. Run health checks
6. Update DNS

### Scenario 2: Update Existing Deployment
1. Pull latest code
2. Build new image
3. Push to registry
4. Update image tag in manifests
5. Apply updated manifests
6. Kubernetes does rolling update
7. Verify all services updated

### Scenario 3: Scale Services
1. Identify bottleneck service
2. Update HPA max replicas
3. Or manually scale: `kubectl scale deployment agents --replicas=10`
4. Monitor metrics
5. Verify performance improvement

### Scenario 4: Emergency Rollback
1. Identify issue
2. Get previous working image tag
3. Update manifests with previous tag
4. Apply manifests
5. Verify rollback complete
6. Run health checks

## Troubleshooting

### Service Not Starting
- Check logs: `kubectl logs deployment/agents`
- Check events: `kubectl describe pod <pod-name>`
- Verify ConfigMap: `kubectl get configmap`
- Verify Secrets: `kubectl get secret`

### High Error Rates
- Check error logs
- Verify database connectivity
- Check rate limiting
- Verify external services

### Performance Issues
- Check metrics dashboard
- Review slow queries
- Check resource limits
- Consider scaling

### Database Issues
- Check database logs
- Verify connections
- Check migrations
- Verify backups

---

**Deployment Guide Version**: 1.0
**Status**: Ready for Implementation
**Last Updated**: March 16, 2026
