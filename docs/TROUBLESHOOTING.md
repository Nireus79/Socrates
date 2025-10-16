# Socratic RAG Enhanced - Troubleshooting & FAQ

**Version:** 7.4.0
**Last Updated:** October 2024
**Purpose:** Common issues, solutions, and frequently asked questions

## Table of Contents

1. [General Troubleshooting](#general-troubleshooting)
2. [Installation Issues](#installation-issues)
3. [Application Issues](#application-issues)
4. [Code Generation Issues](#code-generation-issues)
5. [Repository Management Issues](#repository-management-issues)
6. [Performance Issues](#performance-issues)
7. [Security & Access Issues](#security--access-issues)
8. [Database Issues](#database-issues)
9. [FAQ](#faq)
10. [Getting Help](#getting-help)

---

## General Troubleshooting

### "Page Blank / Application Not Responding"

**Symptoms:** Application loads but displays blank page or spinner indefinitely

**Solutions:**
1. **Check browser console** (F12 → Console tab)
   - Look for JavaScript errors
   - Check network tab for failed requests

2. **Clear browser cache**
   ```bash
   # Or manually:
   # Chrome: Settings → Privacy → Clear browsing data
   # Firefox: Settings → Privacy → Clear All
   ```

3. **Check application logs**
   ```bash
   # Local development
   tail -f logs/socratic.log

   # Docker
   docker-compose logs -f socratic-app
   ```

4. **Verify server is running**
   ```bash
   curl http://localhost:5000/api/health
   ```

5. **Restart application**
   ```bash
   # Local
   pkill -f run.py && python run.py

   # Docker
   docker-compose restart socratic-app
   ```

### "Error 500 - Internal Server Error"

**Symptoms:** Red error message or 500 status code

**Root Causes:**
- Database connection failed
- Missing API key
- Unhandled exception in code
- Service is down

**Solutions:**
1. **Check application logs**
   ```bash
   docker-compose logs socratic-app 2>&1 | tail -50
   ```

2. **Verify environment variables**
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $DATABASE_URL
   ```

3. **Test database connection**
   ```bash
   python -c "from src.database import get_database; db = get_database(); print('OK')"
   ```

4. **Check service status**
   ```bash
   docker-compose ps
   ```

5. **Restart all services**
   ```bash
   docker-compose down && docker-compose up -d
   ```

---

## Installation Issues

### "Python Version Mismatch"

**Error:** `ModuleNotFoundError` or compatibility errors

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Use specific version
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### "Package Installation Fails"

**Symptoms:** `pip install` fails with permissions or network errors

**Solutions:**
```bash
# Method 1: Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Method 2: Install as user
pip install --user -r requirements.txt

# Method 3: Check pip cache
pip cache purge
pip install -r requirements.txt

# Method 4: Use alternative index
pip install -i https://pypi.org/simple/ -r requirements.txt
```

### "Git Clone Fails"

**Error:** `fatal: unable to access repository`

**Solutions:**
```bash
# Check internet connection
ping github.com

# Verify SSH keys
ssh -T git@github.com

# Use HTTPS instead
git clone https://github.com/your-org/socrates.git

# Specify credentials
git clone https://username:token@github.com/your-org/socrates.git
```

---

## Application Issues

### "Cannot Log In"

**Symptoms:** Login fails with "Invalid credentials" or hangs

**Possible Causes:**
- Wrong username/password
- Database not initialized
- Session error

**Solutions:**
1. **Verify credentials**
   - Default: admin@example.com / admin123
   - Check `.env` for database path

2. **Check database**
   ```bash
   python -c "from src.database import init_database; init_database()"
   ```

3. **Clear sessions**
   ```bash
   # Docker
   docker-compose exec socratic-app rm -rf /app/data/sessions

   # Local
   rm -rf data/sessions
   ```

4. **Reset admin account**
   ```python
   from src.database import get_database
   db = get_database()
   db.users.update('admin_user_id', {'password_hash': 'reset_hash'})
   ```

### "Session Keeps Getting Paused"

**Symptoms:** Session pauses mid-conversation without user action

**Causes:**
- Server timeout (default 30 minutes)
- Network interrupted
- Session limit exceeded

**Solutions:**
1. **Check session timeout**
   - Edit `config.yaml`: `session_timeout: 3600`  (1 hour)

2. **Increase timeout**
   ```env
   SESSION_PERMANENT=True
   PERMANENT_SESSION_LIFETIME=7200  # 2 hours
   ```

3. **Check network**
   - Verify stable internet connection
   - Check firewall rules

4. **Resume session**
   - Go back to session and continue
   - Previous context preserved

### "Profile Picture Upload Fails"

**Error:** "File too large" or upload timeout

**Solutions:**
```env
# Increase upload limit
MAX_CONTENT_LENGTH=104857600  # 100MB

# Or in Flask config
UPLOAD_FOLDER=/tmp/uploads
MAX_FILE_SIZE=104857600
```

---

## Code Generation Issues

### "Code Generation Times Out"

**Symptoms:** "Generating..." spinner for >3 minutes, then error

**Causes:**
- Claude API is slow
- Large specification
- Network connectivity issue
- Rate limiting

**Solutions:**
1. **Check API status**
   - Visit https://status.openai.com/ (if using OpenAI)
   - Visit https://www.anthropic.com/status (for Anthropic)

2. **Reduce scope**
   - Generate specific component instead of full project
   - Disable optional features (tests, Docker, etc.)

3. **Increase timeout**
   ```env
   REQUEST_TIMEOUT=300  # 5 minutes
   ```

4. **Use fallback generation**
   - System provides template code if generation fails
   - Review and customize provided template

### "Generated Code Has Syntax Errors"

**Symptoms:** Generated code doesn't compile/run

**Causes:**
- Generated code is template-based
- Missing dependencies
- Language version mismatch

**Solutions:**
1. **Install dependencies**
   ```bash
   # Python
   pip install -r requirements.txt

   # JavaScript
   npm install

   # Java
   gradle build
   ```

2. **Check language version**
   ```bash
   python --version
   node --version
   java -version
   ```

3. **Review and fix errors**
   - Generated code requires customization
   - Fix import paths
   - Update configuration

4. **Use better specifications**
   - Provide more details in requirements
   - Run Socratic session first
   - Export session for context

### "Generated Files Aren't Downloadable"

**Error:** Download button disabled or ZIP is empty

**Solutions:**
```bash
# Check generation status
curl http://localhost:5000/api/generations/{generation_id}/progress

# Verify files were created
docker-compose exec db psql -U socratic_user -d socratic \
  -c "SELECT COUNT(*) FROM generated_files WHERE generation_id='{generation_id}';"

# Re-run generation if no files created
```

---

## Repository Management Issues

### "Repository Import Fails"

**Error:** "Clone failed" or "Access denied"

**Causes:**
- Invalid URL format
- Repository not accessible
- SSH key not configured
- Network firewall blocking

**Solutions:**
1. **Verify URL format**
   ```bash
   # Valid formats
   https://github.com/user/repo.git
   git@github.com:user/repo.git
   https://gitlab.com/user/repo.git
   ```

2. **Test clone manually**
   ```bash
   git clone <your-url> /tmp/test-clone
   ```

3. **Setup SSH (if using SSH URLs)**
   ```bash
   # Generate SSH key
   ssh-keygen -t ed25519 -C "your@email.com"

   # Add to GitHub
   cat ~/.ssh/id_ed25519.pub  # Copy and paste into GitHub settings

   # Test connection
   ssh -T git@github.com
   ```

4. **Use HTTPS instead**
   ```bash
   # If SSH fails, use HTTPS
   https://github.com/user/repo.git
   ```

### "Repository Analysis Incomplete"

**Symptoms:** Repository shows partial analysis, missing languages or frameworks

**Solutions:**
1. **Re-import repository**
   - Delete repository
   - Re-import with same URL

2. **Check supported languages**
   - 30+ languages supported
   - Less common languages may not be detected

3. **Manually verify contents**
   - Visit repository on GitHub
   - Check actual file structure

### "Vector Search Not Working"

**Error:** "Ask AI About Code" returns no context

**Causes:**
- Vectorization disabled during import
- Vector database not initialized
- Search index not built

**Solutions:**
```bash
# Check if vectorization enabled
curl http://localhost:5000/repositories/{repo_id}
# Look for "chunks_created" > 0

# Manually vectorize
docker-compose exec socratic-app python scripts/vectorize_repository.py {repo_id}

# Check ChromaDB
docker-compose exec socratic-app python -c "from src.services.vector_service import VectorService; v = VectorService(); print(v.list_collections())"
```

---

## Performance Issues

### "Application Is Very Slow"

**Symptoms:** Pages take >5 seconds to load, UI is sluggish

**Diagnostic Steps:**
1. **Check server resources**
   ```bash
   docker-compose stats
   # Or local system
   top
   ```

2. **Identify slow queries**
   - Enable query logging in `config.yaml`
   - Check slow query logs

3. **Check network**
   ```bash
   # Test latency
   ping server-host
   curl -o /dev/null -s -w "Time: %{time_total}\n" http://localhost:5000
   ```

**Solutions:**
1. **Add caching**
   ```env
   CACHE_ENABLED=True
   REDIS_URL=redis://localhost:6379
   ```

2. **Optimize database**
   ```sql
   -- Add indexes
   CREATE INDEX idx_projects_owner ON projects(owner_id);
   ANALYZE projects;
   ```

3. **Scale application**
   - Add more app instances
   - Add load balancer
   - Use CDN for static assets

4. **Reduce memory usage**
   ```env
   DATABASE_POOL_SIZE=5
   VECTOR_CACHE_SIZE=100
   ```

### "High Memory Usage"

**Symptoms:** Application crashes or becomes unresponsive

**Investigation:**
```bash
# Check memory
docker-compose stats
ps aux | grep python

# Check what's using memory
docker-compose exec socratic-app python -c "import psutil; p = psutil.Process(); print(p.memory_info())"
```

**Solutions:**
1. **Reduce pool sizes**
   ```env
   DATABASE_POOL_SIZE=5       # Default 20
   VECTOR_CACHE_SIZE=100      # Default 1000
   ```

2. **Enable memory limits**
   ```yaml
   # docker-compose.yml
   services:
     socratic-app:
       mem_limit: 2g
       memswap_limit: 3g
   ```

3. **Restart periodically**
   ```bash
   # Add to crontab
   0 4 * * * docker-compose restart socratic-app
   ```

---

## Security & Access Issues

### "Getting CORS Error"

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
```env
# Allow frontend origin
CORS_ORIGINS=https://your-frontend-domain.com

# Multiple origins
CORS_ORIGINS=https://domain1.com,https://domain2.com

# Development
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### "CSRF Token Missing"

**Error:** `400 Bad Request - CSRF token missing`

**Solutions:**
1. **Include CSRF token in forms**
   ```html
   <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```

2. **Include in AJAX requests**
   ```javascript
   headers: {
     'X-CSRFToken': getCookie('csrf_token')
   }
   ```

3. **Verify cookie enabled**
   - Check browser settings
   - Ensure cookies are enabled

### "Permission Denied - Cannot Access Project"

**Symptoms:** "Access Denied" when opening shared project

**Causes:**
- Not a project member
- Role doesn't have permission
- Project is private

**Solutions:**
1. **Check project permissions**
   - Go to project settings
   - Verify user is added as collaborator

2. **Request access**
   - Contact project owner
   - Ask for appropriate role (Editor, Viewer)

3. **Check role permissions**
   - Owner: Full access
   - Editor: Can create/modify
   - Viewer: Read-only

---

## Database Issues

### "Database Connection Refused"

**Error:** `connection refused` or `cannot connect to database`

**Solutions:**
1. **Check database is running**
   ```bash
   docker-compose ps
   # postgres should be running (Up status)
   ```

2. **Verify connection string**
   ```env
   DATABASE_URL=postgresql://socratic_user:password@db:5432/socratic
   ```

3. **Test connection**
   ```bash
   docker-compose exec db psql -U socratic_user -d socratic -c "SELECT 1;"
   ```

4. **Restart database**
   ```bash
   docker-compose restart db
   docker-compose logs db
   ```

### "Database Locked - Cannot Write"

**Error:** `database is locked` or `cannot acquire lock`

**Solutions:**
1. **Check for active connections**
   ```sql
   SELECT pid, usename, application_name FROM pg_stat_activity;
   TERMINATE pid;
   ```

2. **Reset database**
   ```bash
   docker-compose exec socratic-app \
     python -c "from src.database import reset_database; reset_database()"
   ```

3. **Disable concurrent access**
   - Ensure only one instance running
   - Check lock files in data directory

---

## FAQ

### Q: How often should I back up my data?
**A:**
- Daily backups recommended for production
- More frequent (hourly) if high-value data
- Retention: keep 30 days of daily backups

### Q: Can I use the system offline?
**A:**
- Partial offline capability
- Requires Claude API for code generation (online)
- Repository analysis works offline
- Socratic sessions require AI (online)

### Q: What's the maximum project size?
**A:**
- SQLite: ~1GB database (switch to PostgreSQL for larger)
- Upload limit: 100MB per file
- Vector store: Unlimited (storage dependent)
- Recommended: <10,000 projects per instance

### Q: How do I migrate from SQLite to PostgreSQL?
**A:**
See Deployment Guide section "Migrate from SQLite"
```bash
python scripts/migrate_sqlite_to_postgres.py \
  --sqlite-path data/socratic.db \
  --postgresql-url postgresql://user:pass@host/db
```

### Q: Can multiple users work on same project?
**A:**
- Yes, via collaborators feature
- Real-time synchronization (via polling)
- Concurrent edits may have conflicts
- Changes are persisted automatically

### Q: What happens if API rate limit is exceeded?
**A:**
- Claude API: Error returned
- System: Implements automatic retry with exponential backoff
- User: Receives message about rate limiting
- Solution: Implement request queuing, upgrade API tier

### Q: How do I report a bug?
**A:**
1. Check Troubleshooting guide
2. Check GitHub Issues (may already be reported)
3. File new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Logs (if applicable)
   - Browser/OS information

### Q: How often are updates released?
**A:**
- Major versions: ~3-4 months
- Minor versions: Monthly
- Patches: As needed for bugs
- Security updates: ASAP

### Q: Is data encrypted at rest?
**A:**
- Database: Not encrypted by default (setup required)
- Uploaded files: Stored plaintext (TLS in transit)
- For production: Enable database encryption
- See Security section in Deployment Guide

### Q: What's the maximum number of concurrent users?
**A:**
- Single instance: ~50-100 concurrent users
- Scaling: Add load balancer + multiple instances
- Database bottleneck: ~1000 concurrent with PostgreSQL
- Vector DB: 100+ queries/second

### Q: Can I customize the UI?
**A:**
- Frontend: Bootstrap-based, easy to customize
- Colors: Edit CSS in templates
- Layout: Modify Jinja2 templates
- See User Guide for customization options

---

## Getting Help

### Before Asking for Help

1. ✅ Check this Troubleshooting guide
2. ✅ Check GitHub Issues (search for keywords)
3. ✅ Check application logs
4. ✅ Try restarting application
5. ✅ Check environment variables
6. ✅ Test database connectivity

### Where to Get Help

**Documentation:**
- User Guide: `docs/USER_GUIDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- API Reference: `docs/API_DOCUMENTATION.md`
- Deployment: `docs/DEPLOYMENT.md`

**Community:**
- GitHub Issues: https://github.com/your-org/socrates/issues
- GitHub Discussions: https://github.com/your-org/socrates/discussions
- Stack Overflow: Tag `socratic-rag`

**Direct Support:**
- Email: support@socratic-rag.com
- Discord: https://discord.gg/your-server
- Slack: https://your-workspace.slack.com

**Reporting Issues:**
- Include error messages
- Share logs (sanitized)
- Describe reproduction steps
- Mention: OS, Python version, Docker version

---

## Quick Reference - Command Cheatsheet

```bash
# Application Control
docker-compose up -d        # Start services
docker-compose down         # Stop services
docker-compose ps          # View running services
docker-compose restart     # Restart services

# Logs
docker-compose logs -f socratic-app  # Follow app logs
docker-compose logs db               # Database logs

# Database
docker-compose exec db psql -U socratic_user -d socratic
docker-compose exec socratic-app python -c "from src.database import init_database; init_database()"

# Backup
docker-compose exec db pg_dump -U socratic_user socratic > backup.sql

# Reset
docker-compose down -v     # Remove volumes
docker-compose up -d       # Start fresh

# Health Check
curl http://localhost:5000/api/health
```

---

## Still Need Help?

If you've tried all troubleshooting steps and still have issues:

1. **Create GitHub Issue** with:
   - Title: Descriptive issue title
   - Description: What were you doing?
   - Steps: How to reproduce
   - Logs: Relevant error messages
   - Environment: OS, Python version, Docker version

2. **Contact support**:
   - Email: support@socratic-rag.com
   - Include: Issue description + reproduction steps

3. **Community help**:
   - GitHub Discussions
   - Stack Overflow (tag: socratic-rag)
   - Discord community

We're here to help! 🚀
