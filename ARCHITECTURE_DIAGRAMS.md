# Socrates Architecture Diagrams & Visual Explanations

## Diagram 1: Current Request Flow - When User Asks for a Question

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React)                               │
│                                                                         │
│  CreateProjectModal: "Python Calculator"                               │
│         ↓                                                                │
│  User clicks "Get Question"                                             │
│         ↓                                                                │
│  GET /projects/{id}/chat/question                                       │
│  Headers: {Authorization: "Bearer token"}                               │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│          BACKEND - projects_chat.py get_question()                      │
│                                                                         │
│  1. ✅ Check user is authenticated                                     │
│  2. ✅ Load project from database                                      │
│  3. ✅ Verify project has description                                  │
│  4. ✅ Extract project.description: "Python Calculator"                │
│  5. ✅ Call orchestrator.process_request(                              │
│        "socratic_counselor",                                            │
│        {                                                                │
│          "action": "generate_question",                                 │
│          "project": project,                                            │
│          "topic": "Python Calculator",  ← KEY FIX from this session   │
│          "user_id": current_user,       ← EXISTS BUT NOT USED          │
│          "force_refresh": False                                         │
│        }                                                                 │
│      )                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│      BACKEND - orchestrator.py _handle_socratic_counselor()            │
│                                                                         │
│  ❌ PROBLEM 1: user_id available but not used to fetch user's API key │
│  ❌ PROBLEM 2: Uses global self.llm_client regardless of user          │
│  ❌ PROBLEM 3: No mechanism to look up user's stored API key          │
│                                                                         │
│  Current code (line 891):                                              │
│    if counselor and self.llm_client:                                   │
│        result = counselor.process({"topic": "Python Calculator"})      │
│                       ↓                                                 │
│                    WHICH llm_client?                                   │
│                    → self.llm_client (global, from ANTHROPIC_API_KEY)  │
│                    ← Should be: user's API key if available            │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  LIBRARY - socratic_agents.SocraticCounselor.process()                 │
│                                                                         │
│  1. Receive request: {"topic": "Python Calculator"}                    │
│  2. Call self._generate_guiding_questions(topic="...", level="...")    │
│  3. Our custom subclass is used (✅ from this session)                 │
│  4. Calls self._generate_dynamic_questions()                           │
│  5. Uses self.llm_client.generate_response(prompt)                     │
│      ↓                                                                   │
│      IF llm_client is available:                                       │
│        → Call Claude with prompt about calculator                       │
│        → Claude generates context-aware questions                       │
│        → Parse response as JSON array                                   │
│        → Return ["What frameworks...", "How will...", "Consider..."]   │
│      ELSE:                                                              │
│        → Fall back to hardcoded templates                              │
│        → Return ["What do you know about {topic}?", ...]              │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  BACKEND - projects_chat.py (continued get_question())                  │
│                                                                         │
│  6. ✅ Extract question from response (from this session):             │
│     question_data = result.get("data", {})                             │
│     questions = question_data.get("questions", [])                     │
│     if questions and len(questions) > 0:                               │
│         question = questions[0].strip()  ← TAKE FIRST QUESTION         │
│                                                                         │
│  7. ✅ Return to frontend:                                             │
│     {                                                                   │
│       "status": "success",                                              │
│       "question": "How will you handle user input validation?",         │
│       "project_id": "proj_123"                                          │
│     }                                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       FRONTEND - Display Question                       │
│                                                                         │
│  ✅ Show: "How will you handle user input validation?"                 │
│  (This is Claude-generated, specific to Python Calculator project)      │
│                                                                         │
│  BUT: Questions use API quota from:                                    │
│  - If ANTHROPIC_API_KEY is set: Server's quota                        │
│  - If not set: Placeholder key, calls fail                            │
│  - User's own key: NEVER USED (Problem!)                              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Diagram 2: The API Key Problem

### What Should Happen (Ideal)

```
USER 1: Alice
  ↓
  Browser: "Here's my Claude API key: sk-ant-alice-xxxxx"
  ↓
  POST /llm/api-key?provider=anthropic&api_key=sk-ant-alice-xxxxx
  ↓
  Backend: Store in database
  ↓
  Database: INSERT INTO user_api_keys (user_id='alice', provider='anthropic', api_key='sk-ant-alice-xxxxx')
  ↓
  Later: Alice requests question
  ↓
  Backend: SELECT api_key FROM user_api_keys WHERE user_id='alice'
  ↓
  Create LLMClient with alice's key
  ↓
  Question generation uses Alice's Claude quota
  ↓
  ✅ Works correctly

USER 2: Bob
  ↓
  Browser: "Here's my Claude API key: sk-ant-bob-yyyyy"
  ↓
  POST /llm/api-key?provider=anthropic&api_key=sk-ant-bob-yyyyy
  ↓
  Backend: Store in database
  ↓
  Database: INSERT INTO user_api_keys (user_id='bob', provider='anthropic', api_key='sk-ant-bob-yyyyy')
  ↓
  Later: Bob requests question
  ↓
  Backend: SELECT api_key FROM user_api_keys WHERE user_id='bob'
  ↓
  Create LLMClient with bob's key
  ↓
  Question generation uses Bob's Claude quota
  ↓
  ✅ Works correctly
```

### What Actually Happens (Current - BROKEN)

```
USER 1: Alice
  ↓
  Browser: "Here's my Claude API key: sk-ant-alice-xxxxx"
  ↓
  POST /llm/api-key?provider=anthropic&api_key=sk-ant-alice-xxxxx
  ↓
  Frontend shows: "API Key saved!" ← LIES!
  ↓
  Backend: orchestrator.process_request(
              "multi_llm",
              {"action": "add_api_key", "api_key": "sk-ant-alice-xxxxx"}
            )
  ↓
  Orchestrator._handle_multi_llm() method:
    if action == "add_api_key":
        ❌ NO HANDLER EXISTS
        ↓
        Falls through to: else return {"status": "error", "message": "Unknown action: add_api_key"}
  ↓
  Key is LOST - never stored
  ↓
  Later: Alice requests question
  ↓
  Backend: db.get_api_key('alice', 'anthropic')
             ↓
             Method is a stub, always returns None
  ↓
  No user key found, fall back to global key
  ↓
  self.llm_client = LLMClient(api_key=os.getenv("ANTHROPIC_API_KEY"))
           ↓
           If env var is set: Uses server's API quota
           If not: Uses "placeholder-key-will-use-user-specific-keys" → FAILS
  ↓
  ❌ Alice's API key is completely ignored
  ❌ Question generation uses server's key or fails

USER 2: Bob
  ↓
  (Same as Alice - same problem)
  ↓
  ❌ Bob's API key is also ignored
```

---

## Diagram 3: Data Flow - Current vs. What's Needed

### Current Data Flow (Broken)

```
User submits API key
    ↓
Frontend: POST /llm/api-key
    ↓
Backend Router (routers/llm.py):
    ↓
orchestrator.process_request("multi_llm", {...})
    ↓
orchestrator._handle_multi_llm():
    ↓
    action = "add_api_key"
    ↓
    ❌ No handler → falls to else
    ↓
    Returns: {"status": "error", "message": "Unknown action: add_api_key"}
    ↓
API Key: LOST (never stored)
```

### What's Needed (Minimal Fix)

```
User submits API key
    ↓
Frontend: POST /llm/api-key
    ↓
Backend Router (routers/llm.py):
    ↓
orchestrator.process_request("multi_llm", {
    "action": "add_api_key",
    "user_id": "alice",
    "provider": "anthropic",
    "api_key": "sk-ant-xxxxx"
})
    ↓
orchestrator._handle_multi_llm():
    ↓
    action = "add_api_key"
    ↓
    ✅ NEW HANDLER:
    elif action == "add_api_key":
        db.save_api_key(user_id, provider, api_key)
        return {"status": "success", ...}
    ↓
Database (database.py):
    ↓
    ✅ IMPLEMENTED (not stub):
    def save_api_key(self, user_id, provider, api_key):
        INSERT OR REPLACE INTO user_api_keys (user_id, provider, api_key)
        VALUES (?, ?, ?)
    ↓
Database Table:
    ↓
    ✅ NEW TABLE:
    user_api_keys {
        user_id: "alice",
        provider: "anthropic",
        api_key: "sk-ant-xxxxx"
    }
    ↓
API Key: SAVED ✅
```

---

## Diagram 4: LLM Client Usage - Current vs. What Should Happen

### Current (Single Global Client)

```
Orchestrator.__init__():
    ↓
    api_key = os.getenv("ANTHROPIC_API_KEY")  ← Server's key or placeholder
    ↓
    self.llm_client = LLMClient(..., api_key=api_key)
    ↓
    This single client is stored in: self.llm_client
    ↓
    ∀ requests from any user:
        Use self.llm_client  ← SAME FOR ALL USERS ❌
```

### What Should Happen (Per-User Client)

```
Orchestrator._handle_socratic_counselor():
    ↓
    user_id = request_data.get("user_id")  ← Extract user
    ↓
    db.get_api_key(user_id, "anthropic")  ← Look up user's key
    ↓
    IF user_key exists:
        user_llm_client = LLMClient(..., api_key=user_key)  ← Per-user client
        counselor.llm_client = user_llm_client
    ELSE:
        counselor.llm_client = self.llm_client  ← Fallback to global
    ↓
    counselor.process({...})
    ↓
    → Uses correct API client for that user ✅
```

---

## Diagram 5: Database Schema Needed

### Current Tables (Existing)

```
users {
    username: TEXT (PRIMARY KEY),
    password_hash: TEXT,
    created_at: TIMESTAMP,
    ...
}

projects {
    id: TEXT (PRIMARY KEY),
    owner: TEXT (FOREIGN KEY → users.username),
    name: TEXT,
    description: TEXT,
    type: TEXT,
    created_at: TIMESTAMP,
    is_archived: BOOLEAN,
    ...
}
```

### New Table Needed

```
user_api_keys {
    id: INTEGER (PRIMARY KEY),
    user_id: TEXT (FOREIGN KEY → users.username),  ← REQUIRED
    provider: TEXT,                                 ← 'anthropic', 'openai', etc.
    api_key: TEXT,                                  ← The actual API key (encrypted in prod)
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
    UNIQUE(user_id, provider)
}

SQL:
CREATE TABLE IF NOT EXISTS user_api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

---

## Diagram 6: Handler Chain - Before vs. After

### Before (Current - Broken)

```
POST /llm/api-key (routers/llm.py):
    ↓
    orchestrator.process_request(
        "multi_llm",
        {"action": "add_api_key", ...}
    )
    ↓
orchestrator._handle_multi_llm():
    ↓
    action = "add_api_key"
    ↓
    if action == "list_providers": ...
    elif action == "get_provider_config": ...
    elif action == "set_default_provider": ...
    elif action == "update_api_key": ...
    elif action == "get_usage_stats": ...
    else:
        ❌ return {"status": "error", "message": "Unknown action: add_api_key"}
```

### After (Fixed)

```
POST /llm/api-key (routers/llm.py):
    ↓
    orchestrator.process_request(
        "multi_llm",
        {"action": "add_api_key", "user_id": "alice", "api_key": "..."}
    )
    ↓
orchestrator._handle_multi_llm():
    ↓
    action = "add_api_key"
    ↓
    if action == "list_providers": ...
    elif action == "get_provider_config": ...
    elif action == "set_default_provider": ...
    elif action == "update_api_key": ...
    elif action == "add_api_key":  ← ✅ NEW HANDLER
        user_id = request_data.get("user_id")
        api_key = request_data.get("api_key")
        db.save_api_key(user_id, "anthropic", api_key)
        return {"status": "success", ...}
    elif action == "remove_api_key":  ← ✅ NEW HANDLER
        user_id = request_data.get("user_id")
        db.delete_api_key(user_id, "anthropic")
        return {"status": "success", ...}
    elif action == "get_usage_stats": ...
    else:
        return {"status": "error", "message": "Unknown action: ..."}
```

---

## Diagram 7: Question Generation Flow - Before vs. After Fix

### Before (Current - Broken)

```
GET /projects/{id}/chat/question
    ↓
orchestrator._handle_socratic_counselor():
    ↓
    user_id = request_data.get("user_id")  ← Extracted but ignored
    ↓
    if counselor and self.llm_client:  ← Uses global client ALWAYS
        result = counselor.process({"topic": "Python Calculator"})
    ↓
counselor (SocraticCounselor with custom override):
    ↓
    self.llm_client = self.llm_client  ← Is this user's key?
                                         ← No, it's the global server key
    ↓
    response = self.llm_client.generate_response(prompt)
    ↓
    ❌ Questions use server's API key, not user's
```

### After (Fixed)

```
GET /projects/{id}/chat/question
    ↓
orchestrator._handle_socratic_counselor():
    ↓
    user_id = request_data.get("user_id")  ← EXTRACT USER ID
    ↓
    db.get_api_key(user_id, "anthropic")  ← LOOKUP USER'S KEY
    ↓
    IF user_api_key:
        user_llm_client = LLMClient(..., api_key=user_api_key)
        counselor.llm_client = user_llm_client  ← ASSIGN USER'S CLIENT
    ELSE:
        counselor.llm_client = self.llm_client  ← FALLBACK TO GLOBAL
    ↓
    if counselor and (user_api_key or self.llm_client):
        result = counselor.process({"topic": "Python Calculator"})
    ↓
counselor (SocraticCounselor with custom override):
    ↓
    self.llm_client = (user's client or global)  ← CORRECT CLIENT
    ↓
    response = self.llm_client.generate_response(prompt)
    ↓
    ✅ Questions use user's API key quota
```

---

## Diagram 8: The Complete Picture - All Three Issues

```
ISSUE 1: Hardcoded Questions
├─ Was: socratic_agents library ignored llm_client
├─ Fixed: Created custom subclass that uses Claude ✅
└─ Status: DONE

ISSUE 2: User API Keys Not Stored
├─ Was: database.get_api_key() is a stub
├─ Needs: Implement database methods
└─ Status: TODO

ISSUE 3: User API Keys Not Used
├─ Was: Orchestrator only uses global API key
├─ Needs: Look up user key and use it
└─ Status: TODO

ISSUE 4: Handlers Missing
├─ Was: add_api_key, remove_api_key handlers don't exist
├─ Needs: Add 5 missing handlers to _handle_multi_llm()
└─ Status: TODO
```

---

## Execution Path Summary

### What Happens Now (Current)

```
1. User sets API key: POST /llm/api-key
   → Orchestrator: Unknown action → Key lost

2. User gets question: GET /projects/{id}/chat/question
   → Backend: Use global API key
   → Claude: Generates question (might fail if no server key)
   → User: Sees question but uses server's quota
```

### What Should Happen (After Fix)

```
1. User sets API key: POST /llm/api-key
   → Orchestrator handler: Save to database
   → Database: Store user's key
   → User: API key is now available

2. User gets question: GET /projects/{id}/chat/question
   → Backend: Look up user's API key
   → Found: Create per-user LLMClient
   → Claude: Generates question using user's quota
   → User: Sees custom question, uses their quota

   → Not found: Fall back to server's global key
   → Claude: Generates question using server quota
   → User: Sees custom question, uses server quota
```

---

**These diagrams should make the architecture clear and show exactly what needs to be fixed.**
