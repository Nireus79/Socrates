# Contributing to Socrates

Thank you for your interest in contributing to Socrates! There are many ways to support the project.

## Financial Support (Sponsorship)

The most impactful way to support Socrates development is through **GitHub Sponsors**:

### 🎁 Become a Sponsor

Visit [GitHub Sponsors - Nireus79](https://github.com/sponsors/Nireus79) to become a sponsor.

**Your sponsorship:**
- ✅ Directly funds development and maintenance
- ✅ Automatically upgrades your Socrates account to premium tiers
- ✅ Supports open-source innovation
- ✅ Gets you a sponsor badge on GitHub

**Sponsorship Tiers:**

| Tier | Amount | Socrates Upgrade |
|------|--------|------------------|
| Supporter | $5/month | **Pro Tier** (10 projects, 100GB storage) |
| Contributor | $15/month | **Enterprise Tier** (unlimited everything) |
| Custom | $25+/month | **Enterprise+** (priority support) |

**How Sponsorship Works:**
1. Sponsor on GitHub
2. Your Socrates account automatically upgrades (within seconds)
3. No additional setup needed!
4. View your payment history in Socrates Settings

👉 [Full Sponsorship Guide](SPONSORSHIP.md)

---

## Code Contributions

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Docker** (for local development with services)
- **Git**

### Development Setup

```bash
# Clone repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r socrates-api/requirements.txt
cd socrates-frontend && npm install && cd ..

# Start local development environment
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
alembic upgrade head

# Start backend
python -m socrates_api.main

# Start frontend (in another terminal)
cd socrates-frontend && npm start
```

### Code Standards

1. **Python Code**
   - Follow PEP 8 style guide
   - Use type hints
   - Write docstrings
   - Run linter: `pylint socrates_api/`
   - Run formatter: `black socrates_api/`
   - Run type checker: `mypy socrates_api/`

2. **JavaScript/React Code**
   - Use ESLint configuration in project
   - Use Prettier for formatting
   - Write functional components with hooks
   - Include JSDoc comments for complex logic

3. **Testing**
   - Write unit tests for new features
   - Write integration tests for API endpoints
   - Maintain >80% code coverage
   - Run tests: `pytest socrates_api/tests/`

4. **Commits**
   - Use clear commit messages: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
   - Keep commits focused on single changes
   - Reference issues when applicable: `Closes #123`

### Pull Request Process

1. **Fork the repository** and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit:
   ```bash
   git commit -am 'Add your feature description'
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request**:
   - Clear title describing changes
   - Detailed description of what changed and why
   - Reference related issues
   - Include test results/screenshots if applicable

5. **Code review**:
   - Address review comments
   - Ensure all checks pass
   - Respond to feedback

### Project Structure

```
Socrates/
├── socrates-api/                 # FastAPI backend
│   ├── src/socrates_api/        # Main API code
│   │   ├── routers/             # API endpoints
│   │   ├── models/              # Data models
│   │   └── dependencies/        # Shared dependencies
│   └── tests/                   # Backend tests
├── socratic_system/             # Core business logic
│   ├── database/                # Database access
│   ├── subscription/            # Monetization logic
│   ├── sponsorships/            # GitHub Sponsors integration
│   └── projects/                # Project management
├── socrates-frontend/           # React frontend
│   ├── src/components/          # React components
│   ├── src/pages/               # Page components
│   └── src/services/            # API services
└── docs/                        # Documentation
```

---

## Other Ways to Contribute

Even without code contributions, you can help:

### 📚 Documentation
- Improve existing documentation
- Write tutorials or guides
- Add API documentation examples
- Fix typos and clarify confusing sections

### 🐛 Bug Reports
- Create detailed issue reports
- Include reproduction steps
- Attach relevant logs or screenshots
- Help us understand the environment

### 💡 Feature Requests
- Suggest new features or improvements
- Discuss use cases
- Vote on existing feature requests
- Help prioritize improvements

### 🔊 Community
- Answer questions in discussions
- Help other users
- Share your experience with Socrates
- Contribute to community projects

---

## Development Guidelines

### Architecture Principles

1. **Separation of Concerns**
   - Database layer (project_db.py)
   - Business logic (sponsorships/, subscription/)
   - API layer (routers/)

2. **Dependency Injection**
   - Use FastAPI dependencies
   - Inject database connections
   - Inject configuration

3. **Error Handling**
   - Use specific HTTP status codes
   - Return meaningful error messages
   - Log errors for debugging

4. **Security**
   - Validate all inputs
   - Use parameterized queries
   - Implement rate limiting
   - Protect sensitive endpoints

### Testing

```bash
# Run all tests
pytest socrates_api/tests/ -v

# Run specific test file
pytest socrates_api/tests/test_sponsorships.py -v

# Run with coverage
pytest socrates_api/tests/ --cov=socrates_api

# Run type checking
mypy socrates_api/
```

---

## Getting Help

- **Questions?** Check [Discussions](https://github.com/Nireus79/Socrates/discussions)
- **Found a bug?** Open an [Issue](https://github.com/Nireus79/Socrates/issues)
- **Want to chat?** Join our community
- **Sponsorship questions?** See [SPONSORSHIP.md](SPONSORSHIP.md)

---

## Code of Conduct

Please note we have a Code of Conduct. Be respectful and inclusive in all interactions.

---

## Recognition

Contributors are recognized in:
- Project README (major contributions)
- GitHub Contributors page
- Release notes (for PRs)

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

## Questions?

Feel free to:
- Open an issue for discussion
- Start a discussion in GitHub Discussions
- Ask in pull request comments
- Reach out to the maintainer

**Thank you for supporting Socrates! 💜**
