# Socrates Quick Start - Docker

**Get Socrates running in 2 minutes.**

---

## First Time Setup

```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Start Socrates
sudo docker compose up --build
```

Open browser: **http://localhost:3000**

1. Register a new account
2. Go to **Settings → LLM**
3. Add your API key (Claude, Ollama, OpenAI, Gemini, etc.)
4. Create a project
5. Start asking questions!

**That's it!** Encryption keys are auto-generated and saved. No manual setup needed.

---

## Restart Socrates

```bash
sudo docker compose up
```

Your data persists automatically.

---

## Stop Socrates

```bash
sudo docker compose down
```

Your data is safe - it's stored in a Docker volume.

---

## Complete Reset (Delete Everything)

**Warning: This deletes all your projects and API keys!**

```bash
cd ~/PycharmProjects/Socrates

# Stop Docker
sudo docker compose down

# Delete all volumes (database, cache, everything)
sudo docker volume rm socrates_data socrates_redis_data 2>/dev/null

# Delete old database if it exists
rm ~/.socrates/projects.db 2>/dev/null

# Rebuild from scratch
sudo docker compose up --build
```

Then register and set up again from scratch.

---

## Troubleshooting

### "Port 3000 not accessible"
```bash
# Check if services are running
sudo docker compose ps

# View logs
sudo docker compose logs -f
```

### "No LLM provider configured"
1. Go to **Settings → LLM**
2. Select a provider (Claude, Ollama, etc.)
3. Add your API key
4. Try again

### "API not responding"
```bash
# Restart everything
sudo docker compose down
sudo docker compose up
```

### "Need to see logs"
```bash
sudo docker compose logs -f socrates-api
```

---

## Environment Variables (Optional)

To customize your deployment, set environment variables before `docker compose up`:

```bash
export ENVIRONMENT=production
export ALLOWED_HOSTS=yourdomain.com
export CORS_ORIGINS=https://yourdomain.com

sudo docker compose up
```

---

## That's All!

Everything else happens automatically:
- ✅ Encryption keys generated and persisted
- ✅ Database created and stored safely
- ✅ API keys encrypted before storage
- ✅ Sessions managed securely
- ✅ Data survives restarts

For more details, see [DOCKER_SETUP_GUIDE.md](DOCKER_SETUP_GUIDE.md).

