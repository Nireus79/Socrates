# Docker Test Plan - Socrates Reverse Proxy Setup

## ⚠️ QUICK START AFTER SYSTEM RESTART

Run this in WSL 2 Ubuntu terminal:

```bash
cd /mnt/c/Users/themi/PycharmProjects/Socrates
docker compose build --no-cache && docker compose up -d && docker compose ps
```

The REDIS_URL fix is already applied to docker-compose.yml. This command will rebuild images and start all services.

---

## Documentation Reference
  - REVERSE_PROXY_SETUP.md - Production deployment guide
  - VALIDATION_REPORT.md - Configuration validation
  - DOCKER_TEST_PLAN.md - Testing procedures (this file)
  - TEST_SUITE.sh - Automated test script
  - TESTING_SUMMARY.md - Complete status report

## Current Status

### Static Validation: PASSED (8/8 checks)
- [PASS] docker-compose.yml is valid YAML
- [PASS] Frontend builder stage configured
- [PASS] VITE_API_URL set to /api
- [PASS] nginx reverse proxy stage present
- [PASS] nginx config properly copied
- [PASS] Frontend dist files copied
- [PASS] Upstream api_backend defined
- [PASS] API proxy location /api/ configured
- [PASS] Rewrite rule configured
- [PASS] Health check endpoint defined
- [PASS] Frontend SPA routing configured
- [PASS] CORS headers configured
- [PASS] Security headers configured
- [PASS] Gzip compression enabled

## Docker Installation Status - UPDATED

### Current State (After System Restart):
Native Docker installed in WSL 2 Ubuntu (Docker Desktop was broken and abandoned).

### CRITICAL FIX APPLIED:
✓ **REDIS_URL environment variable added to docker-compose.yml**
  - Location: Line 16 in docker-compose.yml
  - Value: `REDIS_URL: redis://redis:6379`
  - This fixes the API container failing to connect to Redis
  - The API was trying `localhost:6379` (wrong for Docker network) instead of `redis:6379` (service name)

### Known Issue Before Restart:
- Docker daemon became unresponsive after multiple restarts and attempts
- Commands would hang indefinitely or fail with permission errors
- System restart should clear this issue

### Next Steps After System Restart:
1. Open WSL 2 Ubuntu terminal
2. Run the complete rebuild and startup sequence:

```bash
cd /mnt/c/Users/themi/PycharmProjects/Socrates

# Build fresh images with the REDIS_URL fix
docker compose build --no-cache

# Start all services
docker compose up -d

# Verify status
docker compose ps
```

3. If docker commands still hang after restart:
   - Completely reinstall Docker in WSL:
   ```bash
   sudo systemctl stop docker 2>/dev/null || true
   sudo apt-get remove -y docker docker.io 2>/dev/null || true
   sudo rm -rf /var/lib/docker 2>/dev/null || true
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   newgrp docker
   docker ps  # Test it works
   ```
   - Then proceed with build and startup above

## Runtime Test Plan

### Phase 1: Build Images (5-10 minutes)
```bash
cd C:\Users\themi\PycharmProjects\Socrates
docker-compose build
```

Expected output:
- Building socrates-api image
- Building frontend image
- Building nginx reverse proxy image
- No build errors

### Phase 2: Start Services (2-3 minutes)
```bash
docker-compose up -d
```

Verify all services are running:
```bash
docker-compose ps
```

Expected output:
```
NAME              STATUS
socrates-api      Up (healthy)
socrates-redis    Up (healthy)
socrates-web      Up (healthy)
```

### Phase 3: Health Checks (30 seconds)
```bash
# Check reverse proxy health
curl http://localhost/health

# Check API health through proxy
curl http://localhost/api/health

# Check all service logs
docker-compose logs
```

### Phase 4: Frontend Test (1-2 minutes)
1. Open http://localhost in browser
2. Verify page loads without errors
3. Open browser DevTools (F12)
4. Check Console tab for any errors
5. Expected: No CORS errors, no 404 errors

### Phase 5: API Endpoint Tests (2-3 minutes)

Test API-key endpoint:
```bash
curl -X POST http://localhost/api/llm/api-key \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","api_key":"test-key"}'
```

Test search endpoint:
```bash
curl -X GET "http://localhost/api/search?q=test"
```

Test CORS headers:
```bash
curl -i -H "Origin: http://localhost" http://localhost/api/health
```

Expected: `Access-Control-Allow-Origin: http://localhost` in response headers

### Phase 6: CORS Verification (1-2 minutes)

Test preflight request:
```bash
curl -X OPTIONS http://localhost/api/health \
  -H "Origin: http://localhost" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

Expected: HTTP 204 or 200 response with CORS headers

### Phase 7: Automated Tests (2-3 minutes)
```bash
bash TEST_SUITE.sh
```

This runs comprehensive tests including:
- Service health checks
- Network connectivity
- Frontend loading
- API endpoint accessibility
- CORS header verification
- Reverse proxy routing
- Log validation

## Troubleshooting Guide

### Docker Installation Stuck
- Docker Desktop installation can take 10-30 minutes
- May require system restart after installation
- Check Windows Event Viewer for installation errors
- Verify you have admin privileges

### Services Not Starting
```bash
# Check logs for specific errors
docker-compose logs api
docker-compose logs web
docker-compose logs redis

# Try rebuilding images
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Frontend Shows Blank Page
- Check browser console for errors
- Verify nginx is running: `docker-compose ps web`
- Check nginx logs: `docker-compose logs web`
- Verify frontend was built: `docker-compose logs web | grep "built"`

### API Returns 502 Bad Gateway
- Check if API service is running: `docker-compose ps api`
- Check API logs: `docker-compose logs api`
- Verify API is listening on 0.0.0.0:8000
- Check network connectivity: `docker network inspect socrates_socrates-network`

### CORS Errors in Browser Console
- Verify reverse proxy is running: `docker-compose ps web`
- Check that CORS headers are present: `curl -i http://localhost/api/health | grep "Access-Control"`
- Verify nginx config was deployed: `docker-compose logs web`

### Redis Connection Errors
- Verify redis is running: `docker-compose ps redis`
- Check redis logs: `docker-compose logs redis`
- Verify API can reach redis: `docker exec socrates-api redis-cli -h redis ping`

## Success Criteria

All of the following must be true for successful deployment:

- [x] Static validation: All 8 configuration checks pass
- [ ] Docker installation completes successfully
- [ ] All three services (api, redis, web) are running and healthy
- [ ] Frontend loads at http://localhost without errors
- [ ] API health endpoint responds at http://localhost/api/health
- [ ] CORS headers are present on /api/* responses
- [ ] Frontend can make API calls through reverse proxy
- [ ] No browser console errors
- [ ] TEST_SUITE.sh passes all tests

## Timeline Estimate

- Docker Installation: 10-30 minutes (may require restart)
- Building Images: 5-10 minutes
- Starting Services: 2-3 minutes
- Running All Tests: 10-15 minutes

**Total: 30-60 minutes from start to completion**

## Next Steps After Successful Testing

1. Push test results to repository
2. Document any issues found
3. Update deployment documentation if needed
4. Prepare for production deployment

## Important Notes

- VITE_API_URL is set to `/api` during frontend build - this tells the frontend to use relative paths
- nginx reverse proxy rewrites `/api/*` requests to the backend
- All services communicate over Docker's internal `socrates-network`
- Encryption keys are properly configured in .env files
- SOCRATES_API_HOST is set to 0.0.0.0 for Docker networking (not 127.0.0.1)

## References

- REVERSE_PROXY_SETUP.md - Detailed setup documentation
- VALIDATION_REPORT.md - Configuration validation details
- TEST_SUITE.sh - Automated test script
- docker-compose.yml - Service orchestration
