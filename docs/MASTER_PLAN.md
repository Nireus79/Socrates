# Socratic RAG Enhanced - Master Plan v2.0

**Project Version:** 7.3.0
**Plan Version:** 2.0 (Consolidated)
**Last Updated:** October 14, 2025
**Status:** Phase A 89% Complete, Planning Phase B & Extensions

---

## 📋 EXECUTIVE SUMMARY

### Current Status
- **Phase A (Backend Completion):** 89% complete (6.4/7 tasks)
- **Estimated Completion:** 4-5 hours remaining
- **Next Phase:** UI Rebuild (Phase B)
- **New Requirements:** 5 major feature requests identified

### Critical Achievements ✅
1. Session Persistence - Complete
2. Specification Persistence - Complete
3. Conflict Persistence - Complete
4. Context Persistence - Complete
5. Authorization System - Complete
6. Database Restructure - Complete

### Pending Work ⏳
1. Backend Cleanup (2 hours)
2. Integration Testing (2-3 hours)
3. Phase B - UI Rebuild (25-35 hours)
4. Extension Features (estimated 40-60 hours)

---

## 🏗️ CURRENT ARCHITECTURE

### System Overview
```
┌─────────────────────────────────────────────┐
│         Web Interface (Flask)               │
│  - Dashboard, Projects, Socratic Sessions   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│      Agent Orchestrator                      │
│  - Request routing & coordination            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         8 Specialized Agents                 │
│  1. UserManager      5. ContextAnalyzer      │
│  2. ProjectManager   6. DocumentProcessor    │
│  3. SocraticCounselor 7. ServicesAgent       │
│  4. CodeGenerator    8. SystemMonitor        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│    ServiceContainer (Dependency Injection)   │
│  - Config, Logging, Events, Database         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│  Database Layer + External Services          │
│  - SQLite + Repositories                     │
│  - Claude API (Anthropic only)               │
│  - ChromaDB (Vector Storage)                 │
│  - VS Code Integration (IDE only)            │
└──────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- Python 3.8+
- Flask 3.0.3 (web framework)
- SQLite (database, upgradable to PostgreSQL)
- ChromaDB (vector storage)

**AI Integration:**
- Anthropic Claude API (ONLY provider currently)
- sentence-transformers (embeddings)

**IDE Integration:**
- VS Code ONLY (no other IDEs supported)

**Platform Support:**
- ✅ Windows
- ✅ macOS
- ✅ Linux

### File Structure
```
socratic-rag-enhanced/
├── src/
│   ├── core.py              # ServiceContainer, utilities
│   ├── models.py            # 24+ data models
│   ├── database/            # Modular DB structure (17 files)
│   ├── agents/              # 8 agents + orchestrator
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── socratic.py      # ⚠️ SOCRATIC MODE ONLY
│   │   ├── code.py
│   │   ├── context.py
│   │   ├── document.py
│   │   ├── services.py
│   │   └── monitor.py
│   └── services/
│       ├── claude_service.py    # ⚠️ ANTHROPIC ONLY
│       └── ide_service.py       # ⚠️ VS CODE ONLY
├── web/
│   ├── app.py
│   └── templates/
├── tests/
├── data/
├── docs/
└── config.yaml
```

---

## 🎯 PHASE A: BACKEND COMPLETION STATUS

### Completed Tasks (6.4/7)

#### Task 1: Session Persistence ✅ (6 hours)
**Deliverables:**
- [x] SocraticSessionRepository with CRUD
- [x] QuestionRepository with session linking
- [x] ConversationMessageRepository
- [x] SocraticCounselorAgent integration
- [x] Session resume functionality
- [x] All tests passing (26/26)

#### Task 2: Specification Persistence ✅ (4 hours)
**Deliverables:**
- [x] TechnicalSpecificationRepository
- [x] Auto-versioning system (1.0.0 → 1.1.0)
- [x] CodeGeneratorAgent integration
- [x] All CRUD operations working

#### Task 3: Conflict Persistence ✅ (6 hours)
**Deliverables:**
- [x] ConflictRepository with CRUD
- [x] ContextAnalyzerAgent integration
- [x] Resolution tracking
- [x] All tests passing (19/19)

#### Task 4: Context Persistence ✅ (6 hours)
**Deliverables:**
- [x] ProjectContextRepository
- [x] ModuleContextRepository
- [x] TaskContextRepository
- [x] Cache system with refresh logic
- [x] 9 extraction methods implemented
- [x] All tests passing (26/26)

#### Task 5: Authorization System ✅ (4 hours)
**Deliverables:**
- [x] @require_authentication decorator
- [x] @require_project_access decorator
- [x] User status validation
- [x] Collaborator access control
- [x] All tests passing (11/11)

#### Task 6: Backend Cleanup ⏸️ (2 hours remaining)
**Completed:**
- [x] Analysis of backward compatibility issues
- [x] Missing repositories identified
- [x] Repository additions (Task 6.2)

**Pending:**
- [ ] Task 6.1: Remove db_service from 4 agent files (~75 min)
- [ ] Task 6.3: Standardize error responses (~30 min)
- [ ] Task 6.4: Code quality pass (~15 min)

#### Task 7: Integration Testing ⏸️ (2-3 hours)
**Status:** Not started
**Requirements:**
- [ ] End-to-end workflow tests
- [ ] Server restart persistence verification
- [ ] Authorization enforcement tests
- [ ] Performance baseline metrics

### Test Results Summary
- **Total Tests:** 64/65 passing (98.5%)
- **Context Persistence:** 26/26 ✅
- **Authorization:** 11/11 ✅
- **Conflict Persistence:** 19/19 ✅
- **Integration:** 8/9 ✅

---

## 🚀 PHASE B: UI REBUILD (PLANNED)

### Overview
**Duration:** 25-35 hours
**Status:** Planned, blocked by Phase A completion
**Strategy:** Build new UI from scratch knowing full backend capabilities

### Tasks Breakdown

#### B1: Authentication UI (8-11 hours)
- Login/Register pages
- Password reset flow
- User profile management
- Session management UI

#### B2: Project Management UI (8-10 hours)
- Project creation wizard
- Project dashboard
- Module/Task hierarchy view
- Framework selection (fix current issues)

#### B3: Socratic Session UI (8-10 hours)
- Session start/resume interface
- Role selection UI
- Question/Answer flow
- Progress tracking
- Session history view

#### B4: Code & Documentation UI (9-14 hours)
- Code generation interface
- File browser/viewer
- Documentation viewer
- Export options
- IDE sync controls

### Success Criteria
- [ ] Complete workflow possible without coding
- [ ] All backend features accessible
- [ ] Intuitive navigation
- [ ] No broken links or buttons
- [ ] Mobile responsive
- [ ] Works on all supported platforms

---

## 🆕 NEW REQUIREMENTS ANALYSIS

### Requirement A: Direct LLM Chat Mode
**Status:** ❌ NOT CURRENTLY POSSIBLE
**Current Limitation:** System only supports Socratic questioning mode
**Impact:** HIGH - User requested feature

**What's Missing:**
1. No chat interface in UI
2. SocraticCounselorAgent only does Q&A format
3. No conversation history for free-form chat
4. No mode toggle (Socratic vs Chat)

**Implementation Required:**
```
1. New ChatAgent (5-7 hours)
   - Free-form conversation handling
   - Context injection without questions
   - Project/spec updates from chat

2. Chat UI (4-6 hours)
   - Chat interface component
   - Mode toggle (Socratic/Chat)
   - Message history display

3. Context Updates (3-4 hours)
   - Extract requirements from chat
   - Update project specs live
   - Merge chat insights with Socratic data

Total: 12-17 hours
```

**Technical Approach:**
- Create new `ChatAgent` alongside SocraticCounselorAgent
- Use same Claude API but different prompt structure
- Store chat messages in `conversation_messages` table
- Add `conversation_type` field (socratic/chat)
- Update UI with mode selector

---

### Requirement B: Single-Person Project Mode
**Status:** ⚠️ PARTIALLY POSSIBLE
**Current State:** Team features exist but can work with just owner
**Impact:** MEDIUM - Better UX for solo developers

**What Exists:**
- ProjectCollaborator system (can have 0 collaborators)
- Owner-only projects work fine
- Team fields are optional

**What's Missing:**
1. No "solo mode" to hide team UI elements
2. No simplified workflow for one person
3. Team features always visible

**Implementation Required:**
```
1. Solo Mode Detection (2-3 hours)
   - Detect single-user projects
   - Hide team UI elements conditionally
   - Simplified permission checks

2. UI Adjustments (3-4 hours)
   - Conditional team sections
   - "Solo Project" badge/indicator
   - Skip team setup in wizard

Total: 5-7 hours
```

---

### Requirement C: Multiple LLM Provider Support
**Status:** ❌ NOT CURRENTLY POSSIBLE
**Current Limitation:** Hard-coded to Anthropic Claude only
**Impact:** HIGH - Vendor lock-in, flexibility needed

**What's Missing:**
1. No LLM abstraction layer
2. Hard-coded ClaudeService everywhere
3. No provider configuration
4. No provider switching

**Implementation Required:**
```
1. LLM Abstraction Layer (8-10 hours)
   - BaseLLMProvider interface
   - ClaudeProvider (refactor existing)
   - OpenAIProvider (new)
   - GeminiProvider (new)
   - LlamaProvider (local, new)

2. Provider Management (4-5 hours)
   - Provider factory pattern
   - Configuration management
   - API key management per provider

3. Agent Updates (6-8 hours)
   - Update all agents to use abstraction
   - Remove hard-coded Claude references
   - Add provider selection to config

4. UI for Provider Selection (3-4 hours)
   - Settings page for API keys
   - Provider selector
   - Cost comparison display

Total: 21-27 hours
```

**Recommended Providers:**
1. Anthropic Claude (existing)
2. OpenAI GPT-4/GPT-4-turbo
3. Google Gemini Pro
4. Local Llama models (via Ollama)

---

### Requirement D: Cross-Platform Support
**Status:** ✅ ALREADY SUPPORTED
**Current State:** Full Windows, macOS, Linux support
**Impact:** NONE - No work needed

**Evidence:**
- Documentation has Mac/Linux commands
- Uses `pathlib.Path` (cross-platform)
- No OS-specific dependencies
- SQLite works everywhere
- Python 3.8+ available on all platforms

---

### Requirement E: Multiple IDE Support
**Status:** ❌ NOT CURRENTLY POSSIBLE
**Current Limitation:** Only VS Code integration exists
**Impact:** MEDIUM - Limits developer choice

**What's Missing:**
1. Only IDEService for VS Code
2. No PyCharm support
3. No JetBrains IDE support
4. No generic IDE protocol

**Implementation Required:**
```
1. IDE Abstraction Layer (6-8 hours)
   - BaseIDEProvider interface
   - VSCodeProvider (refactor existing)
   - PyCharmProvider (new)
   - JetBrainsProvider (generic, new)

2. Language Server Protocol (8-10 hours)
   - LSP integration for generic support
   - IDE-agnostic file sync
   - Generic workspace management

3. IDE Detection (3-4 hours)
   - Auto-detect installed IDEs
   - User preference management
   - Multi-IDE support per project

4. Provider Implementations (12-16 hours)
   - PyCharm integration (6-8h)
   - JetBrains generic (6-8h)

Total: 29-38 hours
```

**Recommended IDEs:**
1. VS Code (existing)
2. PyCharm / IntelliJ IDEA
3. WebStorm
4. Generic LSP (for others)

---

## 📊 COMPLETE ROADMAP

### Phase A: Backend Completion (4-5 hours remaining)
**Priority:** CRITICAL
**Current:** 89% complete
- [ ] Task 6: Backend Cleanup (2 hours)
- [ ] Task 7: Integration Testing (2-3 hours)

### Phase B: UI Rebuild (25-35 hours)
**Priority:** HIGH
**Blocked By:** Phase A completion
- [ ] B1: Authentication UI (8-11h)
- [ ] B2: Project Management UI (8-10h)
- [ ] B3: Socratic Session UI (8-10h)
- [ ] B4: Code & Documentation UI (9-14h)

### Phase C: Extension Features (77-99 hours)
**Priority:** MEDIUM
**Blocked By:** Phase B completion

#### C1: Direct LLM Chat Mode (12-17 hours)
- [ ] New ChatAgent implementation (5-7h)
- [ ] Chat UI component (4-6h)
- [ ] Context extraction from chat (3-4h)

#### C2: Solo Project Mode (5-7 hours)
- [ ] Solo mode detection (2-3h)
- [ ] UI adjustments (3-4h)

#### C3: Multiple LLM Providers (21-27 hours)
- [ ] LLM abstraction layer (8-10h)
- [ ] Provider management (4-5h)
- [ ] Agent updates (6-8h)
- [ ] Provider UI (3-4h)

#### C4: Multiple IDE Support (29-38 hours)
- [ ] IDE abstraction layer (6-8h)
- [ ] LSP integration (8-10h)
- [ ] IDE detection (3-4h)
- [ ] PyCharm provider (6-8h)
- [ ] JetBrains generic (6-8h)

#### C5: Documentation & Testing (10-15 hours)
- [ ] New feature documentation (4-6h)
- [ ] Extension tests (4-6h)
- [ ] Migration guides (2-3h)

---

## 📋 ESTIMATED TIMELINES

### Immediate Path (Phase A + B)
```
Phase A Completion:     4-5 hours   (this week)
Phase B UI Rebuild:    25-35 hours  (2-3 weeks)
─────────────────────────────────────
Total:                 29-40 hours
```

### Full Extension Path (A + B + C)
```
Phase A Completion:     4-5 hours
Phase B UI Rebuild:    25-35 hours
Phase C Extensions:    77-99 hours
─────────────────────────────────────
Total:                106-139 hours  (13-17 weeks part-time)
```

### Feature Priority Ordering
```
1. Complete Phase A (CRITICAL - foundation)
2. Complete Phase B (HIGH - working UI needed)
3. Implement C3 (Multiple LLMs) (HIGH - flexibility)
4. Implement C1 (Chat Mode) (MEDIUM - UX improvement)
5. Implement C5 (Documentation) (MEDIUM - usability)
6. Implement C4 (Multiple IDEs) (LOW - nice to have)
7. Implement C2 (Solo Mode) (LOW - minor improvement)
```

---

## 🔧 TECHNICAL SPECIFICATIONS

### New Database Schema Changes

#### For Chat Mode (C1)
```sql
-- Add conversation_type to existing table
ALTER TABLE conversation_messages
ADD COLUMN conversation_type TEXT DEFAULT 'socratic';
-- Values: 'socratic', 'chat'

-- Add chat_sessions table
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### For Solo Mode (C2)
```sql
ALTER TABLE projects
ADD COLUMN is_solo_project BOOLEAN DEFAULT FALSE;
```

#### For Multiple Providers (C3)
```sql
CREATE TABLE provider_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    api_key TEXT,
    settings JSON,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### For IDE Support (C4)
```sql
CREATE TABLE ide_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    ide_type TEXT NOT NULL,
    ide_path TEXT,
    settings JSON,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### New Configuration Options

```yaml
# LLM Provider Configuration
llm:
  default_provider: "anthropic"

  providers:
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-sonnet-4"

    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-4-turbo"

    gemini:
      api_key: "${GEMINI_API_KEY}"
      model: "gemini-pro"

    ollama:
      base_url: "http://localhost:11434"
      model: "llama2"

# IDE Configuration
ide:
  default_ide: "vscode"

  ides:
    vscode:
      path: "code"
      enabled: true

    pycharm:
      path: "pycharm"
      enabled: true

# Chat Mode Configuration
chat:
  enabled: true
  default_mode: "socratic"
  allow_mode_switching: true

# Solo Project Configuration
solo_mode:
  enabled: true
  auto_detect: true
  hide_team_features: true
```

---

## 🎯 SUCCESS CRITERIA

### Phase A Success (Backend Complete)
- [x] All 7 tasks completed (currently 6.4/7)
- [ ] All persistence working through restart
- [ ] Authorization enforced everywhere
- [ ] 100% of tests passing
- [ ] No backward compatibility issues
- [ ] Clean, maintainable code

### Phase B Success (Working UI)
- [ ] User can create account and login
- [ ] User can create project completely
- [ ] User can run Socratic session
- [ ] User can generate code
- [ ] User can export/sync to IDE
- [ ] All features accessible via UI
- [ ] No broken workflows

### Phase C Success (Extensions)
- [ ] **C1:** User can switch between Socratic and Chat modes
- [ ] **C2:** Solo projects hide team features
- [ ] **C3:** User can choose LLM provider (4+ options)
- [ ] **C4:** User can choose IDE (3+ options)
- [ ] **C5:** Documentation covers all features

---

## 🐛 KNOWN ISSUES & LIMITATIONS

### Current Issues (Phase A)
1. Backend cleanup pending (Task 6)
2. Integration testing incomplete (Task 7)
3. Import warnings in database/agents (cosmetic)

### Architectural Limitations
1. **Hard-coded to Claude:** All agents assume Anthropic
2. **No chat mode:** Only Socratic questioning works
3. **VS Code only:** No other IDE support
4. **Team-focused UI:** Solo users see unnecessary team features

### Performance Considerations
- SQLite may struggle with 50+ concurrent users
- ChromaDB has 100K document limit practically
- Single-threaded Flask limits concurrent requests
- Consider PostgreSQL + Redis for production

---

## 🚀 NEXT SESSION GUIDE

### Immediate Actions (Next 1-2 Sessions)

**Session 1: Complete Phase A (4-5 hours)**
1. Task 6.1: Remove db_service from agents (~75 min)
2. Task 6.3-6.4: Error responses + code quality (~45 min)
3. Task 7: Integration testing (2-3 hours)
4. Update this document with Phase A completion ✅

**Session 2: Start Phase B (4-6 hours)**
1. B1: Design authentication UI
2. B1: Implement login/register pages
3. B1: Test authentication flow
4. Update TODO with progress

### Testing Commands
```bash
# After Phase A completion
pytest tests/test_integration.py

# After authentication UI
python run.py
# Test: http://localhost:5000/login

# Full test suite
pytest
```

---

**END OF MASTER PLAN v2.0**

**Status:** Phase A 89% complete, Phase B planned, Phase C specified
**Total Estimated Remaining:** 106-139 hours (all phases)
**Critical Path:** Phase A (5h) → Phase B (30h) → Phase C priorities
