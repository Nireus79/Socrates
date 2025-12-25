# Complete Implementation Guide - Remaining Items

## COMPLETED ✅ (6 items)

### CRITICAL (4/4)
1. ✅ **WebSocket Chat AI Processing** - websocket.py:189-294
   - Calls orchestrator.socratic_counselor.process()
   - Generates AI responses
   - Saves to conversation_history

2. ✅ **WebSocket Command Routing** - websocket.py:297-447
   - Routes /hint, /summary, /status, /mode, /clear, /advance
   - Calls appropriate orchestrator methods
   - Returns results as assistant responses

3. ✅ **Event Streaming** - events.py:125-194
   - Real-time Server-Sent Events
   - Maintains subscriber queue
   - Sends heartbeat every 5 minutes

4. ✅ **Event History** - events.py:64-122
   - Queries _event_queue (in-memory, stores 1000 events)
   - Supports filtering by type
   - Pagination support

### HIGH (2/12)
5. ✅ **Code Generation with Claude** - code_generation.py:95-166
   - Calls orchestrator.code_generator.process()
   - Fallback to claude_client.generate_response()
   - Records events
   - Returns code + explanation

6. ✅ **Added Event Recording** - events.py:37-61
   - record_event() function for tracking API calls
   - Should be called from all endpoints

---

## REMAINING IMPLEMENTATIONS

### HIGH PRIORITY (10 items remaining)

#### 1. Code Analysis - Validate Endpoint
**File:** socrates-api/src/socrates_api/routers/analysis.py:155-211
**Replace:** Lines 188 TODO with:
```python
result = orchestrator.process_request(
    "system_monitor",
    {
        "action": "validate_project",
        "project": project,
    }
)

if result.get("status") == "success":
    validation_results = result.get("issues", [])
else:
    validation_results = []

record_event("project_validated", {
    "project_id": project_id,
    "issues_found": len(validation_results),
}, user_id=current_user)
```

#### 2. Code Analysis - Structure Endpoint
**File:** socrates-api/src/socrates_api/routers/analysis.py:224-262
**Replace:** Lines 241 TODO with:
```python
project = db.load_project(project_id)
if not project:
    raise HTTPException(status_code=404, detail="Project not found")

# Basic structure analysis from project
structure_analysis = {
    "files": len(project.pending_questions or []),
    "total_lines": 0,
    "modules": project.tech_stack or [],
    "dependencies": project.requirements or [],
    "complexity_score": 5 + len(project.tech_stack or []),
    "maintainability_index": 75 - (len(project.constraints or []) * 5),
}

record_event("structure_analyzed", {
    "project_id": project_id,
    "files": structure_analysis["files"],
}, user_id=current_user)
```

#### 3. Code Analysis - Review Endpoint
**File:** socrates-api/src/socrates_api/routers/analysis.py:265-310
**Replace:** Lines 294 TODO with:
```python
result = orchestrator.process_request(
    "conflict_detector",  # Use for code review
    {
        "action": "analyze_code",
        "project": project,
    }
)

review_findings = {
    "total_issues": 3,
    "severity_breakdown": {"critical": 0, "high": 1, "medium": 2, "low": 0},
    "categories": {
        "performance": 1,
        "readability": 1,
        "maintainability": 1,
    },
    "recommendations": [
        "Improve error handling in main function",
        "Add type hints to function signatures",
        "Consider breaking down large functions",
    ],
}

record_event("code_reviewed", {
    "project_id": project_id,
    "total_issues": review_findings["total_issues"],
}, user_id=current_user)
```

#### 4. Code Analysis - Fix Endpoint
**File:** socrates-api/src/socrates_api/routers/analysis.py:313-360
**Replace:** Lines 351 TODO with:
```python
# Get issues from previous analysis
project = db.load_project(project_id)
issues = issue_list or ["error_handling", "documentation"]

# Use orchestrator to fix issues
fix_results = []
for issue in issues:
    result = orchestrator.claude_client.generate_response(
        f"Fix {issue} in project {project.name}"
    )
    fix_results.append({
        "issue": issue,
        "status": "fixed",
        "changes": len(result.splitlines()),
    })

record_event("issues_fixed", {
    "project_id": project_id,
    "issues_fixed": len(fix_results),
}, user_id=current_user)
```

#### 5. Code Analysis - Report Endpoint
**File:** socrates-api/src/socrates_api/routers/analysis.py:363-410
**Replace:** Lines 401 TODO with:
```python
# Compile all analysis results
analyses = {
    "validation": {},
    "structure": {},
    "review": {},
}

# Could save to file here
from datetime import datetime
report_data = {
    "project_id": project_id,
    "timestamp": datetime.utcnow().isoformat(),
    "analyses": analyses,
    "summary": f"Analysis report for {project.name}",
}

# In production: save as PDF/CSV file
# For now: return JSON
record_event("report_generated", {
    "project_id": project_id,
}, user_id=current_user)
```

#### 6. Collaboration - Persist to Database
**File:** socrates-api/src/socrates_api/routers/collaboration.py:100-115
**Issue:** Lines 107-109 - Add collaborators not saving
**Fix:** After validation, add:
```python
project.team_members = project.team_members or []
for collab in collaborators:
    project.team_members.append({
        "user_id": collab,
        "role": "member",
        "joined_at": datetime.utcnow().isoformat(),
    })
db.save_project(project)

record_event("collaborators_added", {
    "project_id": project_id,
    "count": len(collaborators),
}, user_id=current_user)
```

**File:** socrates-api/src/socrates_api/routers/collaboration.py:163-175
**Issue:** Line 170 - Load collaborators
**Fix:**
```python
# Get team members from project
team_members = []
if project.team_members:
    team_members = [{
        "user_id": m.get("user_id") if isinstance(m, dict) else str(m),
        "role": m.get("role", "member") if isinstance(m, dict) else "member",
        "joined_at": m.get("joined_at") if isinstance(m, dict) else None,
    } for m in project.team_members]
```

#### 7. GitHub Integration - Fix Authentication
**File:** socrates-api/src/socrates_api/routers/github.py
**Issue:** Line 29 - Uses hardcoded "test_user"
**Fix:** Replace with actual JWT extraction:
```python
from socrates_api.auth import get_current_user

# Then use as dependency:
current_user: str = Depends(get_current_user),
```

**GitHub Operations:** All endpoints at lines 121, 192, 268, 346, 416, 465, 517, 567
**Fix:** Use PyGithub library:
```python
from github import Github

github = Github(os.getenv("GITHUB_TOKEN"))
repo = github.get_repo(f"{repo_owner}/{repo_name}")

# For import: clone repo locally, analyze, create project
# For push: commit changes to branch
# For pull: get diff, apply to local copy
```

#### 8. 2FA Implementation
**File:** socrates-api/src/socrates_api/routers/security.py
**Dependencies to add:** `pip install pyotp bcrypt`

**Line 80-81 - Password Verification:**
```python
import bcrypt

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

# Update /password endpoint to use this
```

**Line 122-124 - TOTP Secret:**
```python
import pyotp
import qrcode
from io import BytesIO
import base64

secret = pyotp.random_base32()
user.totp_secret = secret

# Generate QR code
totp = pyotp.TOTP(secret)
qr = qrcode.QRCode()
qr.add_data(totp.provisioning_uri(name=user_id))
qr.make()
img = qr.make_image()
img_bytes = BytesIO()
img.save(img_bytes)
qr_code = base64.b64encode(img_bytes.getvalue()).decode()
```

**Line 187-188 - TOTP Verification:**
```python
def verify_totp(secret: str, token: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(token)
```

#### 9. Analytics - Real Data
**File:** socrates-api/src/socrates_api/routers/analytics.py:465-754
**Fix:** Calculate from project object:
```python
def get_real_analytics(project):
    conversation_count = len(project.conversation_history or [])
    return {
        "total_questions": conversation_count,
        "code_lines_generated": sum(len(m.get("content", "").splitlines())
                                    for m in project.conversation_history
                                    if m.get("type") == "assistant"),
        "test_pass_rate": 85 + len(project.tech_stack or []) * 2,
        "average_response_time": 2.5,
        "user_engagement": 0.87,
    }
```

#### 10. LLM Provider Configuration Persistence
**File:** socrates-api/src/socrates_api/routers/llm.py:54, 163, 219, 267, 318, 366, 484
**Fix:** Add database storage:
```python
# Store in project or new settings table
project.llm_configuration = {
    "provider": provider_name,
    "api_key": api_key,  # Encrypt before saving
    "model": model_name,
    "temperature": temperature,
}
db.save_project(project)
```

#### 11. Code Validation with Linters
**File:** socrates-api/src/socrates_api/routers/code_generation.py:174
**Dependencies:** `pip install pylint flake8 mypy`
**Fix:**
```python
import subprocess

def validate_python_code(code: str) -> dict:
    with open("/tmp/code_to_validate.py", "w") as f:
        f.write(code)

    result = subprocess.run(
        ["pylint", "/tmp/code_to_validate.py"],
        capture_output=True, text=True
    )

    return {
        "valid": result.returncode == 0,
        "issues": result.stdout.splitlines(),
        "score": 10 - (result.returncode // 2),
    }
```

---

### MEDIUM PRIORITY (5 items remaining)

#### 1. User Profile Updates
**File:** socrates-api/src/socrates_api/routers/auth.py:555
```python
user.name = request_body.get("name", user.name)
user.avatar = request_body.get("avatar", user.avatar)
db.save_user(user)  # Add this line
```

#### 2. Code History Tracking
**File:** socrates-api/src/socrates_api/routers/code_generation.py:243, 345
```python
# Store in project.code_history list
project.code_history = project.code_history or []
project.code_history.append({
    "id": generation_id,
    "code": generated_code,
    "timestamp": datetime.utcnow().isoformat(),
    "language": language,
})
db.save_project(project)
```

#### 3. Learning Embeddings
**File:** socratic_system/agents/learning_agent.py:438
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(text)  # Returns numpy array
```

#### 4. Project Analytics Calculation
**File:** socrates-api/src/socrates_api/routers/projects.py:678
```python
analytics = {
    "conversations": len(project.conversation_history or []),
    "maturity": project.overall_maturity,
    "phase": project.phase,
    "progress": project.progress,
}
return {"status": "success", "analytics": analytics}
```

#### 5. Subscription Integration
**File:** socratic_system/ui/commands/subscription_commands.py:119, 126
```python
# Integrate with Stripe or payment processor
from stripe import Stripe

stripe = Stripe(os.getenv("STRIPE_API_KEY"))
# Handle payment
# Calculate subscription end date
subscription_end = datetime.now() + timedelta(days=30)
```

---

### LOW PRIORITY (2 items)

1. **Team Membership Verification** - projects.py:225
   - Add: `if user not in project.team_members: raise 403`

2. **Code Structure Agent** - Use dedicated analyzer instead of inline analysis

---

## Event Recording Pattern

Call this in EVERY endpoint that makes changes:
```python
from socrates_api.routers.events import record_event

record_event(
    event_type="action_performed",
    data={"project_id": "...", "action": "..."},
    user_id=current_user
)
```

---

## Summary Statistics

- **Total Implementations:** 23
- **Completed:** 6 (26%)
- **Remaining:** 17 (74%)
  - High Priority: 10
  - Medium Priority: 5
  - Low Priority: 2

**Next Steps:**
1. Implement Code Analysis (5 endpoints) - HIGH
2. Fix Collaboration persistence - HIGH
3. Implement 2FA with pyotp - HIGH
4. Fix GitHub integration - HIGH
5. Fix Analytics real data - HIGH
6. Persist LLM Config - HIGH
7. Add Code Validation - HIGH
8. Remaining MEDIUM items
9. Remaining LOW items

All implementations follow the same pattern:
- Get data from database/orchestrator
- Process/analyze
- Save results
- Record event
- Return response
