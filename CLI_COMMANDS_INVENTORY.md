# Complete CLI Commands Inventory

**Total CLI Commands: 42+ commands across 23 files**
**Status**: 50% wired to API (42 implemented), 50% missing API endpoints

---

## ALL 42+ CLI COMMANDS - COMPLETE LIST

### PROJECT MANAGEMENT (11 commands)
**File**: `socratic_system/ui/commands/project_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 1 | `project create` | ✅ API ready | `POST /projects` | Create new project with type selection |
| 2 | `project load` | ❌ No API | - | Load project from list |
| 3 | `project list` | ✅ API ready | `GET /projects` | List user's projects |
| 4 | `project archive` | ✅ API ready | `DELETE /projects/{id}` | Soft delete project |
| 5 | `project restore` | ✅ API ready | `POST /projects/{id}/restore` | Restore archived project |
| 6 | `project delete` | ✅ API ready | `DELETE /projects/{id}` | Permanent delete |
| 7 | `project analyze` | ✅ API ready | `POST /analysis/structure` | Code analysis |
| 8 | `project test` | ✅ API ready | `POST /analysis/test` | Run project tests |
| 9 | `project fix` | ✅ API ready | `POST /analysis/fix` | Apply automated fixes |
| 10 | `project validate` | ✅ API ready | `POST /analysis/validate` | Validate project |
| 11 | `project review` | ✅ API ready | `POST /analysis/review` | Code review |

---

### SESSION/CHAT (5 commands)
**File**: `socratic_system/ui/commands/session_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 12 | `chat` | ✅ API ready | `GET /projects/{id}/chat/question` | Interactive session with Socratic/direct modes |
| 13 | `done` | ✅ API ready | `POST /projects/{id}/chat/done` | Finish interactive session (NEW) |
| 14 | `advance` | ✅ API ready | `PUT /projects/{id}/phase` | Advance project phase |
| 15 | `mode` | ✅ API ready | `PUT /projects/{id}/chat/mode` | Switch Socratic/direct mode |
| 16 | `hint` | ✅ API ready | `GET /projects/{id}/chat/hint` | Get hint for question |

---

### USER MANAGEMENT (6 commands)
**File**: `socratic_system/ui/commands/user_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 17 | `user login` | ✅ API ready | `POST /auth/login` | Login to account |
| 18 | `user create` | ✅ API ready | `POST /auth/register` | Create new account |
| 19 | `user logout` | ✅ API ready | `POST /auth/logout` | Logout current user |
| 20 | `user archive` | ❌ No API | - | Archive user account |
| 21 | `user delete` | ✅ API ready | `DELETE /auth/me` | Delete user account |
| 22 | `user restore` | ❌ No API | - | Restore archived account |

---

### CODE GENERATION (2 commands)
**File**: `socratic_system/ui/commands/code_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 23 | `code generate` | ✅ API ready | `POST /code/{id}/generate` | Generate code |
| 24 | `code docs` | ❌ No API | - | Generate documentation |

---

### COLLABORATION (4 commands)
**File**: `socratic_system/ui/commands/collab_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 25 | `collab add` | ✅ API ready | `POST /projects/{id}/collaborators` | Add team member |
| 26 | `collab remove` | ✅ API ready | `DELETE /projects/{id}/collaborators/{user}` | Remove team member |
| 27 | `collab list` | ✅ API ready | `GET /projects/{id}/collaborators` | List team members |
| 28 | `collab role` | ✅ API ready | `PUT /projects/{id}/collaborators/{user}/role` | Change role |

---

### DOCUMENTATION/KNOWLEDGE (5 commands)
**File**: `socratic_system/ui/commands/doc_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 29 | `docs import` | ✅ API ready | `POST /knowledge/import/file` | Import single file |
| 30 | `docs import-dir` | ❌ No API | - | Import directory recursively |
| 31 | `docs paste` | ✅ API ready | `POST /knowledge/import/text` | Import text content |
| 32 | `docs import-url` | ✅ API ready | `POST /knowledge/import/url` | Import from URL |
| 33 | `docs list` | ✅ API ready | `GET /knowledge/documents` | List documents |

---

### SYSTEM/CONTROL (10 commands)
**File**: `socratic_system/ui/commands/system_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 34 | `help` | ❌ No API | - | Show available commands |
| 35 | `exit` | ❌ No API | - | Exit application |
| 36 | `back` | ❌ No API | - | Go back to previous context |
| 37 | `menu` | ❌ No API | - | Return to main menu |
| 38 | `status` | ❌ No API | - | Show system status |
| 39 | `clear` | ❌ No API | - | Clear screen |
| 40 | `prompt` | ❌ No API | - | Show current context |
| 41 | `info` | ❌ No API | - | Show system info |
| 42 | `nlu enable` | ❌ No API | - | Enable NLU commands |
| 43 | `nlu disable` | ❌ No API | - | Disable NLU commands |

---

### PROJECT FINALIZATION (2 commands)
**File**: `socratic_system/ui/commands/finalize_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 44 | `finalize generate` | ❌ No API | - | Generate final artifacts |
| 45 | `finalize docs` | ❌ No API | - | Generate final documentation |

---

### GITHUB INTEGRATION (4 commands)
**File**: `socratic_system/ui/commands/github_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 46 | `github import` | ✅ API ready | `POST /github/import` | Import repository |
| 47 | `github pull` | ✅ API ready | `POST /github/projects/{id}/pull` | Pull latest changes |
| 48 | `github push` | ✅ API ready | `POST /github/projects/{id}/push` | Push changes |
| 49 | `github sync` | ✅ API ready | `POST /github/projects/{id}/sync` | Sync bidirectional |

---

### ANALYTICS/MATURITY (10 commands)
**File**: `socratic_system/ui/commands/analytics_commands.py` + `maturity_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 50 | `analytics analyze` | ✅ API ready | `GET /analytics/projects/{id}` | Category analysis |
| 51 | `analytics recommend` | ✅ API ready | `POST /analytics/recommend` | AI recommendations |
| 52 | `analytics trends` | ✅ API ready | `GET /analytics/trends` | Maturity trends |
| 53 | `analytics summary` | ✅ API ready | `GET /analytics/summary` | Analytics overview |
| 54 | `analytics breakdown` | ❌ No API | - | Detailed breakdown |
| 55 | `analytics status` | ❌ No API | - | Analytics status |
| 56 | `maturity` | ✅ API ready | `GET /projects/{id}/maturity` | Phase maturity breakdown |
| 57 | `maturity summary` | ✅ API ready | `GET /projects/{id}/maturity` | Maturity overview |
| 58 | `maturity history` | ✅ API ready | `GET /projects/{id}/maturity/history` | Maturity timeline (NEW) |
| 59 | `maturity status` | ✅ API ready | `GET /projects/{id}/maturity/status` | Phase completion status (NEW) |

---

### NOTE MANAGEMENT (4 commands)
**File**: `socratic_system/ui/commands/note_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 60 | `note add` | ❌ No API | - | Add project note |
| 61 | `note list` | ❌ No API | - | List notes |
| 62 | `note search` | ❌ No API | - | Search notes |
| 63 | `note delete` | ❌ No API | - | Delete note |

---

### DIRECT QUERY (3 commands)
**File**: `socratic_system/ui/commands/query_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 64 | `ask` | ❌ No API | - | Ask direct question (non-Socratic) |
| 65 | `explain` | ❌ No API | - | Explain concept |
| 66 | `search` | ✅ API ready | `GET /knowledge/search` | Search knowledge base |

---

### CONVERSATION (2 commands)
**File**: `socratic_system/ui/commands/conv_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 67 | `conv search` | ❌ No API | - | Search conversation history |
| 68 | `conv summary` | ❌ No API | - | Summarize conversation |

---

### PROJECT STATISTICS (3 commands)
**File**: `socratic_system/ui/commands/stats_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 69 | `project stats` | ✅ API ready | `GET /projects/{id}/stats` | Project statistics |
| 70 | `project progress` | ❌ No API | - | Update progress percentage |
| 71 | `project status` | ❌ No API | - | Set project status |

---

### SUBSCRIPTION (5 commands + 1 HIDDEN)
**File**: `socratic_system/ui/commands/subscription_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 72 | `subscription status` | ❌ No API | - | Show subscription tier |
| 73 | `subscription upgrade` | ❌ No API | - | Upgrade subscription |
| 74 | `subscription downgrade` | ❌ No API | - | Downgrade subscription |
| 75 | `subscription compare` | ❌ No API | - | Compare tiers |
| 76 | `subscription testing-mode` | ⚠️ Special | - | **HIDDEN: Enable/disable testing mode** |

---

### LLM MANAGEMENT (1 command family)
**File**: `socratic_system/ui/commands/llm_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 77 | `llm` | ⚠️ Partial | `GET /llm/config` | Multi-subcommand LLM manager |

---

### DEBUG COMMANDS (3 commands)
**File**: `socratic_system/ui/commands/debug_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 78 | `debug` | ❌ No API | - | Toggle debug mode |
| 79 | `logs` | ❌ No API | - | View recent logs |
| 80 | `debug status` | ❌ No API | - | Show debug info |

---

### KNOWLEDGE MANAGEMENT (8 commands)
**File**: `socratic_system/ui/commands/knowledge_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 81 | `knowledge add` | ❌ No API | - | Add knowledge entry |
| 82 | `knowledge list` | ❌ No API | - | List knowledge entries |
| 83 | `knowledge search` | ❌ No API | - | Search knowledge |
| 84 | `knowledge export` | ❌ No API | - | Export knowledge to JSON |
| 85 | `knowledge import` | ❌ No API | - | Import knowledge from JSON |
| 86 | `knowledge remove` | ❌ No API | - | Remove knowledge entry |
| 87 | `remember` | ❌ No API | - | Quick remember shortcut |

---

### SKILLS MANAGEMENT (2 commands)
**File**: `socratic_system/ui/commands/skills_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 88 | `skills set` | ❌ No API | - | Set team member skills |
| 89 | `skills list` | ❌ No API | - | List team skills |

---

### MODEL SWITCHING (1 command)
**File**: `socratic_system/ui/commands/model_commands.py`

| # | Command | Status | API Endpoint | Notes |
|---|---------|--------|--------------|-------|
| 90 | `model` | ⚠️ Partial | `GET /llm/config` | Switch Claude model at runtime |

---

## SPECIAL FEATURES

### 1. TESTING-MODE (HIDDEN COMMAND)

**Command**: `subscription testing-mode <on|off>`
**Location**: `socratic_system/ui/commands/subscription_commands.py` (lines 263-322)
**Visibility**: HIDDEN (not shown in help)

**Purpose**: Enable/disable testing mode to bypass all monetization restrictions

**How It Works**:
1. User runs: `/subscription testing-mode on`
2. Sets `user.testing_mode = True` flag in database
3. All subscription restrictions are bypassed for user
4. User gets full access to all premium features

**When Enabled (Testing Mode)**:
- ✅ Unlimited projects (normally 1-10 based on tier)
- ✅ Unlimited team members
- ✅ Unlimited questions per month
- ✅ All LLM models available (Opus, Sonnet, Haiku)
- ✅ All features unlocked
- ✅ No cost tracking

**Implementation Details**:
- Flag stored in User database model
- Checked in `SubscriptionChecker.check_command_access()`
- Can be toggled on/off at any time
- User-specific flag (each user has independent setting)

**Frontend Integration Needed**:
- Add UI toggle for testing mode (likely in settings or admin panel)
- Show indicator when testing mode is active
- Require password/confirmation to toggle
- Track state in auth store (testing_mode flag)

**API Endpoint**: Should map to `PUT /auth/me/testing-mode` (already exists!)

---

### 2. PRE-SESSION CHAT FEATURE

**Feature Type**: NLU-Enabled Guidance System (integrated into chat flow)
**Location**: `socratic_system/ui/commands/session_commands.py` (ChatCommand class)

**How It Works**:
1. User logs in and is in "pre-session" state (no project loaded)
2. User can run `/chat` command WITHOUT loading a project first
3. System provides guided navigation through NLU interface
4. Features:
   - Natural language command interpretation (if NLU enabled)
   - Helps user understand system capabilities
   - Suggests available actions
   - Guides toward creating/loading a project
   - Can answer general questions about the system

**Components**:

**A. Automatic Knowledge Base Loading** (when entering chat):
- Function: `_auto_load_project_files()` (lines 466-506)
- Auto-loads files from project into knowledge base
- Uses `ProjectFileLoader` agent
- Shows progress and success metrics
- Up to 50 files, priority-based loading

**B. Insight Extraction & Confirmation** (lines 20-52):
- In direct mode, Claude extracts insights before saving
- Interactive confirmation dialog
- Four insight categories:
  1. **goals** - What user is trying to accomplish
  2. **requirements** - What needs to be built/analyzed
  3. **tech_stack** - Technology and tools involved
  4. **constraints** - Limitations and restrictions
- User can: accept, reject, explain, or provide custom insights

**C. NLU Integration**:
- Commands: `/nlu enable` and `/nlu disable`
- When enabled: understands plain English instead of just slash commands
- Example: "Create a new project" instead of `/project create`
- Helps guide users who don't know all the CLI commands

**Current Behavior in CLI**:
- User lands in pre-session state after login
- Can run `/chat` to start interactive session
- System loads project context automatically
- NLU helps interpret natural language guidance requests
- Extracts and confirms insights from conversation

**Frontend Integration Needed**:
1. **Pre-Login Chat Widget**:
   - After registration/login, show guidance chat
   - Allow user to ask "What can I do?"
   - Suggest next steps
   - Guide toward project creation

2. **NLU Chatbot**:
   - Add chat interface separate from project-specific chat
   - Use `/chat` endpoint for general guidance
   - Show available actions and capabilities
   - Help users understand the system

3. **Insight Extraction Modal**:
   - When user is in direct mode, show insights confirmation
   - Allow user to review extracted insights
   - Edit or provide custom insights
   - Save insights to project context

**API Endpoints Needed**:
- `POST /projects/{id}/chat/message` - Can use existing for pre-session guidance
- New endpoint could be: `POST /chat/guidance` - General system guidance without project

---

## MISSING ENDPOINT COUNT BY CATEGORY

| Category | Total | Implemented | Missing | % Implemented |
|----------|-------|-------------|---------|----------------|
| Project Management | 11 | 10 | 1 | 91% |
| Session/Chat | 5 | 5 | 0 | 100% ✅ **PHASE 1 COMPLETE** |
| User Management | 6 | 4 | 2 | 67% |
| Code Generation | 2 | 1 | 1 | 50% |
| Collaboration | 4 | 4 | 0 | 100% |
| Documentation | 5 | 4 | 1 | 80% |
| System/Control | 10 | 0 | 10 | 0% |
| Finalization | 2 | 0 | 2 | 0% |
| GitHub | 4 | 4 | 0 | 100% |
| Analytics/Maturity | 10 | 8 | 2 | 80% |
| Notes | 4 | 0 | 4 | 0% |
| Query | 3 | 1 | 2 | 33% |
| Conversation | 2 | 0 | 2 | 0% |
| Statistics | 3 | 1 | 2 | 33% |
| Subscription | 5 | 0 | 5 | 0% |
| LLM Management | 1 | 1 | 0 | 100% |
| Debug | 3 | 0 | 3 | 0% |
| Knowledge | 8 | 0 | 8 | 0% |
| Skills | 2 | 0 | 2 | 0% |
| Model Switching | 1 | 1 | 0 | 100% |
| **TOTAL** | **~90** | **46** | **~44** | **51%** |

---

## THE 42 MISSING COMMANDS (NOT YET WIRED TO API)

### By Priority

**CRITICAL (5 commands - 5 COMPLETED)**
1. ✅ `chat` - Interactive session with guidance (GET /projects/{id}/chat/question)
2. ✅ `done` - Finish session (POST /projects/{id}/chat/done)
3. ✅ `ask` - Direct questions (POST /projects/{id}/chat/message mode=direct)
4. ✅ `maturity history` - Timeline tracking (GET /projects/{id}/maturity/history)
5. ✅ `maturity status` - Phase completion (GET /projects/{id}/maturity/status)

**HIGH (10 commands)**
1. `docs import-dir` - Batch file import
2. `code docs` - Generate documentation
3. `finalize generate` - Final artifacts
4. `finalize docs` - Final documentation
5. `note add` - Add notes
6. `note list` - List notes
7. `note search` - Search notes
8. `note delete` - Delete notes
9. `conv search` - Search conversations
10. `conv summary` - Summarize chats

**MEDIUM (12 commands)**
1. `help` - System help
2. `exit` - Application exit
3. `back` - Navigation
4. `menu` - Main menu
5. `status` - System status
6. `clear` - Clear screen
7. `prompt` - Show context
8. `info` - System info
9. `nlu enable` - Enable NLU
10. `nlu disable` - Disable NLU
11. `analytics breakdown` - Analytics detail
12. `analytics status` - Analytics status

**MEDIUM (10 more)**
1. `subscription status` - Show tier
2. `subscription upgrade` - Upgrade plan
3. `subscription downgrade` - Downgrade plan
4. `subscription compare` - Compare tiers
5. `subscription testing-mode` - **Testing access (HIDDEN)**
6. `user archive` - Archive account
7. `user restore` - Restore account
8. `explain` - Explain concepts
9. `search` - General search
10. `knowledge add` - Add knowledge

**LOW (5 commands)**
1. `knowledge list` - List knowledge
2. `knowledge search` - Search knowledge
3. `knowledge export` - Export knowledge
4. `knowledge import` - Import knowledge
5. `knowledge remove` - Remove knowledge

**VERY LOW (2-3 commands)**
1. `skills set` - Set skills
2. `skills list` - List skills
3. `project progress` - Update progress
4. `project status` - Set status

---

## IMPLEMENTATION PRIORITY ROADMAP

### Phase 1: Critical Session Features (Days 1-2)
- [x] Wire `chat` command for guided pre-session chat - GET /projects/{id}/chat/question
- [x] Add `done` command to finish sessions - POST /projects/{id}/chat/done (NEW)
- [x] Add `ask` command for direct questions - POST /projects/{id}/chat/message with mode=direct
- [x] Add maturity history and status endpoints - GET /projects/{id}/maturity/history, /status (NEW)

### Phase 2: Important Features (Days 3-5)
- [x] Wire all note commands (add, list, search, delete) - NEW endpoints created
- [x] Add documentation generation - POST /projects/{id}/docs/generate (NEW)
- [x] Add conversation search/summary - GET/POST endpoints already exist (from Phase 1)
- [ ] Add finalization commands - Generate and docs endpoints needed

### Phase 3: System Commands (Days 6-7)
- [ ] Add system control commands (help, exit, menu, etc.)
- [ ] Add NLU enable/disable
- [ ] Add debug commands
- [ ] Add subscription and testing-mode endpoints

### Phase 4: Knowledge & Skills (Days 8-10)
- [ ] Wire all knowledge management commands
- [ ] Add skills management
- [ ] Add remaining analytics features
- [ ] Add project progress/status tracking

---

*This inventory represents all CLI commands currently in the codebase, with detailed information about which ones have API endpoints and which ones need to be wired.*
