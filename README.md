# Socrates AI - Collaborative Development Platform

Nireus79 Available for freelance work. Please contact me.

Socrates AI
Self-hosted AI agent platform with RAG, tools and collaboration.

• Python API
• CLI
• Web UI
• Docker deployment

A complete project management and vibe coding RAG system.
Comprehensive AI-powered platform for collaborative software project development, with real-time collaboration,
multi-agent orchestration, and production-grade infrastructure.

> **Status**: Production Ready (v1.1.0)
> **License**: MIT
> **Architecture**: FastAPI Backend + React Frontend + PostgreSQL + Redis + ChromaDB
>
> <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/075353f2-6871-4b03-93d0-d319b97d3efd" />


## Key Features

🎓 **Socratic Learning**: AI-guided Socratic questioning to help teams think through complex design and development problems

🤖 **Multi-Agent System**: Specialized agents for project management, code generation, conflict resolution, knowledge management, and more

📚 **Knowledge Management**: RAG (Retrieval-Augmented Generation) with vector embeddings for intelligent knowledge retrieval and synthesis

🔄 **Real-Time Collaboration**: WebSocket-powered real-time presence, cursor tracking, and document synchronization

🔐 **Enterprise Security**: JWT authentication with MFA, OWASP-compliant security headers, role-based access control, encryption

⚡ **High-Performance**: Rate limiting, Redis caching, connection pooling, async database queries, optimized query execution

📊 **Production Monitoring**: Prometheus metrics, Grafana dashboards, health checks, detailed logging, performance tracking

☸️ **Kubernetes-Ready**: Complete Kubernetes manifests, Helm charts, Docker multi-platform builds, CI/CD automation

## Quick Start

### 1-Minute Setup

```bash
# Install (choose one)
pip install socrates-ai              # Everything
# OR
pip install socratic-core            # Just framework
# OR
pip install socratic-core socrates-cli    # Framework + CLI

# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Start API server (optional)
socrates-api

# In another terminal, use the CLI
socrates project create --name "My Project" --owner "your-name"
```

### Full Setup (Docker)

```bash
git clone https://github.com/themsou/Socrates.git
cd Socrates

# Create environment
cp .env.example .env

# Start with Docker
docker-compose up -d

# Access API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with JWT
- `POST /auth/logout` - Logout and invalidate session
- `POST /auth/refresh` - Refresh access token
- `POST /auth/mfa/setup` - Setup MFA (TOTP)

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `DELETE /projects/{id}` - Delete project
- `POST /projects/{id}/advance-phase` - Move to next phase
- `POST /projects/{id}/team-members` - Add team member

### Chat & Knowledge
- `POST /projects/{id}/chat/sessions` - Create chat session
- `POST /projects/{id}/chat/sessions/{sid}/message` - Send message
- `GET /projects/{id}/knowledge` - List knowledge entries
- `POST /projects/{id}/knowledge` - Add knowledge entry
- `GET /projects/{id}/knowledge/search` - Search knowledge

### Analytics & Reports
- `GET /projects/{id}/analytics` - Project analytics
- `GET /projects/{id}/analytics/detail` - Detailed metrics
- `GET /projects/{id}/chat/sessions/{sid}/export` - Export chat

See [API_REFERENCE.md](docs/API_REFERENCE.md) for complete endpoint documentation.

## Architecture

Socrates has been refactored from a 50,000-line monolith into a modular ecosystem of reusable libraries:

```
                    Socrates Nexus (LLM Foundation)
                            ↓
        ┌───────────────────────────────────┐
        │      socratic-core (20 KB)        │
        │  ─────────────────────────────    │
        │  • Configuration                  │
        │  • Events                         │
        │  • Exceptions                     │
        │  • Logging                        │
        │  • Utilities                      │
        └────────────────────┬──────────────┘
             ┌───────────────┼───────────────┐
             │               │               │
    ┌────────▼────┐  ┌───────▼───────┐  ┌──▼──────────┐
    │ socratic-rag│  │ socratic-     │  │ socratic-   │
    │  (8 KB)     │  │ agents        │  │ analyzer    │
    │             │  │  (15 KB)      │  │  (8 KB)     │
    │ 1 dep       │  │               │  │             │
    │ (Nexus)     │  │ 1 dep (Nexus) │  │ 1 dep       │
    └─────────────┘  └───────────────┘  └─────────────┘
             │               │               │
             └───────────────┼───────────────┘
                      ↓
        ┌─────────────────────────────┐
        │ socratic-knowledge (8 KB)   │
        │ socratic-learning (10 KB)   │
        │ socratic-workflow (9 KB)    │
        │ socratic-conflict (8 KB)    │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼─────┐   ┌───▼────┐   ┌────▼───┐
   │socrates- │   │socrates│   │Socrates│
   │   cli    │   │  -api  │   │(Main)  │
   │(50 KB)   │   │(100KB) │   │(200KB) │
   └──────────┘   └────────┘   └────────┘
```

**Key Benefits of Modular Architecture**:
- Pick components you need (no bloat)
- 25x smaller core (20 KB vs 500 KB)
- 10x fewer dependencies (3 vs 30)
- 100% backward compatible
- Scales from embedded to enterprise

Learn more: [ARCHITECTURE.md](ARCHITECTURE.md) | [Transformation Story](TRANSFORMATION_STORY.md)

## Documentation

### Getting Started
- [📖 QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [📋 INSTALL.md](INSTALL.md) - Complete installation guide
- [🔄 MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Upgrade from old versions

### Architecture & Design
- [🏗️ ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design
- [📚 TRANSFORMATION_STORY.md](TRANSFORMATION_STORY.md) - How we decomposed the monolith
- [✨ MODULAR_VS_MONOLITH_COMPARISON.md](MODULAR_VS_MONOLITH_COMPARISON.md) - Before/after comparison
- [📝 BLOG_POST_MONOLITH_TO_MODULAR.md](BLOG_POST_MONOLITH_TO_MODULAR.md) - Marketing story

### API & CLI Documentation
- [🌐 socrates-api/README.md](socrates-api/README.md) - REST API server documentation
- [💻 socrates-cli/README.md](socrates-cli/README.md) - CLI tool documentation
- [🔧 socratic-core/README.md](socratic-core/README.md) - Core framework documentation

## Production Features

✅ **Security**
- JWT authentication with TOTP MFA
- OWASP Top 10 protection
- Rate limiting (5/min free, 100/min pro)
- Input validation & sanitization
- Encrypted database fields

✅ **Performance**
- Connection pooling (20 connections)
- Redis caching with in-memory fallback
- Query optimization & indexing
- Async database operations
- Request compression

✅ **Reliability**
- Database transactions & rollback
- Automated backups with S3 support
- Health monitoring & self-healing
- Graceful degradation
- Error tracking & logging

✅ **Operations**
- Kubernetes manifests & Helm charts
- Docker multi-platform builds
- CI/CD GitHub Actions workflows
- Prometheus metrics & Grafana dashboards
- Structured logging

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/your-org/socrates.git
cd socrates

# Create environment
cp .env.production.example .env.local

# Install dependencies
pip install -r requirements.txt
npm install  # For frontend

# Run tests
pytest tests/ --cov=socratic_system
```

### Run Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=socratic_system

# Specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# With coverage report
pytest --cov=socratic_system --cov-report=html
```

### Code Quality

```bash
# Format code
black socrates_api/ socratic_system/
isort socrates_api/ socratic_system/

# Lint
ruff check socrates_api/ socratic_system/

# Type check
mypy socrates_api/ socratic_system/

# Security scan
bandit -r socrates_api/ socratic_system/
```

## ☕ Support Socrates Development

Socrates is free and open-source. If you find it useful, consider supporting development through GitHub Sponsors:

### 🎁 GitHub Sponsors - Premium Tiers

Become a sponsor to unlock premium features and support active development. **Your sponsorship is automatically applied to your Socrates account!**

| Tier | Price | Features | Link |
|------|-------|----------|------|
| **Supporter** | $5/month | 10 projects, 5 team members, 100GB storage | [Sponsor Now](https://github.com/sponsors/Nireus79) |
| **Contributor** | $15/month | Unlimited projects, unlimited members, unlimited storage | [Sponsor Now](https://github.com/sponsors/Nireus79) |
| **Custom** | $25+/month | All Enterprise + priority support | [Sponsor Now](https://github.com/sponsors/Nireus79) |

**How It Works:**
1. Sponsor on [GitHub Sponsors](https://github.com/sponsors/Nireus79)
2. Your Socrates account is **automatically upgraded** (usually within seconds)
3. Start using premium features immediately
4. View payment history and tier details in Socrates Settings

👉 **[Full Sponsorship Guide](SPONSORS.md)** - Learn about sponsorship tiers and benefits for the Socratic Ecosystem.

### Other Ways to Support
- **Star the repository** ⭐
- **Fork and contribute** code improvements
- **Share feedback** and feature requests
- **Report bugs** to help us improve
- **Write documentation** for new features
- **Spread the word** about Socrates

---

## Contributing



1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## Support

- **Bugs & Issues**: [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- **Documentation**: [Docs Directory](./docs)
- **Sponsorship**: [Sponsorship Guide](SPONSORS.md)
- **GitHub Sponsors**: [Become a Sponsor](https://github.com/sponsors/Nireus79)
- **Email**: support@socrates-ai.dev

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

Built with:
- [Claude AI](https://anthropic.com) by Anthropic
- [FastAPI](https://fastapi.tiangolo.com/) for REST API
- [PostgreSQL](https://www.postgresql.org/) for data persistence
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Redis](https://redis.io/) for caching
- [Kubernetes](https://kubernetes.io/) for orchestration

---

**Made with ❤️ for teams who believe in collaborative development**
