# Socratic RAG Enhanced - Master Plan v2.0

**Project Version:** 7.3.0
**Plan Version:** 2.1 (Strategic Pivot - Test After Completion)
**Last Updated:** October 14, 2025
**Status:** Phase A Complete, Phase B Ready to Start, Phase D Added

---

## 📋 EXECUTIVE SUMMARY

### Current Status (October 14, 2025)
- **Phase A (Backend):** ✅ 100% COMPLETE
- **Phase B (UI Rebuild):** Ready to Start (0% complete)
- **Phase C (Extensions):** Planned after Phase B
- **Phase D (Integration Tests):** NEW - Deferred for efficiency
- **Strategic Decision:** Test-after-completion approach

### Critical Achievements ✅
1. Session Persistence - Complete
2. Specification Persistence - Complete
3. Conflict Persistence - Complete
4. Context Persistence - Complete
5. Authorization System - Complete
6. Backend Cleanup - Complete
7. Repository Pattern - Fully Implemented
8. Unit Tests - 98.5% Passing (64/65)

### Strategic Decision: Test-After-Completion ⚠️
**Decision Made:** October 14, 2025
- Integration testing (original Task 7) DEFERRED to Phase D
- **Reason:** Avoid redundant test rewrites as features evolve
- Phase B (UI) will define real API surface
- Phase C (Extensions) will change architecture significantly
- Comprehensive testing after completion is more cost-efficient
- **Critical Rule:** Check facts, not assumptions; avoid greedy behavior

### Active Development Path (OPTIMAL ORDER)
1. ✅ Phase A - Backend (COMPLETE)
2. ⏳ Phase B - Extensions (133-181 hours) ← **CURRENT**
   - C6: Architecture Optimizer FIRST (prevents waste)
   - C2, C1, C4, C3, C5 in that order
3. 📋 Phase C - Complete UI Rebuild (30-40 hours)
   - Build UI last with all features known
4. 📋 Phase D - Integration Testing (4-6 hours)
   - Test complete system as built

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

## 🚀 PHASE B: EXTENSIONS (OPTIMAL PRIORITY ORDER)

### Overview
**Duration:** 133-181 hours (includes new C6 Architecture Optimizer)
**Status:** Ready to start
**Strategy:** Build extensions FIRST with C6 preventing waste, then UI last

### Priority Order Rationale
1. **C6 First** - Prevents greedy algorithms in all subsequent work
2. **C2 Second** - Quick win (5-7h), builds momentum
3. **C1 Third** - Chat mode with C6 validation (12-17h)
4. **C4 Fourth** - Multi-IDE with C6 design review (29-38h)
5. **C3 Fifth** - Multi-LLM with C6 optimization (21-27h)
6. **C5 Last** - Document complete, optimized system (10-15h)

### Why Extensions Before UI
- Extensions define final API surface
- UI built once for complete system = No rework
- C6 optimizes all subsequent extensions
- Estimated savings: 14-21 hours of UI rework + 20-40 hours prevented by C6

---

## 🆕 EXTENSION REQUIREMENTS ANALYSIS

### NEW Requirement F: Architecture Optimizer Agent ⭐ **HIGHEST PRIORITY**
**Status:** ❌ NOT CURRENTLY POSSIBLE
**Current Limitation:** System has NO meta-level optimization or greedy algorithm prevention
**Impact:** CRITICAL - Causes waste and technical debt across ALL projects

**What's Missing:**
1. No global cost analysis (only local optimization)
2. No greedy algorithm detection in design decisions
3. No architecture pattern validation
4. No TCO (Total Cost of Ownership) calculation
5. No design trade-off analysis
6. Questions are narrow and don't explore full problem space

**Problem Examples:**
- Socratic questions don't catch missing requirements (greedy questioning)
- Designs optimize locally, not globally (e.g., choose MongoDB without considering relations)
- No validation of architecture against best practices
- Users make decisions without seeing alternatives
- Technical debt accumulates unchecked

**Implementation Required:**
```
1. Core Optimizer Agent (15-20 hours)
   - Global cost analysis algorithms
   - Greedy pattern detection
   - Anti-pattern matching
   - TCO calculation engine

2. Question Quality Analyzer (8-10 hours)
   - Validate Socratic question completeness
   - Detect narrow/greedy questioning
   - Generate supplementary questions
   - Ensure full problem space coverage

3. Design Pattern Validator (10-12 hours)
   - Common anti-pattern detection
   - Complexity analysis (cyclomatic, coupling)
   - Scalability assessment
   - Security and performance review

4. Global Cost Calculator (8-10 hours)
   - Development time estimation
   - Maintenance burden prediction
   - Technical debt calculation
   - Alternative comparison engine

5. Integration & UI (8-10 hours)
   - Hook into all agents
   - Display warnings/recommendations
   - Show cost comparisons
   - Explain reasoning

6. Testing & Docs (6-8 hours)
   - Validate optimization logic
   - Document decision criteria
   - Create example scenarios

Total: 55-70 hours
```

**Expected Benefits:**
- Prevents 20-40 hours of rework per project
- Reduces technical debt by 40-60%
- Catches design flaws before coding
- Validates requirements completeness
- **ROI: Saves more time than it costs**

**Why Build This FIRST:**
- Will optimize C2, C1, C4, C3 as they're built
- Prevents greedy decisions in subsequent extensions
- Foundation for intelligent system behavior
- Critical for avoiding waste going forward

---

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

## 📊 COMPLETE ROADMAP (UPDATED WITH OPTIMAL ORDER)

### Phase A: Backend Completion ✅ COMPLETE
**Status:** 100% complete
**Achievements:**
- All persistence systems working
- Authorization implemented
- Repository pattern fully functional
- Unit tests 98.5% passing

### Phase B: Extensions (133-181 hours) ← **CURRENT PHASE**
**Priority:** CRITICAL (build features before UI)
**Blocked By:** NOTHING - Ready to start!

**Optimal Order:**

#### C6: Architecture Optimizer Agent (55-70 hours) ⭐ **BUILD FIRST**
- [ ] C6.1: Core optimizer agent (15-20h)
- [ ] C6.2: Question quality analyzer (8-10h)
- [ ] C6.3: Design pattern validator (10-12h)
- [ ] C6.4: Global cost calculator (8-10h)
- [ ] C6.5: Integration & UI (8-10h)
- [ ] C6.6: Testing & documentation (6-8h)

**Why First:** Prevents greedy algorithms and waste in ALL subsequent work

#### C2: Solo Project Mode (5-7 hours)
- [ ] Solo mode detection (2-3h)
- [ ] UI adjustments (3-4h)

**Why Second:** Quick win after C6, builds momentum

#### C1: Direct LLM Chat Mode (12-17 hours)
- [ ] New ChatAgent implementation (5-7h)
- [ ] Chat UI component (4-6h)
- [ ] Context extraction from chat (3-4h)

**Why Third:** C6 validates chat mode design

#### C4: Multiple IDE Support (29-38 hours)
- [ ] IDE abstraction layer (6-8h)
- [ ] LSP integration (8-10h)
- [ ] IDE detection (3-4h)
- [ ] PyCharm provider (6-8h)
- [ ] JetBrains generic (6-8h)

**Why Fourth:** Complex feature, C6 ensures good design

#### C3: Multiple LLM Providers (21-27 hours)
- [ ] LLM abstraction layer (8-10h)
- [ ] Provider management (4-5h)
- [ ] Agent updates (6-8h)
- [ ] Provider UI (3-4h)

**Why Fifth:** Complex architecture, C6 optimizes design

#### C5: Documentation (10-15 hours)
- [ ] New feature documentation (4-6h)
- [ ] Extension guides (4-6h)
- [ ] Migration documentation (2-3h)

**Why Last:** Document complete, optimized system

### Phase C: Complete UI Rebuild (30-40 hours)
**Priority:** HIGH
**Blocked By:** Phase B completion
**Strategy:** Build UI once with ALL features known

- [ ] Authentication UI (6-8h)
- [ ] Project Management UI (8-10h)
- [ ] Socratic & Chat UI (8-10h)
- [ ] Code & Documentation UI (8-12h)

**Benefits:**
- One design iteration (no rework)
- All extensions integrated from start
- Consistent UX across all features

### Phase D: Comprehensive Integration Testing (4-6 hours)
**Priority:** MEDIUM
**Blocked By:** Phase C completion
**Strategy:** Test complete system as built

- [ ] End-to-end workflow tests (2-3h)
- [ ] Authorization tests (1h)
- [ ] Performance baseline (1-2h)

---

## 📋 ESTIMATED TIMELINES (UPDATED)

### Optimal Development Path
```
Phase A: Backend         ✅ COMPLETE
Phase B: Extensions      133-181 hours (17-23 weeks part-time)
Phase C: UI Rebuild      30-40 hours   (4-5 weeks part-time)
Phase D: Integration     4-6 hours     (1 week part-time)
─────────────────────────────────────────────────────────
Total Remaining:         167-227 hours (22-29 weeks part-time)
```

### Phase B Extension Priorities (UPDATED ORDER)
```
1. C6: Architecture Optimizer (55-70h) ⭐ PREVENTS WASTE
2. C2: Solo Mode (5-7h) - Quick win
3. C1: Chat Mode (12-17h) - UX improvement
4. C4: Multi-IDE (29-38h) - Tool flexibility
5. C3: Multi-LLM (21-27h) - Provider flexibility
6. C5: Documentation (10-15h) - Complete docs
```

### Time Savings from Optimal Order
```
Old Approach (UI first):
- UI initial build:       25-35h
- Extensions:             77-99h
- UI rework for extensions: +19-26h
- Total:                  121-160h

New Approach (Extensions first with C6):
- C6 optimizer:           55-70h
- Other extensions:       78-111h
- UI (one build):         30-40h
- Total:                  163-221h

But C6 prevents:          -20-40h waste
Net total:                143-181h

SAVINGS: 20-40 hours + higher quality code
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

## 🚀 NEXT SESSION GUIDE (UPDATED)

### Immediate Actions (Next Session)

**Session 1: Start Phase B - C6 Architecture Optimizer (8-10 hours)**
1. C6.1: Design core optimizer algorithms
   - Global cost analysis framework
   - Greedy pattern detection logic
   - TCO calculation formulas

2. C6.2: Question quality analyzer basics
   - Parse Socratic question history
   - Identify coverage gaps
   - Generate supplementary questions

3. Document C6 architecture and integration points
4. Update TODO with C6 progress

**Why Start with C6:**
- Foundation for all subsequent work
- Prevents waste in C2, C1, C4, C3
- Critical for avoiding greedy algorithms
- ROI: Saves more time than it costs

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

**END OF MASTER PLAN v2.1**

**Status:** Phase A ✅ Complete, Phase B Ready (Extensions First), Phase C & D Planned
**Total Estimated Remaining:** 167-227 hours (Phases B+C+D)
**Critical Path:** Phase B Extensions (C6→C2→C1→C4→C3→C5) → Phase C UI → Phase D Tests
**Key Innovation:** C6 Architecture Optimizer prevents greedy algorithms systemwide
**Strategic Benefit:** Extensions→UI→Tests order saves 20-40 hours + higher quality
