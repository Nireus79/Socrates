# Quick Access Guide - All New Features

## 🎯 Feature Quick Links

### 1. GitHub Integration
**What it does:** Import and synchronize GitHub repositories with your Socrates projects

**Where to access:**
- **Projects Page** → "Import from GitHub" button (top right)
- **Project Detail Page** → "GitHub" tab → "Link Repository" button
- **Quick Actions** bar on project detail

**Main actions:**
- Import repository as new project
- Pull latest changes from GitHub
- Push local changes to repository
- Sync (bidirectional)
- View sync status and history

---

### 2. Knowledge Base
**What it does:** Import, organize, and search project documentation and knowledge

**Where to access:**
- **Sidebar** → "Knowledge Base" menu item
- Direct URL: `/knowledge`

**Main actions:**
- Import files (documents, code samples)
- Import from URLs (web pages, articles)
- Paste text directly
- Search across all documents
- Tag and organize documents
- Export knowledge base

---

### 3. LLM Provider Management
**What it does:** Switch between different LLM providers and manage API keys

**Where to access:**
- **Settings** → "LLM Providers" tab (top navigation)

**Main sections:**
- **Current Configuration** - View active provider and model
- **Available Providers** - Claude, OpenAI, Gemini, Local LLM
- **Provider Cards** - See configuration status for each
- **API Key Manager** - Add/update/remove API keys securely
- **Usage Statistics** - View requests, tokens, and costs
- **Model Selection** - Choose specific model per provider

---

### 4. Project Analysis
**What it does:** Validate code, run tests, analyze structure, and get code review recommendations

**Where to access:**
- **Project Detail Page** → "Analysis" tab
- **Project Detail Page** → "Quick Actions" → "Analyze" button
- Direct URL: `/projects/{projectId}/analysis`

**Analysis types:**
- **Validation** - Check code for issues and style violations
- **Tests** - Run test suites and check coverage
- **Structure** - Analyze code organization and complexity
- **Review** - Get AI-powered code review findings
- **Overview** - Dashboard with all metrics and recommendations

---

### 5. Account Security
**What it does:** Secure your account with password management and two-factor authentication

**Where to access:**
- **Settings** → "Security" tab

**Security features:**
- **Password Management**
  - Change password with strength validation
  - Requirements: 8+ chars, uppercase, digit

- **Two-Factor Authentication**
  - Setup 2FA with authenticator apps
  - QR code scanning
  - Backup codes for account recovery
  - Disable 2FA anytime

- **Session Management**
  - View all active sessions
  - See device, IP, and login time
  - Revoke any session remotely

---

### 6. Advanced Analytics
**What it does:** Track project progress over time and export analytics reports

**Where to access:**
- **Analytics Page** (when integrated)
- **Project Detail Page** → Analytics link

**Analytics features:**
- **Trends Chart** - Line/bar charts of project metrics over time
  - Maturity progress
  - Code quality trend
  - Test coverage growth
  - Documentation completion

- **Export Options**
  - **PDF** - Formatted report with charts
  - **CSV** - Raw data for spreadsheet analysis
  - **JSON** - Complete data for integration

- **Time Periods**
  - Last 7 days
  - Last 30 days
  - Last 90 days
  - Last year

---

## 📊 Feature Comparison Matrix

| Feature | Backend Ready | Frontend Ready | Fully Integrated |
|---------|---------------|----------------|------------------|
| GitHub Integration | ✅ | ✅ | ✅ |
| Knowledge Base | ✅ | ✅ | ✅ |
| LLM Management | ✅ | ✅ | ✅ |
| Project Analysis | ✅ | ✅ | ✅ |
| Account Security | ✅ | ✅ | ✅ |
| Advanced Analytics | ✅ | ✅ | ✅ |

---

## 🗺️ Navigation Map

### Sidebar (Left Menu)
```
Dashboard
Projects
Dialogue
Code Generation
Knowledge Base ← NEW
Analytics
Collaboration
Documentation
Settings
```

### Settings Page Tabs
```
Account
  - Subscription tier
  - Account info
  - Quick security actions

Preferences
  - Theme (dark/light)
  - Default settings
  - Notifications

LLM Providers ← NEW
  - Current configuration
  - Provider cards
  - API key management
  - Usage statistics

Security ← NEW
  - Change password
  - 2FA setup
  - Active sessions

Subscription
  - Current plan
  - Plan options
  - Billing info

API Keys
  - Generate new keys
  - Manage existing keys

Developer (hidden by default)
  - Testing mode toggle
```

### Project Detail Tabs
```
Overview
  - Phase information
  - Created/updated dates

GitHub ← NEW
  - Sync status widget
  - Pull/Push/Sync actions
  - Link repository button

Analysis ← NEW
  - Analysis overview
  - Five analysis tabs
  - Recommendations

Team
  - Team members
  - Member roles

Settings
  - Project configuration
```

### Projects Page
```
Header Actions:
  - "Import from GitHub" ← NEW
  - "New Project"

Filter Options:
  - All Projects
  - Active Projects
  - Archived Projects

Search:
  - Search by name or description
```

---

## 🔐 Security Best Practices

### When Using GitHub Integration
- ✅ Authenticate via OAuth (coming soon)
- ✅ Review repository permissions before importing
- ✅ Keep local changes synced to avoid conflicts

### When Managing API Keys
- ✅ Never share API keys in chat or comments
- ✅ Rotate keys periodically
- ✅ Only store minimal required keys locally
- ✅ Use project-specific keys when possible

### When Using 2FA
- ✅ Save backup codes in secure location
- ✅ Test 2FA setup immediately
- ✅ Use authenticator app (not SMS if available)
- ✅ Disable old devices before losing access

---

## ⚡ Keyboard Shortcuts (Coming Soon)

| Shortcut | Action |
|----------|--------|
| `K` | Knowledge base search |
| `G` | GitHub quick sync |
| `S` | Settings |
| `?` | Help menu |

---

## 🐛 Troubleshooting

### Knowledge Base Not Showing Documents
**Solution:** Refresh the page and check that documents imported successfully

### GitHub Sync Failing
**Solution:** Verify API key has repository access permissions

### LLM Not Switching
**Solution:** Ensure new provider has valid API key configured

### Analytics Not Loading
**Solution:** Project must have activity to generate trends

### 2FA Not Working
**Solution:**
1. Verify time is synced on authenticator device
2. Try with backup codes
3. Disable and re-enable 2FA

---

## 📞 Support Resources

- **API Docs:** `/docs` (Swagger UI)
- **ReDoc Docs:** `/redoc` (HTML documentation)
- **GitHub Issues:** Report bugs and feature requests
- **Documentation:** `/docs` folder in repository

---

## 🎓 Learning Resources

### Getting Started Videos
- [ ] GitHub Integration tutorial
- [ ] Knowledge Base setup guide
- [ ] LLM provider configuration
- [ ] Project analysis walkthrough

### Best Practices
- [ ] Organizing your knowledge base
- [ ] Optimizing code for analysis
- [ ] Using analytics for project planning
- [ ] Security hardening guide

---

## 📋 Implementation Checklist

Before deploying to production, verify:

### Testing
- [ ] All sidebar links navigate correctly
- [ ] All Settings tabs render properly
- [ ] All Project Detail tabs work
- [ ] GitHub import modal displays
- [ ] Analytics export downloads files
- [ ] Modal close/dismiss buttons work
- [ ] Error states display correctly
- [ ] Loading states show spinners
- [ ] Dark mode works for all components
- [ ] Mobile responsive layout works

### API Integration
- [ ] All endpoints are accessible
- [ ] CORS is properly configured
- [ ] Error handling works
- [ ] Loading states are shown
- [ ] Data persists correctly

### Performance
- [ ] Page load times acceptable
- [ ] Charts render smoothly
- [ ] Search is responsive
- [ ] Modal animations smooth

### Security
- [ ] API keys are masked in UI
- [ ] Passwords validated properly
- [ ] 2FA codes expire correctly
- [ ] Session revocation works
- [ ] CSRF tokens working

---

**Last Updated:** 2025-12-19
**Version:** 1.0 - Complete Feature Set
