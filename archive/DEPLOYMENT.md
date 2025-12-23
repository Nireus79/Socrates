# Socrates AI - Production Deployment Guide

## Overview

Socrates is a full-stack application with:
- **Backend**: FastAPI (Python) with PostgreSQL
- **Frontend**: React + Vite (TypeScript)
- **Real-time**: WebSocket for chat and events
- **Database**: PostgreSQL + ChromaDB + Redis

This guide covers deployment to production platforms.

---

## Architecture

```
┌─────────────────┐
│  Vercel         │ (React Frontend)
│ socrates.app    │
└────────┬────────┘
         │
         │ HTTPS
         │
┌────────▼────────────────┐
│  Nginx (Reverse Proxy)  │
│  Load Balancer          │
└────────┬────────────────┘
         │
    ┌────┴──────────┬──────────────┐
    │               │              │
┌───▼──┐     ┌──────▼──┐     ┌────▼──┐
│ API  │     │ Database │     │ Cache │
│FastAPI     │PostgreSQL    │ Redis │
│Railway     │Supabase      │Upstash
└──────┘     └───────────┘     └───────┘
```

---

## Frontend Deployment (Vercel)

### Prerequisites
- Vercel account
- GitHub repository

### Steps

1. **Connect Repository**
   ```bash
   # Push code to GitHub
   git push origin main
   ```

2. **Create Vercel Project**
   - Visit https://vercel.com/dashboard
   - Click "Add New..." → "Project"
   - Import your GitHub repository
   - Select `socrates-frontend` as root directory

3. **Configure Environment Variables**
   In Vercel Dashboard → Settings → Environment Variables:
   ```
   VITE_API_URL=https://api.socrates.app
   VITE_ENABLE_ANALYTICS=true
   VITE_ENABLE_WEBSOCKET=true
   ```

4. **Build Configuration**
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm ci`

5. **Deploy**
   - Vercel automatically deploys on push to main
   - Monitor deployment in dashboard

### Optimization

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_URL": "@vercel/api-url"
  }
}
```

---

## Backend Deployment (Railway)

### Prerequisites
- Railway account
- GitHub repository
- PostgreSQL database (Supabase or Railway)
- Redis (Upstash or Railway)
- ChromaDB instance

### Steps

1. **Create Railway Project**
   - Visit https://railway.app
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository

2. **Add Services**
   ```bash
   # Add PostgreSQL
   railway add postgresql

   # Add Redis
   railway add redis
   ```

3. **Configure Environment Variables**
   In Railway → Project → Variables:
   ```
   ANTHROPIC_API_KEY=sk-...
   DATABASE_URL=postgresql://user:pass@host:5432/db
   REDIS_URL=redis://host:6379/0
   CHROMADB_URL=http://chromadb.example.com
   SOCRATES_API_HOST=0.0.0.0
   SOCRATES_API_PORT=8000
   ```

4. **Deploy**
   ```bash
   # Push to GitHub
   git push origin main

   # Railway auto-deploys
   ```

5. **Configure Domain**
   - Railway → Project → Settings → Domain
   - Add custom domain: `api.socrates.app`
   - Configure DNS records

### Health Check
```bash
curl https://api.socrates.app/health
```

---

## Database Setup (Supabase)

### Prerequisites
- Supabase account

### Steps

1. **Create Project**
   - Visit https://supabase.com
   - Create new project
   - Note connection string

2. **Initialize Schema**
   ```bash
   psql -U postgres -h db.xxx.supabase.co -f schema.sql
   ```

3. **Connection String**
   ```
   postgresql://user:password@db.xxx.supabase.co:5432/postgres
   ```

4. **Backups**
   - Supabase: Automated daily backups
   - Retention: 7 days (paid: 30 days)

---

## Cache Setup (Upstash)

### Prerequisites
- Upstash account

### Steps

1. **Create Redis Database**
   - Visit https://upstash.com
   - Create new Redis database
   - Select region close to API server

2. **Configuration**
   ```
   REDIS_URL=redis://default:password@host:port
   ```

3. **Monitoring**
   - CPU: < 50%
   - Memory: < 80%
   - Commands/sec: Monitor for spikes

---

## Local Development

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Direct Installation

```bash
# Backend
cd socrates-api
pip install -r requirements.txt
python -m uvicorn main:app --reload

# Frontend
cd socrates-frontend
npm install
npm run dev
```

---

## Monitoring & Logging

### Application Monitoring
- **Sentry**: Error tracking
- **New Relic**: Performance monitoring
- **Datadog**: Infrastructure monitoring

### Setup Sentry
```python
# main.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    traces_sample_rate=0.1,
    environment="production"
)
```

### Logs
- Railway: View in dashboard
- Vercel: Deployment logs
- PostgreSQL: Error logs via Supabase dashboard

---

## SSL/TLS & HTTPS

### Automatic (Recommended)
- **Vercel**: Automatic with `*.vercel.app`
- **Railway**: Auto with Railway domains
- **Custom Domain**: Use Let's Encrypt (free)

### Custom Domain SSL
```bash
# Railway handles SSL automatically for custom domains
# Just add domain in Settings → Domain
```

---

## Performance Optimization

### Frontend (Vercel)
- Automatic image optimization
- Code splitting by route
- Cache static assets (1 year)
- CDN edge caching

### Backend (Railway)
- Connection pooling (10-20 connections)
- Redis caching (1 hour TTL)
- Query optimization
- Compression (gzip)

### Monitoring Performance
```bash
# Lighthouse score
vercel telemetry
```

---

## Security Checklist

- ✅ HTTPS/TLS enabled
- ✅ CORS configured (frontend only)
- ✅ Rate limiting (auth: 5/min, API: 10/sec)
- ✅ CSRF protection
- ✅ JWT tokens (15 min access, 7 day refresh)
- ✅ Password hashing (bcrypt)
- ✅ SQL injection protection (parameterized)
- ✅ XSS protection (DOMPurify)
- ✅ Security headers (CSP, X-Frame-Options, etc.)
- ✅ Database backups (daily)
- ✅ Secrets in environment variables
- ✅ Network isolation (private database)

---

## Scaling

### Horizontal Scaling
- **Multiple API instances**: Railway auto-scales
- **Load balancer**: Use Nginx or Railway
- **Database**: Use Supabase pro tier for auto-scaling

### Vertical Scaling
- **More CPU/RAM**: Railway → Settings → Compute
- **Larger database**: Supabase → Upgrade plan

### Caching Strategy
- **User data**: 1 hour Redis
- **Project metadata**: 30 minutes
- **Chat history**: 5 minutes
- **Static assets**: 1 year CDN

---

## Cost Estimation (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Pro | $20 |
| Railway | Starter | $5 |
| Supabase | Pro | $25 |
| Upstash | Free | $0 |
| **Total** | | **$50** |

---

## Disaster Recovery

### Backup Strategy
- **Database**: Daily automated (7-day retention)
- **Code**: GitHub version control
- **Secrets**: Environment variables in `.env` (not committed)

### Recovery Steps
1. Restore database from Supabase
2. Redeploy from GitHub
3. Verify health checks
4. Run smoke tests

---

## Support & Troubleshooting

### Common Issues

**API Timeout**
- Check Railway logs: `railway logs`
- Increase proxy timeout in Nginx
- Check database connection pool

**WebSocket Connection Failed**
- Verify Nginx WebSocket config
- Check CORS headers
- Ensure Railway domain is accessible

**Database Connection Error**
- Verify connection string
- Check Supabase IP whitelist (none = public)
- Confirm credentials

### Resources
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

---

## Next Steps

1. Set up monitoring with Sentry
2. Configure CI/CD pipeline (GitHub Actions)
3. Implement automated testing
4. Set up staging environment
5. Plan disaster recovery drills
