# Reverse Proxy Setup - Docker Deployment

This guide explains the production-ready reverse proxy setup that combines the frontend and API under a single origin, eliminating CORS issues.

## Architecture

The setup consists of three main components:

```
┌─────────────────────────────────────────────────┐
│         Reverse Proxy (nginx) - Port 80          │
│  ┌──────────────────┐  ┌───────────────────┐   │
│  │  Frontend (SPA)  │  │  API Proxy Routes │   │
│  │  Served at /     │  │  Proxied at /api/ │   │
│  └──────────────────┘  └───────────────────┘   │
└──────────────────────────────────┬──────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
        ┌───────▼────────┐                  ┌─────────▼────────┐
        │  API Backend   │                  │  Redis Cache     │
        │  Port 8000     │                  │  Port 6379       │
        └────────────────┘                  └──────────────────┘
```

## Files

- `Dockerfile.reverse-proxy` - Multi-stage build for reverse proxy + frontend
- `docker-compose.yml` - Orchestration configuration
- `nginx-reverse-proxy.conf` - nginx configuration for routing
- `socrates-api/src/socrates_api/main.py` - API (modified to support 0.0.0.0)
- `socrates-frontend/src/api/client.ts` - Frontend API client (supports /api prefix)

## Building and Running

### Prerequisites

- Docker and Docker Compose installed
- `.env` file with `SOCRATES_ENCRYPTION_KEY` set (see SECURITY_SETUP.md)

### Start Services

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Accessing the Application

- **Frontend**: http://localhost
- **API**: http://localhost/api
- **Health Check**: http://localhost/health

## Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
api:
  environment:
    SOCRATES_API_HOST: 0.0.0.0      # Required for Docker networking
    SOCRATES_API_PORT: 8000         # API port (internal)
    ENVIRONMENT: production         # production, staging, development
    SOCRATES_ENCRYPTION_KEY: ...    # Required - set from .env file
```

### Encryption Key Setup

1. **Generate key** (if not already done):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Create .env file** in project root:
   ```
   SOCRATES_ENCRYPTION_KEY=your-generated-key-here
   ```

3. **Docker Compose** will mount this file into the API container

### Frontend API Configuration

The frontend uses this priority:
1. **With Reverse Proxy**: Uses `/api/` prefix (set in Dockerfile.reverse-proxy build)
2. **Environment Variable**: VITE_API_URL (if set during build)
3. **Auto-discovery**: Tries common ports (8000, 8008, etc.)
4. **Fallback**: http://localhost:8000

## How It Works

### Request Flow

1. **Frontend Requests**:
   ```
   GET /search?q=test
   → Served by nginx (SPA routing)

   POST /api/llm/api-key
   → nginx rewrites to /llm/api-key
   → Proxies to http://api:8000/llm/api-key
   ```

2. **CORS Handling**:
   - All requests are same-origin (localhost)
   - Reverse proxy adds CORS headers anyway (for safety)
   - No browser CORS errors

3. **Static Assets**:
   - Cached for 1 year with immutable headers
   - SPA files cached with no-cache headers
   - Gzip compression enabled

## DNS and Domains

For production with custom domain (e.g., `app.example.com`):

1. **Update nginx config** (add to `nginx-reverse-proxy.conf`):
   ```nginx
   server_name app.example.com;
   ```

2. **Enable HTTPS**:
   - Use Certbot/Let's Encrypt for SSL
   - Or use cloud provider's certificate service

3. **Update API origin** (in docker-compose.yml):
   ```yaml
   environment:
     ALLOWED_ORIGINS: "https://app.example.com"
   ```

## Troubleshooting

### API not reachable from reverse proxy

**Symptom**: `502 Bad Gateway` errors

**Solution**:
- Ensure API container is running: `docker-compose ps`
- Check API logs: `docker-compose logs api`
- Verify SOCRATES_API_HOST is set to `0.0.0.0` (not 127.0.0.1)
- Ensure network is connected: `docker network inspect socrates_socrates-network`

### Frontend loads but API calls fail

**Symptom**: Network errors in browser console

**Solution**:
- Check browser console for specific errors
- Ensure frontend is using `/api/` prefix paths
- Verify VITE_API_URL is set to `/api` in build
- Check nginx proxy logs: `docker-compose logs web`

### Encryption key not recognized

**Symptom**: `500 Internal Server Error` on API calls

**Solution**:
- Verify SOCRATES_ENCRYPTION_KEY is set in .env file
- Ensure .env file is in project root
- Restart API service: `docker-compose restart api`

### Port already in use

**Symptom**: `bind: address already in use`

**Solution**:
- Change port in docker-compose.yml: `ports: ["8080:80"]`
- Or stop other services using the port
- Or use: `docker-compose up -d --remove-orphans`

## Performance Considerations

### Caching Strategy

- **Frontend files**: 1 year (immutable assets) or no-cache (HTML)
- **API responses**: Determined by API headers (not cached by nginx)
- **Gzip**: Enabled for text, JSON, JavaScript

### Timeouts

- **Connection timeout**: 60s
- **Read timeout**: 60s
- **Max body size**: 100M (file uploads)

## Security Notes

- ✅ CORS headers properly configured
- ✅ Security headers applied (X-Frame-Options, X-Content-Type-Options, etc.)
- ✅ Hidden files denied (.env, .git, etc.)
- ✅ Strict HTTPS recommended for production
- ⚠️ Encryption key must be kept secret
- ⚠️ Environment variable sensitive in docker-compose.yml

## Production Checklist

- [ ] Set `SOCRATES_ENCRYPTION_KEY` in .env file
- [ ] Set `ENVIRONMENT=production` in docker-compose.yml
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Set up HTTPS with valid certificate
- [ ] Configure proper DNS records
- [ ] Set resource limits in docker-compose.yml
- [ ] Configure Redis persistence
- [ ] Set up log rotation
- [ ] Test health endpoints
- [ ] Test API authentication flow
- [ ] Test file uploads (if applicable)
- [ ] Monitor container resource usage
- [ ] Set up automated backups

## Development vs Production

### Development (Current Setup)

```bash
# Terminal 1: API
cd socrates-api
python -m socrates_api.main

# Terminal 2: Frontend
cd socrates-frontend
npm run dev
```

### Production (Docker)

```bash
docker-compose up -d
```

## Updating Configuration

After editing docker-compose.yml or nginx-reverse-proxy.conf:

```bash
# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Or just restart specific service
docker-compose restart web    # Restart reverse proxy
docker-compose restart api    # Restart API
```

## Next Steps

1. ✅ Create .env file with encryption key
2. ✅ Build images: `docker-compose build`
3. ✅ Start services: `docker-compose up -d`
4. ✅ Test health: `curl http://localhost/health`
5. ✅ Access frontend: Open http://localhost in browser
6. ✅ Monitor logs: `docker-compose logs -f`

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [nginx Documentation](https://nginx.org/en/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
