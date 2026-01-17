# Socrates Documentation Index

Complete guide to finding documentation for Socrates features and functionality.

## Quick Links

- **Getting Started**: [Quick Start Guide](#getting-started)
- **Sponsorship & Tiers**: [Premium Features](#sponsorship--premium-tiers)
- **API Reference**: [API Documentation](#api-reference)
- **Contributing**: [How to Help](#how-to-help)

---

## Getting Started

### For New Users

- **[README.md](../README.md)** - Project overview, features, quick start
- **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** - Quick sponsorship reference (start here!)
- **Setup & Installation** - See README Quick Start section

### CLI & Local Development

- **[Local Development](LOCAL_DEVELOPMENT.md)** - Setting up dev environment
- **[Configuration](CONFIGURATION.md)** - Environment variables and settings

---

## Sponsorship & Premium Tiers

### User Resources

**📖 Read These First:**
1. **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** - Quick 5-minute reference
2. **[SPONSORSHIP.md](../SPONSORSHIP.md)** - Complete sponsorship guide
3. **[TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md)** - Detailed tier information

### What You'll Learn

- **SPONSORSHIP_USER_GUIDE.md**
  - How to sponsor in 3 steps
  - Check your tier in UI and API
  - Common tasks (upgrade, downgrade, link GitHub)
  - Troubleshooting quick reference

- **SPONSORSHIP.md** (Root directory)
  - Sponsorship tiers and benefits
  - How sponsorship works step-by-step
  - FAQ (frequently asked questions)
  - GitHub Sponsors secure payment info
  - Tier change management
  - Customer support

- **TIERS_AND_SUBSCRIPTIONS.md**
  - Feature vs. quota explanation
  - Storage quota management
  - Testing mode details
  - Billing and payment history
  - Comprehensive troubleshooting

### Admin Resources

- **[SPONSORSHIP_SETUP.md](SPONSORSHIP_SETUP.md)** - Server setup and webhook configuration
- **[LOCAL_WEBHOOK_TESTING.md](../LOCAL_WEBHOOK_TESTING.md)** - Testing sponsorship webhooks locally
- **[GITHUB_SPONSORS_SETUP.md](../GITHUB_SPONSORS_SETUP.md)** - Detailed GitHub Sponsors integration

---

## API Reference

### Sponsorship Endpoints

```
GET  /sponsorships/info                    - Public sponsorship info (no auth)
GET  /sponsorships/verify                  - Check user's active sponsorship
GET  /sponsorships/history                 - User's sponsorship history
GET  /sponsorships/payments                - User's payment history
GET  /sponsorships/refunds                 - User's refund history
GET  /sponsorships/tier-history            - User's tier change timeline
GET  /sponsorships/analytics               - Comprehensive sponsorship analytics
GET  /sponsorships/payment-methods         - User's saved payment methods
POST /sponsorships/webhooks/github-sponsors - GitHub webhook receiver
GET  /sponsorships/admin/dashboard         - Admin dashboard (repo owner only)
```

### Subscription Endpoints

```
GET  /subscription/status                  - Check subscription tier and quotas
GET  /subscription/storage                 - Storage usage details
POST /subscription/testing-mode            - Enable/disable testing mode
```

### Complete API Documentation

- **[API_REFERENCE.md](API_REFERENCE.md)** - Full API endpoint documentation
- **Running Instance**: Visit `http://localhost:8000/docs` for interactive Swagger UI

---

## Features

### Code Generation
- Workspace organization
- Code generation with AI
- Analysis and recommendations

### Collaboration
- Real-time collaboration
- Team projects
- Knowledge sharing

### Knowledge Management
- Knowledge base creation
- RAG (Retrieval-Augmented Generation)
- Knowledge search and retrieval

### Analytics
- Project analytics
- Usage reporting
- Performance metrics

---

## How to Help

### For Users

- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Ways to contribute
  - Financial support (sponsorship)
  - Code contributions
  - Documentation improvements
  - Bug reports and feature requests
  - Community participation

### For Developers

**Setting up for development:**
1. Clone repository
2. Follow development setup in [CONTRIBUTING.md](../CONTRIBUTING.md)
3. Read code standards and guidelines
4. Submit pull requests

**Code areas:**
- Backend API: `socrates-api/src/socrates_api/`
- Business Logic: `socratic_system/`
- Frontend: `socrates-frontend/src/`
- Database: `socratic_system/database/`
- Sponsorships: `socratic_system/sponsorships/`

---

## Key Documentation Files

### Root Directory
```
├── README.md                    - Main project overview
├── SPONSORSHIP.md               - Complete sponsorship guide
├── CONTRIBUTING.md              - How to contribute
├── TIERS_AND_SUBSCRIPTIONS.md   - Tier details
└── LOCAL_WEBHOOK_TESTING.md     - Webhook testing guide
```

### Docs Directory (`docs/`)
```
├── INDEX.md                      - This file
├── SPONSORSHIP_USER_GUIDE.md     - Quick user reference
├── TIERS_AND_SUBSCRIPTIONS.md    - Detailed tier information
├── SPONSORSHIP_SETUP.md          - Server setup
├── API_REFERENCE.md              - API documentation
├── LOCAL_DEVELOPMENT.md          - Dev environment setup
└── CONFIGURATION.md              - Configuration guide
```

---

## By Use Case

### I want to sponsor/upgrade my tier
→ **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** (5 min read)
→ **[SPONSORSHIP.md](../SPONSORSHIP.md)** (detailed)

### I need to understand what my tier includes
→ **[TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md)**
→ **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** - "Features Across Tiers"

### I want to check my payment history
→ **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** - "View Payment History" section
→ **API**: GET `/sponsorships/payments`

### I'm hitting my project/storage quota
→ **[SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md)** - "Quotas Explained" section
→ **[TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md)** - "Quota System"

### I want to contribute code
→ **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Complete guide

### I want to financially support Socrates
→ **[SPONSORSHIP.md](../SPONSORSHIP.md)** - Sponsorship options
→ **[github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)** - Sponsor now

### I'm setting up Socrates for production
→ **[README.md](../README.md)** - Quick Start → Kubernetes section
→ **[CONFIGURATION.md](CONFIGURATION.md)** - Environment setup
→ **[SPONSORSHIP_SETUP.md](SPONSORSHIP_SETUP.md)** - Webhook configuration

### I'm testing sponsorships locally
→ **[LOCAL_WEBHOOK_TESTING.md](../LOCAL_WEBHOOK_TESTING.md)** - ngrok and testing guide
→ **[setup_github_sponsors_webhook.py](../setup_github_sponsors_webhook.py)** - Webhook registration script

### I'm developing a feature
→ **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Code standards and setup
→ **[API_REFERENCE.md](API_REFERENCE.md)** - API documentation
→ **[LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)** - Dev environment

### I found a bug
→ **[CONTRIBUTING.md](../CONTRIBUTING.md)** - "Bug Reports" section
→ **[GitHub Issues](https://github.com/Nireus79/Socrates/issues)** - Report here

---

## FAQ

### Where do I sponsor?
→ [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)

### How do I check my tier?
→ Socrates Settings → Subscription
→ Or API: GET `/sponsorships/verify`

### What's the difference between tiers?
→ [TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md)
→ [SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md) - "Sponsorship Tiers" section

### How long does sponsorship activation take?
→ Usually instant (5 seconds)
→ See [SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md) - Troubleshooting

### Can I downgrade my tier?
→ Yes, see [SPONSORSHIP_USER_GUIDE.md](SPONSORSHIP_USER_GUIDE.md) - "Downgrade My Tier"

### Is my payment information secure?
→ Yes! See [SPONSORSHIP.md](../SPONSORSHIP.md) - FAQ section

### Can I contribute without sponsoring?
→ Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md) - "Code Contributions" and "Other Ways to Contribute"

---

## Need Help?

**Documentation-related:**
- Can't find what you need? Check [GitHub Discussions](https://github.com/Nireus79/Socrates/discussions)
- Spot an error? Open an issue on [GitHub Issues](https://github.com/Nireus79/Socrates/issues)

**Product Support:**
- Sponsorship issues: See [SPONSORSHIP.md](../SPONSORSHIP.md) - Support section
- Technical issues: [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- Questions: [GitHub Discussions](https://github.com/Nireus79/Socrates/discussions)

---

## Version Info

- **Last Updated**: January 2024
- **Socrates Version**: 1.2.0+
- **Status**: Complete documentation for v1.2.0 sponsorship integration

---

## Document Relationship Map

```
User Learning Path:
  README.md
    ↓
  SPONSORSHIP_USER_GUIDE.md (quick start)
    ↓
  SPONSORSHIP.md (if need more detail)
    ↓
  TIERS_AND_SUBSCRIPTIONS.md (detailed reference)

Developer Learning Path:
  README.md
    ↓
  CONTRIBUTING.md
    ↓
  LOCAL_DEVELOPMENT.md
    ↓
  API_REFERENCE.md
    ↓
  Specific subsystem docs (Sponsorships, etc.)

Admin/Setup Path:
  README.md → Kubernetes section
    ↓
  CONFIGURATION.md
    ↓
  SPONSORSHIP_SETUP.md
    ↓
  LOCAL_WEBHOOK_TESTING.md (if local testing needed)
```

---

**Happy Sponsoring! 💜**
