# Deployment Checklist for Socrates

## Pre-Deployment (1-2 hours before)

### Infrastructure
- [ ] Database is running and accessible
- [ ] Redis cache is running and accessible
- [ ] PostgreSQL backups are configured
- [ ] Backup verification test passed
- [ ] Sufficient disk space available (min 50GB)
- [ ] Network connectivity verified

### Code & Dependencies
- [ ] All code committed to repository
- [ ] All tests passing locally
- [ ] Code review completed
- [ ] Dependencies updated and locked
- [ ] No security vulnerabilities found (safety check passed)
- [ ] TypeScript compilation successful

### Configuration
- [ ] `.env.production` created with all required variables
- [ ] Secrets properly encrypted and stored
- [ ] Database credentials rotated
- [ ] SSL certificates valid and installed
- [ ] CORS settings configured correctly
- [ ] Allowed hosts list updated

### Documentation
- [ ] Deployment runbook reviewed
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured
- [ ] Team notified of deployment window
- [ ] Communication channels established

## Staging Deployment (2-4 hours)

### Initial Setup
- [ ] Clone repository to staging server
- [ ] Create Python virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Install development tools: `pip install -e ".[dev]"`
- [ ] Copy .env.staging to /etc/socrates/.env.staging
- [ ] Set proper file permissions (chmod 600 for secrets)

### Database
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify database schema
- [ ] Seed test data (if needed)
- [ ] Run database integrity checks
- [ ] Verify backup/restore procedures

### Backend Services
- [ ] Start API service: `systemctl start socrates-api`
- [ ] Verify service status: `systemctl status socrates-api`
- [ ] Check API logs for errors
- [ ] Health check endpoint responding: `curl http://localhost:8000/health`
- [ ] API documentation accessible: `curl http://localhost:8000/docs`

### Frontend Services
- [ ] Install Node.js dependencies: `npm ci`
- [ ] Build optimized version: `npm run build`
- [ ] Static files served correctly
- [ ] API connectivity working
- [ ] Environment variables loaded correctly

### Reverse Proxy
- [ ] Nginx configuration syntax valid: `nginx -t`
- [ ] SSL certificates loaded
- [ ] HTTPS working: `curl -k https://localhost`
- [ ] HTTP redirects to HTTPS
- [ ] Security headers present
- [ ] Static file caching working

### Testing
- [ ] Health check: API responds to /health
- [ ] Database health: Can execute queries
- [ ] Redis health: Can set/get values
- [ ] File uploads working
- [ ] Project generation working
- [ ] Export functionality working
- [ ] GitHub integration (if configured)

### Monitoring
- [ ] Application logs flowing
- [ ] Metrics endpoint working: `/metrics`
- [ ] Performance baseline recorded
- [ ] Alerts configured and tested
- [ ] Log aggregation working

## Production Deployment (2-4 hours)

### Pre-Deployment
- [ ] Staging deployment successful and verified
- [ ] All tests passing in staging
- [ ] Performance acceptable in staging
- [ ] No critical issues found
- [ ] Production maintenance window scheduled
- [ ] Team ready for deployment

### Backup Before Deployment
- [ ] Full database backup created
- [ ] Backup verified (restore test)
- [ ] File uploads backup created
- [ ] Configuration backup created
- [ ] Backups stored in secure location

### Production Setup
- [ ] Clone stable branch to production
- [ ] Create virtual environment
- [ ] Install dependencies
- [ ] Copy .env.production
- [ ] Set correct permissions and ownership
- [ ] Verify all configuration files

### Production Deployment
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Clear caches: `redis-cli FLUSHDB` (if safe)
- [ ] Start API service: `systemctl start socrates-api`
- [ ] Wait 30 seconds for service stabilization
- [ ] Health check: `curl https://yourdomain.com/health`
- [ ] Verify service is running: `systemctl status socrates-api`

### Post-Deployment Verification
- [ ] API responding to requests
- [ ] Database queries working
- [ ] Frontend accessible
- [ ] HTTPS working
- [ ] Security headers present
- [ ] Static files serving with correct cache headers
- [ ] Logs show no errors
- [ ] Metrics showing healthy service

### Smoke Tests
- [ ] Can login with test account
- [ ] Can create a new project
- [ ] Can finalize a project
- [ ] Can export a project
- [ ] Can view project details
- [ ] Can update project settings
- [ ] GitHub integration working (if enabled)

### Monitoring & Alerts
- [ ] Application monitoring active
- [ ] Error tracking working (Sentry, etc.)
- [ ] Performance monitoring active
- [ ] Uptime checks reporting
- [ ] Alert notifications configured
- [ ] Team members have access to dashboards

## Post-Deployment (Ongoing)

### Day 1
- [ ] Monitor logs for errors
- [ ] Check performance metrics
- [ ] Verify no spike in error rates
- [ ] Check database performance
- [ ] Verify backups completed
- [ ] Team debriefing completed

### Week 1
- [ ] Monitor uptime and performance
- [ ] Check error rates trending down/stable
- [ ] Verify all features working
- [ ] User feedback checked
- [ ] Performance baseline compared

### Ongoing
- [ ] Regular monitoring of logs and metrics
- [ ] Weekly backup verification
- [ ] Monthly security updates
- [ ] Performance optimization
- [ ] Documentation updates

## Rollback Procedures

### Quick Rollback (< 5 minutes)
1. Revert to previous container image: `docker pull socrates:v1.x.x`
2. Stop current service: `systemctl stop socrates-api`
3. Start previous version: `systemctl start socrates-api`
4. Verify health: `curl https://yourdomain.com/health`

### Full Rollback (with database)
1. Stop all services
2. Restore database from backup: `pg_restore < backup.sql`
3. Restore file uploads from backup
4. Revert configuration files
5. Restart services
6. Verify all functionality

## Emergency Contacts

- **On-Call Engineer:** [Phone/Slack]
- **Database Admin:** [Phone/Slack]
- **Infrastructure Lead:** [Phone/Slack]
- **Project Lead:** [Phone/Slack]

## Success Criteria

- ✅ All health checks passing
- ✅ Error rate < 0.1%
- ✅ Response time < 500ms (p95)
- ✅ Database queries < 100ms (p95)
- ✅ CPU usage < 50%
- ✅ Memory usage < 2GB
- ✅ Disk space > 20GB available
- ✅ No critical errors in logs
- ✅ Uptime > 99.9%

---

**Deployment Date:** [Date]
**Deployed By:** [Name]
**Approved By:** [Name]
**Notes:** [Any special notes]
