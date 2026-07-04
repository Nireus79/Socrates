# Socrates Docker Quick Start

**Get Socrates running in 5 minutes.**

---

## Prerequisites

- Docker & Docker Compose installed
- ~3GB disk space
- Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

---

## 1️⃣ Generate Configuration (1 minute)

Navigate to the docker directory:

```bash
cd deployment/docker
```

**Linux/macOS:**
```bash
./generate-keys.sh
```

**Windows:**
```bash
generate-keys.bat
```

✅ This creates `.env` with all required keys automatically.

---

## 2️⃣ Add Your API Key (30 seconds)

Edit the generated `.env` file:

```bash
nano .env  # or use your editor
```

Find this line:
```
ANTHROPIC_API_URL=sk-ant-YOUR-KEY-HERE
```

Replace `sk-ant-YOUR-KEY-HERE` with your actual API key from [console.anthropic.com](https://console.anthropic.com).

Save the file.

---

## 3️⃣ Start Services (2 minutes)

From the `deployment/docker` directory:

```bash
docker-compose up -d
```

Wait 10-15 seconds for all containers to be ready.

**Check status:**
```bash
docker-compose ps
```

All containers should show `Up`.

---

## 4️⃣ Access Socrates ✨

Open in your browser:

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

---

## 5️⃣ First Steps

1. **Register** a new account
2. **Create a project** with a description
3. **Ask Socratic questions** about your project
4. **Generate code** from your project definition

---

## 🆘 Troubleshooting

### "Port already in use" error
```bash
# Find what's using the port
lsof -i :8000  # or :3000

# Or use different ports in .env:
SOCRATES_API_PORT=8001
CORS_ORIGINS=http://localhost:3001
```

### "Cannot connect to Docker daemon"
```bash
# Make sure Docker is running
docker ps

# On Windows, start Docker Desktop
```

### "API not responding"
```bash
# Check logs
docker-compose logs api

# Wait 20-30 seconds, containers need time to start
docker-compose ps
```

### "Frontend stuck loading"
```bash
# Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)
# Or restart frontend container
docker-compose restart frontend
```

### "Data lost after container restart" or "Database file not created"
```bash
# Check if SOCRATES_DATA_DIR is set
docker-compose exec api env | grep SOCRATES_DATA_DIR

# Check if projects.db file exists
docker-compose exec api ls -la /app/data/

# Run diagnostic to test database initialization
docker-compose exec api python /app/test-db-init.py

# If projects.db is missing, check API logs
docker-compose logs api | tail -50

# See: Docker Data Persistence Guide (./DOCKER_DATA_PERSISTENCE.md)
```

### "Need to change API key"
```bash
# Edit .env
nano .env

# Restart containers
docker-compose down
docker-compose up -d
```

---

## 📝 Common Commands

```bash
# View logs
docker-compose logs -f api

# Stop containers (data persists)
docker-compose down

# Restart containers
docker-compose restart

# Access API container shell
docker-compose exec api bash

# View database
docker-compose exec api ls -la /app/data/

# Inspect volume (check if data persists)
docker volume inspect deployment_docker_socrates_data
```

---

## ✅ Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Should return: {"status":"healthy",...}
```

---

## 🎓 Next Steps

- **Learn more**: See [Docker README](./README.md)
- **Data persistence issues**: See [Docker Data Persistence Guide](./DOCKER_DATA_PERSISTENCE.md) — **Important if data is lost after restart!**
- **Production setup**: See the main project documentation

---

## 🚀 Pro Tips

1. **Persistent data**: Your projects and database survive container restarts
2. **Custom ports**: Edit `.env` to change `SOCRATES_API_PORT` and `CORS_ORIGINS`
3. **Performance**: Initial startup takes 15-20s; subsequent restarts are 5-10s
4. **Multiple users**: Create separate `.env` files for different setups

---

**Questions?** Check [Docker README](./README.md) or open an issue on GitHub.
