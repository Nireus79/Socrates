# Socratic RAG Enhanced - Deployment Guide

**Version:** 7.4.0
**Last Updated:** October 2024
**Audience:** DevOps & System Administrators

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [Security Setup](#security-setup)
8. [Monitoring & Logging](#monitoring--logging)
9. [Scaling & Performance](#scaling--performance)
10. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Python:** 3.8 or higher
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 10GB minimum (with vector database)
- **CPU:** 2 cores minimum

### Recommended Production Requirements
- **Python:** 3.10 or higher
- **RAM:** 8GB or more
- **Storage:** 50GB+ (SSD recommended)
- **CPU:** 4+ cores
- **OS:** Linux (Ubuntu 20.04 LTS+) or macOS

### Required External Services
- **Anthropic API Key** - For Claude AI
- **Git** - For repository operations
- **PostgreSQL 12+** - For production database (SQLite for dev)

### Optional Services
- **Redis** - For caching and sessions
- **Docker** - For containerized deployment
- **Nginx** - For reverse proxy
- **Certbot** - For SSL/TLS certificates

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/socrates.git
cd socrates
```

### 2. Create Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-this

# Database
SOCRATIC_DB_PATH=./data/socratic.db
SOCRATIC_DATA_PATH=./data

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # Optional

# Application
APP_PORT=5000
APP_HOST=127.0.0.1
CORS_ORIGINS=http://localhost:3000

# Vector Database
CHROMA_PATH=./data/vector_db
```

### 5. Initialize Database
```bash
python -c "from src.database import init_database; init_database()"
```

### 6. Run Application
```bash
python run.py
```

**Output:**
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Visit: `http://localhost:5000`

### 7. Default Credentials
- **Email:** admin@example.com
- **Password:** admin123
- ⚠️ Change these immediately in production!

---

## Docker Deployment

### 1. Build Docker Image
```bash
docker build -t socratic-rag:7.4.0 .
```

### 2. Create Docker Compose File
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  socratic-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - DATABASE_URL=postgresql://user:password@db:5432/socratic
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=socratic
      - POSTGRES_USER=socratic_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U socratic_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### 3. Deploy with Docker Compose
```bash
# Create environment file
cp .env.example .env.production
# Edit with production values

# Start services
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f socratic-app
```

### 4. Docker Commands
```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View specific service logs
docker-compose logs -f db

# Execute command in container
docker-compose exec socratic-app python -c "from src.database import init_database; init_database()"
```

---

## Cloud Deployment

### AWS Deployment

#### 1. Prepare EC2 Instance
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application user
sudo useradd -m -s /bin/bash socratic
sudo usermod -aG docker socratic
```

#### 2. Deploy Application
```bash
# Clone repository
sudo -u socratic git clone https://github.com/your-org/socrates.git /opt/socrates
cd /opt/socrates

# Setup environment
sudo -u socratic cp .env.example .env.production
# Edit environment with production values

# Start services
sudo -u socratic docker-compose -f docker-compose.yml up -d
```

#### 3. Setup RDS Database (Optional)
```yaml
# In docker-compose.yml, replace local PostgreSQL with RDS
services:
  socratic-app:
    environment:
      - DATABASE_URL=postgresql://user:password@socratic-db.xxxxx.rds.amazonaws.com:5432/socratic
    # Remove db service dependency if using RDS
```

#### 4. Configure Auto-Scaling (Optional)
- Create AMI from configured instance
- Setup Auto Scaling Group
- Configure load balancer (ALB)
- Setup CloudWatch monitoring

### Heroku Deployment

#### 1. Setup Heroku CLI
```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

#### 2. Create Heroku App
```bash
heroku create socratic-rag-app --region us-east-1
```

#### 3. Add Buildpacks
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add --index 1 heroku/apt
```

#### 4. Configure Environment
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku addons:create heroku-postgresql:standard-0
heroku addons:create heroku-redis:premium-0
```

#### 5. Deploy
```bash
git push heroku main
heroku logs -t
```

### Google Cloud Deployment

#### 1. Setup Google Cloud CLI
```bash
curl https://sdk.cloud.google.com | bash
gcloud init
gcloud auth application-default login
```

#### 2. Deploy to Cloud Run
```bash
gcloud run deploy socratic-rag \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars=ANTHROPIC_API_KEY=sk-ant-... \
  --memory=2Gi \
  --cpu=2 \
  --timeout=3600
```

#### 3. Setup Cloud SQL
```bash
# Create instance
gcloud sql instances create socratic-db \
  --database-version=POSTGRES_14 \
  --tier=db-custom-2-8192 \
  --region=us-central1

# Create database
gcloud sql databases create socratic --instance=socratic-db

# Update connection string
DATABASE_URL=postgresql://user:password@/socratic?host=/cloudsql/project:us-central1:socratic-db
```

---

## Configuration

### Environment Variables

#### Critical Settings
```env
# Flask Configuration
FLASK_ENV=production              # development or production
SECRET_KEY=your-very-secret-key   # Change this!
FLASK_DEBUG=False                 # Never True in production

# Database Configuration
DATABASE_URL=postgresql://...     # Connection string
SOCRATIC_DB_PATH=/app/data/socratic.db

# API Keys (Required)
ANTHROPIC_API_KEY=sk-ant-...     # Claude API
OPENAI_API_KEY=sk-...             # Optional OpenAI

# Application Settings
APP_PORT=5000
APP_HOST=0.0.0.0
MAX_CONTENT_LENGTH=104857600      # 100MB file upload limit

# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FILE=/app/logs/socratic.log

# Security
SESSION_COOKIE_SECURE=True        # HTTPS only
SESSION_COOKIE_HTTPONLY=True      # No JavaScript access
CORS_ORIGINS=https://your-domain.com

# Vector Database
CHROMA_PERSIST_DIRECTORY=/app/data/vector_db
```

#### Optional Settings
```env
# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Rate Limiting
RATELIMIT_REQUESTS=50
RATELIMIT_PERIOD=3600

# Backup
BACKUP_ENABLED=True
BACKUP_SCHEDULE=0 2 * * *  # 2 AM daily
```

### Configuration File

Edit `config.yaml`:
```yaml
# Application
app:
  name: "Socratic RAG Enhanced"
  version: "7.4.0"
  debug: false
  host: "0.0.0.0"
  port: 5000

# Database
database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  name: "socratic"
  pool_size: 10

# Vector Database
vector_db:
  type: "chromadb"
  path: "/app/data/vector_db"
  persist: true

# Logging
logging:
  level: "INFO"
  format: "json"
  file: "/app/logs/socratic.log"
  max_size: 104857600  # 100MB
  backup_count: 5

# Security
security:
  cors_origins:
    - "https://your-domain.com"
  rate_limit:
    requests: 50
    period: 3600
  session_timeout: 3600

# External Services
services:
  claude:
    enabled: true
    rate_limit: 50
  vector_search:
    top_k: 5
```

---

## Database Setup

### PostgreSQL Setup (Production)

#### 1. Install PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Or use Docker
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=secure-password \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:14-alpine
```

#### 2. Create Database & User
```bash
sudo -u postgres psql

postgres=# CREATE USER socratic_user WITH PASSWORD 'secure-password';
postgres=# CREATE DATABASE socratic OWNER socratic_user;
postgres=# GRANT ALL PRIVILEGES ON DATABASE socratic TO socratic_user;
postgres=# \q
```

#### 3. Migrate from SQLite
```bash
# Backup SQLite database
cp data/socratic.db data/socratic.db.backup

# Run migration script
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path data/socratic.db \
  --postgresql-url postgresql://socratic_user:password@localhost/socratic
```

#### 4. Initialize Schema
```bash
python -c "from src.database import init_database; init_database()"
```

### Backup Strategy

#### Automated Backups
```bash
# Add to crontab
0 2 * * * /opt/socrates/scripts/backup.sh

# Backup script content
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/socratic"
mkdir -p $BACKUP_DIR

# Database backup
pg_dump postgresql://user:pass@localhost/socratic > $BACKUP_DIR/db_$DATE.sql

# Application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /app/data/

# Upload to S3 or Cloud Storage
aws s3 cp $BACKUP_DIR s3://your-backup-bucket/socratic/ --recursive
```

#### Restore from Backup
```bash
# Restore database
psql postgresql://user:pass@localhost/socratic < backup_db.sql

# Restore application data
tar -xzf backup_app_data.tar.gz -C /app/
```

---

## Security Setup

### SSL/TLS Configuration

#### Using Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d your-domain.com

# Setup auto-renewal
sudo systemctl enable certbot.timer
```

#### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
}
```

### Firewall Configuration

```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny all
sudo ufw enable
```

### Database Security
```sql
-- Restrict user permissions
REVOKE ALL ON DATABASE socratic FROM PUBLIC;
GRANT CONNECT ON DATABASE socratic TO socratic_user;
GRANT USAGE ON SCHEMA public TO socratic_user;

-- Create read-only user
CREATE USER socratic_readonly WITH PASSWORD 'readonly-password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO socratic_readonly;
```

---

## Monitoring & Logging

### Logging Configuration

#### Structured Logging
```python
# in config.yaml or .env
LOG_FORMAT=json
LOG_LEVEL=INFO
LOG_FILE=/var/log/socratic/app.log
```

#### Log Rotation
```bash
# /etc/logrotate.d/socratic
/var/log/socratic/app.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0600 socratic socratic
    sharedscripts
    postrotate
        systemctl reload socratic > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Setup

#### Health Checks
```bash
# Check application health
curl http://localhost:5000/api/health

# Response
{
  "status": "healthy",
  "system_available": true,
  "app_version": "7.4.0"
}
```

#### Prometheus Metrics
```bash
# Scrape metrics
curl http://localhost:5000/metrics
```

#### Uptime Monitoring
- Configure external uptime monitoring (UptimeRobot, Pingdom, etc.)
- Monitor key endpoints
- Set up alerts for downtime

### Error Tracking

#### Sentry Integration (Optional)
```bash
# Install Sentry
pip install sentry-sdk

# Configure in app
import sentry_sdk
sentry_sdk.init(
    dsn="https://your-sentry-dsn@o0000.ingest.sentry.io/000000",
    traces_sample_rate=1.0,
    environment="production"
)
```

---

## Scaling & Performance

### Horizontal Scaling

#### Load Balancer Setup
```nginx
upstream socratic_backend {
    least_conn;
    server socratic1:5000;
    server socratic2:5000;
    server socratic3:5000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://socratic_backend;
        proxy_set_header Host $host;
        proxy_buffering off;
    }
}
```

#### Kubernetes Deployment (Optional)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: socratic-rag
spec:
  replicas: 3
  selector:
    matchLabels:
      app: socratic-rag
  template:
    metadata:
      labels:
        app: socratic-rag
    spec:
      containers:
      - name: socratic-rag
        image: socratic-rag:7.4.0
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: socratic-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Performance Optimization

#### Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_generations_project ON generations(project_id);
CREATE INDEX idx_vector_chunks_collection ON vector_chunks(collection_name);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM projects WHERE owner_id = 'user_123';
```

#### Caching Strategy
```env
# Redis caching
REDIS_URL=redis://localhost:6379
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=300
```

#### Connection Pooling
```env
DATABASE_POOL_SIZE=20
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_PRE_PING=True
```

---

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check logs
docker-compose logs socratic-app

# Common causes
# 1. Port already in use
sudo lsof -i :5000

# 2. Database connection failed
docker-compose logs db

# 3. Missing environment variables
echo $ANTHROPIC_API_KEY
```

#### High Memory Usage
```bash
# Check memory consumption
top -o %MEM

# Reduce pool size in config
DATABASE_POOL_SIZE=5

# Restart application
docker-compose restart socratic-app
```

#### Database Connection Errors
```bash
# Test database connection
python -c "from src.database import get_database; db = get_database(); print('OK')"

# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database
python -c "from src.database import reset_database, init_database; reset_database(); init_database()"
```

---

## Support & Documentation

- Documentation: `/docs` directory
- GitHub: https://github.com/your-org/socrates
- Issues: https://github.com/your-org/socrates/issues
- Discussions: https://github.com/your-org/socrates/discussions

For more information, see:
- User Guide: `docs/USER_GUIDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- API Documentation: `docs/API_DOCUMENTATION.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
