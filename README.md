# Socrates AI - Collaborative Development Platform

A complete project management and vibe coding RAG system.
Comprehensive AI-powered platform for collaborative software project development, with real-time collaboration,
multi-agent orchestration, and production-grade infrastructure.

> **Status**: Production Ready (v1.1.0)
> **License**: MIT
> **Architecture**: FastAPI Backend + React Frontend + PostgreSQL + Redis + ChromaDB

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

### Docker Compose (Local Development)

```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create environment
cp .env.production.example .env.local

# Start services
docker-compose up -d

# Access at http://localhost:3000 (Frontend) and http://localhost:8000 (API)
```

### Kubernetes (Production)

```bash
# Using Helm
helm install socrates ./helm \
  --namespace production \
  --set api.image.tag=latest \
  --set postgresql.auth.password=$(openssl rand -base64 32)

# Or using kubectl with manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/*.yaml
```

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

```
┌─────────────────────────────────────────────────────────────┐
│                    Socrates Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React)          API Server (FastAPI)              │
│  ┌──────────────┐          ┌──────────────────┐              │
│  │ React UI     │◄─────────┤ REST Endpoints   │              │
│  │ WebSocket    │          │ Rate Limiting    │              │
│  │ Real-time    │          │ Security Headers │              │
│  └──────────────┘          │ JWT Auth + MFA   │              │
│                            │ CORS Hardened    │              │
│                            └──────────────────┘              │
│                                      │                       │
│                ┌─────────────────────┼──────────────────┐   │
│                │                     │                  │   │
│        ┌───────▼──────┐     ┌────────▼────────┐  ┌─────▼──┐ │
│        │  PostgreSQL  │     │  Redis Cache    │  │ChromaDB│ │
│        │  - Projects  │     │  - Sessions     │  │ - RAG  │ │
│        │  - Users     │     │  - Rate Limits  │  │Vectors │ │
│        │  - Knowledge │     │  - Embeddings   │  └────────┘ │
│        └──────────────┘     └─────────────────┘             │
│                                                               │
│        ┌──────────────────────────────────────┐             │
│        │        Multi-Agent Orchestrator      │             │
│        ├──────────────────────────────────────┤             │
│        │ - ProjectManager                     │             │
│        │ - CodeGenerator                      │             │
│        │ - SocraticCounselor                  │             │
│        │ - ContextAnalyzer                    │             │
│        │ - ConflictDetector                   │             │
│        │ - KnowledgeManager                   │             │
│        └──────────────────────────────────────┘             │
│                          │                                   │
│                  ┌───────▼────────┐                         │
│                  │  Claude AI API  │                         │
│                  └────────────────┘                         │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│              Kubernetes Orchestration Layer                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Pod Scaling  │  │ Load Balancing│  │ Health Checks│      │
│  │ Auto-Healing │  │ Service Mesh  │  │ Self-Healing│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│              Monitoring & Observability                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Prometheus   │  │ Grafana       │  │ AlertManager │      │
│  │ Metrics      │  │ Dashboards    │  │ Notifications│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Documentation

- [📖 QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md) - Get started quickly
- [🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture deep-dive
- [📚 API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API documentation
- [🚀 DEPLOYMENT.md](docs/DEPLOYMENT.md) - Production deployment & Docker guide
- [⚙️ CONFIGURATION.md](docs/CONFIGURATION.md) - Environment configuration
- [👨‍💻 DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) - Development setup & patterns
- [🔄 CI_CD.md](docs/CI_CD.md) - GitHub Actions workflows & testing
- [🐛 TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Problem solving guide
- [📋 INSTALLATION.md](docs/INSTALLATION.md) - Setup and installation instructions

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

### GitHub Sponsors
Become a sponsor to unlock premium features and support active development:

- **[$5/month Sponsor](https://github.com/sponsors/Nireus79)** → **Pro Tier**
  - 10 projects
  - 5 team members
  - 100GB storage
  - Priority support

- **[$15/month Sponsor](https://github.com/sponsors/Nireus79)** → **Enterprise Tier**
  - Unlimited projects
  - Unlimited team members
  - Unlimited storage
  - Dedicated support

### Other Ways to Support
- **Star the repository** ⭐
- **Fork and contribute** code improvements
- **Share feedback** and feature requests
- **Report bugs** to help us improve
- **Write documentation** for new features

---

## Contributing



1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## Support

- **Bugs & Issues**: [GitHub Issues](https://github.com/your-org/Socrates/issues)
- **Documentation**: [Docs Directory](./docs)
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
