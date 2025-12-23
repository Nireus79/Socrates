# Frontend Missing Features - Quick Reference

**Date:** December 19, 2025
**User Request:** Identify backend commands/functions not in frontend

---

## 12 CRITICAL MISSING FEATURES

### 1. ❌ PROJECT DELETION
- **Button Location:** ProjectsPage.tsx line 18
- **Status:** UI button only (non-functional)
- **What's Missing:**
  - Confirmation modal
  - Permanent deletion logic
  - API integration
- **Backend:** `project delete` command + DELETE /projects/{id}

### 2. ❌ ACCOUNT DELETION
- **Button Location:** SettingsPage.tsx line 150-155
- **Status:** Button with no onClick handler
- **What's Missing:**
  - Confirmation & email verification
  - Account deletion logic
  - API integration
- **Backend:** `user delete` command

### 3. ❌ PRE-SESSION NLU CHAT
- **Location:** None (doesn't exist)
- **What's Missing:**
  - Landing page with global chat
  - Natural language understanding
  - Q&A without project context
- **Backend:** ChatCommand with NLU capability

### 4. ❌ SUBSCRIPTION TESTING-MODE
- **Location:** None (doesn't exist)
- **What's Missing:**
  - Hidden testing UI
  - Tier switching
  - Monetization bypass toggle
- **Backend:** `subscription testing-mode` hidden command

### 5. ❌ GITHUB INTEGRATION
- **Pages Missing:** 4 pages
  - GitHubAuthPage (OAuth)
  - GitHubImportPage
  - GitHubSyncPage
  - GitHubPullPage
- **Commands:** `github import`, `github pull`, `github push`, `github sync`
- **Priority:** HIGH for developers

### 6. ❌ KNOWLEDGE BASE MANAGEMENT
- **Location:** None (doesn't exist)
- **What's Missing:**
  - Document import UI (files, URLs, pasted text)
  - Knowledge browser
  - Document editor
  - Full CRUD for documents
- **Commands:** 7 knowledge commands + 5 doc commands

### 7. ❌ CODE REFACTORING UI
- **Location:** CodePage.tsx (buttons exist, no logic)
- **What's Missing:**
  - Refactor type selector
  - Before/after diff viewer
  - Apply/reject functionality
- **Backend:** POST /code/refactor endpoint

### 8. ❌ MULTI-LLM PROVIDER MANAGEMENT
- **Location:** None (doesn't exist)
- **What's Missing:**
  - Provider selection UI
  - API key configuration
  - Model selection
  - Usage statistics per provider
- **Commands:** 8 llm commands

### 9. ❌ PROJECT ANALYSIS SUITE
- **Commands Missing:** 5 commands
  - `project analyze`
  - `project test`
  - `project fix`
  - `project validate`
  - `project review`
- **What's Missing:**
  - Analysis request UI
  - Results display
  - Recommendations

### 10. ❌ ACCOUNT SECURITY FEATURES
- **Location:** SettingsPage.tsx (buttons only, no logic)
- **What's Missing:**
  - Change password modal
  - 2FA setup UI
  - Session management
  - Login history
- **Priority:** MEDIUM (security)

### 11. ❌ PROJECT DIFF/COMPARISON
- **Location:** None (doesn't exist)
- **Command:** `project diff`
- **What's Missing:**
  - Project comparison page
  - Version history viewer
  - Diff viewer UI

### 12. ❌ ADVANCED STATISTICS & EXPORT
- **Location:** AnalyticsPage.tsx (partial)
- **What's Missing:**
  - Time series charts
  - Phase comparisons
  - Export to CSV/PDF
  - Detailed breakdowns
  - Predictive analytics

---

## CRITICAL ISSUE: Subscription Limit Error

**Problem:** `POST /projects` returns 500 when quota exceeded
- Should return 400 Bad Request
- Should show subscription message
- Should show upgrade CTA

**User Impact:** Users confused about endpoint failure
**Status:** Documented and noted ✓

---

## IMPLEMENTATION PRIORITY (User's Explicit Requests)

User stated: "There is no way user delete a project or an account. There is no pre session chat with nlu, there is no way /subscription testing-mode on/off command to be passed."

### IMMEDIATE (Must Have):
1. Project Deletion
2. Account Deletion
3. Subscription Testing-Mode
4. Pre-Session NLU Chat

### HIGH (Should Have):
5. GitHub Integration
6. Knowledge Base Management
7. Account Security (2FA, password reset)

### MEDIUM (Nice to Have):
8. Code Refactoring
9. LLM Provider Selection
10. Project Analysis

### LOW (Future):
11. Project Diff/Comparison
12. Advanced Analytics Export

---

## FEATURE PARITY METRICS

```
Backend Capability:       92 CLI commands + 25+ API endpoints
Frontend Implementation:  33 commands (36%) + all core endpoints ✓
Gap:                      59 commands (64%) not exposed in UI

By Category:
- 100% Complete:    Session/Chat, Code Gen, Collaboration (3 categories)
- 80%+ Complete:    Subscription (4/5), Stats (2/3)
- 50% Complete:     Analytics, Projects, Maturity, Query
- 0% Complete:      LLM, GitHub, Knowledge, Debug, System (11 categories)
```

---

## Files to Create (Minimal Implementation)

```
Minimal Frontend Gap Fix (1-2 weeks):
├── ProjectDeletionModal.tsx
├── AccountDeletionModal.tsx
├── NLUChatPage.tsx
├── TestingModePage.tsx
└── Store updates for each

Full Frontend Gap Fix (4-6 weeks):
├── All above +
├── GitHubAuthPage.tsx
├── KnowledgeBasePage.tsx
├── ProjectAnalysisPage.tsx
├── LLMProviderPage.tsx
├── AccountSecurityPage.tsx
└── Multiple store updates
```

---

## Summary

**Total Backend Features:** 92 CLI commands across 21 categories

**Implemented:** 33 features (36%)
- All core workflows ✓
- Basic CRUD operations ✓
- Authentication ✓
- Collaboration ✓

**Missing:** 59 features (64%)
- User/account management (delete, security)
- Advanced project features (analyze, test, review, diff)
- GitHub integration
- Knowledge base
- LLM provider selection
- Debug & system features

**User Must Implement:**
- Project deletion
- Account deletion
- Pre-session NLU chat
- Subscription testing-mode toggle
- GitHub integration (high impact)
- Knowledge base (high impact)

---

**Status:** READY FOR IMPLEMENTATION
**Full Analysis:** See FRONTEND_GAP_ANALYSIS.md for complete details