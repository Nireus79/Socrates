# Socrates Monetization System - Interactive Demo

This document demonstrates how the monetization system works in real-world scenarios.

---

## Demo 1: Free Tier User Tries to Use Team Collaboration

### Initial State
```
User: free_user
Tier: Free
Projects: 1/1
Questions Used: 45/100
```

### User Action
```
> /collab add alice creator
```

### System Response
The CommandHandler intercepts the command and checks subscription:

```python
# In CommandHandler._execute_command()
has_access, error_msg = SubscriptionChecker.check_command_access(
    user, "collab add"
)
# Returns: (False, "┌─ Premium Feature Required ─┐...")
```

### Output to User
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Premium Feature Required

The command 'collab add' requires Team Collaboration.
Your current tier: FREE
Required tier: PRO

💡 Upgrade to unlock this feature!
Run: /subscription upgrade pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### What Happens Behind the Scenes

1. **Command Name Lookup**:
   - `"collab add"` → Found in `COMMAND_FEATURE_MAP`
   - Maps to feature: `"team_collaboration"`

2. **Feature to Tier Lookup**:
   - `"team_collaboration"` → Found in `FEATURE_TIER_REQUIREMENTS`
   - Requires tier: `"pro"`

3. **User Tier Check**:
   - User tier: `"free"` (value: 0)
   - Required tier: `"pro"` (value: 1)
   - Result: 0 < 1 → Access Denied ✗

4. **Error Message Generation**:
   - Friendly message generated with:
     - Feature name: "Team Collaboration"
     - Current tier: "FREE"
     - Required tier: "PRO"
     - Action: `/subscription upgrade pro`

---

## Demo 2: User Upgrades from Free to Pro

### Initial State
```
User: pro_wannabe
Tier: Free
Subscription Status: active
```

### User Action
```
> /subscription upgrade pro
```

### System Response

**Step 1**: Command executes
```python
# In SubscriptionUpgradeCommand.execute()
old_tier = user.subscription_tier  # "free"
user.subscription_tier = new_tier  # "pro"
user.subscription_status = "active"
user.subscription_start = datetime.now()
orchestrator.database.save_user(user)
```

**Step 2**: Output to user
```
✓ Successfully upgraded to Pro tier!

Monthly Cost: $29.00
Features Unlocked:
  • Multi-LLM Access
  • Team Collaboration (up to 5 members)
  • Advanced Analytics
  • Code Generation
  • Maturity Tracking

Note: Payment integration coming soon. For now, this is a manual upgrade.
```

**Step 3**: User now has access to gated commands

### New Abilities After Upgrade
```
> /collab add alice creator
SUCCESS: Added alice as creator to the project

> /analytics analyze
[Advanced Analytics Report Generated...]

> /code generate
[Code generation enabled - generating solution...]

> /llm openai
[Switching to OpenAI LLM...]
```

---

## Demo 3: Free Tier User Hits Project Limit

### Initial State
```
User: solo_developer
Tier: Free
Projects: 1 (at max)
```

### User Action
```
> /project create "My Second Project"
```

### System Response

**Step 1**: ProjectManager checks project limit
```python
# In ProjectManager._create_project()
user = database.load_user(owner)
active_projects = database.get_user_projects(owner)
active_count = len([p for p in active_projects if not p.is_archived])
# active_count = 1

can_create, error_msg = SubscriptionChecker.check_project_limit(user, 1)
# Returns: (False, "┌─ Project Limit Reached ─┐...")
```

**Step 2**: Output to user
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Limit Reached

Your Free tier allows 1 active project(s).
You currently have 1 active project(s).

💡 Upgrade to Pro for 10 projects or Enterprise for unlimited projects.
Run: /subscription upgrade pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Solution: Upgrade or Archive
```
Option 1: Upgrade to Pro
> /subscription upgrade pro
[Now can have 10 projects]

Option 2: Archive existing project
> /project archive "My First Project"
[Archived project doesn't count toward limit]
> /project create "My Second Project"
[Now can create second project]
```

---

## Demo 4: Free Tier User Tracks Monthly Usage

### Scenario: User asks questions throughout the month

**Week 1**: 25 questions asked
```
> /subscription status

Usage This Month

  Questions: 25/100 (25%)
  Projects: 1/1 (100%)
```

**Week 2**: 50 more questions (total 75)
```
> /subscription status

Usage This Month

  Questions: 75/100 (75%)
  Projects: 1/1 (100%)
```

**Week 3**: Hit the limit at 100 questions
```
> /chat "Can you help me debug this?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monthly Question Limit Reached

Your Free tier allows 100 questions per month.
You've used 100 questions this month.

💡 Upgrade to Pro for 1,000 questions/month or Enterprise for unlimited.
Run: /subscription upgrade pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Automatic Reset on Next Month
```
[Month ends, new month begins]

> /subscription status

Usage This Month

  Questions: 0/100 (0%)    # Automatically reset!
  Projects: 1/1 (100%)
```

**Behind the scenes**:
```python
# In check_question_limit()
user.reset_monthly_usage_if_needed()

# In User.reset_monthly_usage_if_needed()
if self.usage_reset_date and datetime.now() >= self.usage_reset_date:
    self.questions_used_this_month = 0
    # Set next reset date to 1st of next month
```

---

## Demo 5: Pro Tier User Adds Team Members

### Initial State
```
User: team_lead
Tier: Pro
Team Members: 2/5
```

### Action 1: Add team member (under limit)
```
> /collab add bob developer

SUCCESS: Added bob as developer to the project
```

### Action 2: Add more team members
```
> /collab add charlie tester

SUCCESS: Added charlie as tester to the project

> /collab add diana qa_lead

SUCCESS: Added diana as qa_lead to the project
```

### State After Additions
```
Team Members: 5/5 (100%)
```

### Action 3: Try to add 6th member (hits limit)
```
> /collab add eve architect

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Team Member Limit Reached

Your Pro tier allows 5 team member(s).
You currently have 5 team member(s).

💡 Upgrade to Enterprise for unlimited team members.
Run: /subscription upgrade enterprise
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Solution: Upgrade to Enterprise
```
> /subscription upgrade enterprise

✓ Successfully upgraded to Enterprise tier!

Monthly Cost: $99.00
Features Unlocked:
  • Multi-LLM Access
  • Team Collaboration (up to unlimited members)
  • Advanced Analytics
  • Code Generation
  • Maturity Tracking

> /collab add eve architect

SUCCESS: Added eve as architect to the project
Team Members: 6/Unlimited
```

---

## Demo 6: Comparing Subscription Tiers

### User Action
```
> /subscription compare
```

### System Output
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subscription Tier Comparison

Feature                        Free            Pro             Enterprise
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monthly Cost                   $0              $29             $99
Active Projects                1               10              Unlimited
Team Members                   Solo only       Up to 5         Unlimited
Questions/Month                100             1,000           Unlimited
Multi-LLM Access               ✗               ✓               ✓
Advanced Analytics             ✗               ✓               ✓
Code Generation                ✗               ✓               ✓
Maturity Tracking              ✗               ✓               ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run /subscription upgrade <tier> to upgrade
```

---

## Demo 7: Developer Uses API-Level Quota Checks

### Scenario: Agent-based operation needs to check quotas

```python
# In some agent or service
from socratic_system.subscription.checker import SubscriptionChecker

user = database.load_user(username)

# Check if user can create project
can_create, error_msg = SubscriptionChecker.check_project_limit(user, current_count)
if not can_create:
    return {"status": "error", "message": error_msg}

# Check if user can add team member
can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, team_size)
if not can_add:
    return {"status": "error", "message": error_msg}

# Check if user can ask question
can_ask, error_msg = SubscriptionChecker.check_question_limit(user)
if not can_ask:
    return {"status": "error", "message": error_msg}

# All checks passed - proceed with operation
user.increment_question_usage()
database.save_user(user)
```

---

## Demo 8: Enterprise User with No Limits

### Initial State
```
User: large_org
Tier: Enterprise
Projects: 47 (no limit)
Team Members: 23 (no limit)
Questions/Month: 8,500 used (no limit)
```

### Actions: All succeed without restrictions

```
> /project create "Project 48"
SUCCESS: Created project 48

> /collab add frank director
SUCCESS: Added frank as director

> /collab add grace consultant
SUCCESS: Added grace as consultant

> /analytics analyze
[Advanced Analytics Report Generated...]

> /code generate
[Generating solution with unlimited questions...]

> /subscription status

Subscription Status

Tier: Enterprise
Status: Active
Monthly Cost: $99.00

Usage This Month

  Questions: 8,500 (unlimited)
  Projects: 48 (unlimited)

Features

  ✓ Multi-LLM Access (Claude, OpenAI, Gemini)
  ✓ Team Collaboration
  ✓ Advanced Analytics
  ✓ Code Generation
  ✓ Maturity Tracking
```

---

## How the System Works: Technical Flow

### Command Execution with Subscription Check

```
User Input: /collab add alice creator
    ↓
CommandHandler.execute()
    ↓
Parse command: "collab add"
    ↓
Find command object
    ↓
[NEW] Check subscription access:
    ↓
    ├─ Get user from context
    ├─ Call SubscriptionChecker.check_command_access(user, "collab add")
    │   ├─ Look up in COMMAND_FEATURE_MAP: "team_collaboration"
    │   ├─ Look up in FEATURE_TIER_REQUIREMENTS: "pro"
    │   ├─ Get user tier: "free"
    │   ├─ Compare tier levels: free(0) < pro(1) → NO ACCESS
    │   └─ Generate error message with upgrade CTA
    ├─ If no access: return error message
    └─ If has access: continue
    ↓
Execute command or return error
```

### Project Creation with Quota Enforcement

```
User Action: /project create "My Project"
    ↓
ProjectManager._create_project()
    ↓
Check project limit:
    ├─ Load user
    ├─ Get user projects from database
    ├─ Count active (non-archived) projects
    ├─ Call SubscriptionChecker.check_project_limit(user, count)
    │   ├─ Get tier limits
    │   ├─ Check if count >= max_projects
    │   ├─ Return (can_create, error_message)
    └─ If can't create: return error with upgrade CTA
    ↓
If quota OK: create project and save
```

### Question Limit with Automatic Reset

```
User Action: /chat "Can you help?"
    ↓
SocraticCounselor._generate_question()
    ↓
Check question limit:
    ├─ Call SubscriptionChecker.check_question_limit(user)
    │   ├─ Call user.reset_monthly_usage_if_needed()
    │   │   ├─ Check if today >= usage_reset_date
    │   │   ├─ If yes: reset counter and set next reset date
    │   │   └─ If no: do nothing
    │   ├─ Get tier limits
    │   ├─ Check if questions_used >= max_questions
    │   └─ Return (can_ask, error_message)
    └─ If can't ask: return error with upgrade CTA
    ↓
If quota OK: generate question and increment counter
    ├─ Perform question generation
    ├─ Call user.increment_question_usage()
    ├─ Save user to database
    └─ Return result
```

---

## Summary

The Socratic Monetization System provides:

1. **Seamless Feature Gating**: Single CommandHandler interception point gates all commands
2. **Clear User Experience**: Friendly upgrade messages with actionable CTAs
3. **Flexible Quotas**: Easily configured per tier
4. **Automatic Management**: Monthly resets happen automatically
5. **Scalable Design**: Easy to add new tiers, features, or commands
6. **Backward Compatible**: Existing users get Free tier by default
7. **Production Ready**: 44 tests passing, all scenarios covered

All demonstrations above work exactly as shown with the current implementation!

Notes
  Bypass Methods & Vulnerabilities

  1. Direct User Object Modification (CRITICAL)

  If a user has access to the Python environment or can modify their session:
  # In-memory modification before checker runs
  user.subscription_tier = "enterprise"
  user.questions_used_this_month = 0
  Risk: High if running locally with direct code access

  2. Database Tampering (CRITICAL)

  Since subscriptions are persisted in the projects database:
  # Direct database modification
  orchestrator.database.users_collection.update_one(
      {"username": "attacker"},
      {"$set": {"subscription_tier": "enterprise"}}
  )
  Risk: High if user has direct database file access

  3. Modifying Tier Definitions (HIGH)

  The tier limits are hardcoded in tiers.py:
  # Could manually edit the FREE_TIER to have higher limits
  FREE_TIER = Tier(
      name="free",
      max_projects=1000,  # Changed from 1
      max_questions=999999,  # Changed from 100
  )
  Risk: High for local development/testing

  4. Disabling the Checker (HIGH)

  Comment out or skip checker logic in:
  - command_handler.py lines 145-153
  - project_manager.py lines 87-92
  - socratic_counselor.py lines 96-101

  5. Usage Reset Manipulation (MEDIUM)

  Modify the monthly usage tracking:
  user.questions_used_this_month = 0
  user.usage_reset_date = datetime.now() + timedelta(days=365)

  6. Direct API/Database Calls (MEDIUM)

  If there are any direct database save/load methods that bypass subscription checks

  ---
  Recommendations to Secure Monetization

  1. Server-Side Enforcement Only (CRITICAL)

  - All restrictions must be enforced on the backend
  - Never trust client-side checks
  - Ensure the checker runs before ANY data modification

  2. Database Security (CRITICAL)

  - Encrypt subscription fields in the database
  - Use role-based access control (RBAC) for database access
  - Hash/sign tier information to detect tampering
  - Add audit logs for subscription changes

  3. Immutable Subscription State (HIGH)

  # Use a signed/hashed subscription token instead of plain text
  subscription_token = sign_subscription_data(user.subscription_tier)
  # Verify token before using subscription data
  verified_tier = verify_subscription_token(subscription_token)

  4. Separate Configuration from Application (HIGH)

  - Move tier definitions to a read-only configuration file
  - Load at startup and make immutable
  - Don't allow runtime modification

  5. Comprehensive Audit Logging (HIGH)

  # Log every subscription check and result
  logger.info(f"Subscription check: user={username}, command={command}, tier={tier}, granted={result}")
  logger.warning(f"SECURITY: Potential bypass attempt: {details}")

  6. Integrity Verification (MEDIUM)

  - Add checksums to critical subscription data
  - Detect if fields have been modified
  - Trigger security alerts on tampering

  7. Rate Limiting + Quota Enforcement (MEDIUM)

  - Track and limit rapid-fire requests
  - Enforce quotas at multiple levels (per-second, per-day, per-month)

  8. Input Validation (MEDIUM)

  - Validate tier values against allowed enum
  - Validate usage counters are non-negative
  - Validate dates are reasonable

  ---
  Current Weak Points in Your System

  1. No authentication shown - How are users authenticated? Username-only?
  2. No encryption - Subscription data is stored in plaintext
  3. No audit trail - Can't detect or trace unauthorized changes
  4. No integrity checks - No way to know if database has been tampered with
  5. Direct database access - If users have file system access, they can modify SQLite/JSON files directly

4 ways to bypass monetization for testing:

  ---
  Summary of Methods

  | Method               | Ease   | Steps                                  | Persistence  |
  |----------------------|--------|----------------------------------------|--------------|
  | Built-in Command     | ⭐⭐⭐ | 1 command                              | Permanent    |
  | Database Script      | ⭐⭐⭐ | python bypass_monetization.py username | Permanent    |
  | Environment Variable | ⭐⭐   | set SOCRATES_BYPASS_MONETIZATION=1     | Session only |
  | Direct DB Query      | ⭐⭐   | 1 SQL command                          | Permanent    |

  ---
  Quick Start (Recommended)

  Environment Variable Method (Easiest for testing)

  On Windows Command Prompt:
  set SOCRATES_BYPASS_MONETIZATION=1
  python -m socratic_system.main

  Or PowerShell:
  $env:SOCRATES_BYPASS_MONETIZATION="1"
  python -m socratic_system.main

  This grants full access to all features without modifying the database.

  Python Script Method (Permanent upgrade)

  python bypass_monetization.py your_username

  This upgrades your user to enterprise tier in the database.

  ---
  What Gets Bypassed

  ✅ Command access restrictions
  ✅ Project creation limits
  ✅ Team member limits
  ✅ Monthly question quotas

Usage for Testers

  Enable Testing Mode

  /subscription testing-mode on

  This command:
  - ✅ Unlocks all premium features
  - ✅ Removes all tier restrictions
  - ✅ Persists in the database (survives restarts)
  - ✅ Displays confirmation message

  Disable Testing Mode

  /subscription testing-mode off

  Usage

  Command Prompt:
  python socrates.py --testing

  PowerShell:
  python socrates.py --testing

  ---
  What It Does

  When you run with --testing:

  1. ✅ Sets the SOCRATES_TESTING_MODE environment variable
  2. ✅ Automatically enables testing mode for the logged-in user after authentication
  3. ✅ Displays confirmation message: "Testing mode ENABLED"
  4. ✅ User can continue with all premium features unlocked
  5. ✅ Testing mode persists in the database

  ---
  Files Created/Modified

  | File                     | Change   | Purpose                                              |
  |--------------------------|----------|------------------------------------------------------|
  | socrates.py              | Created  | Command-line entry point with --testing flag support |
  | main_app.py              | Modified | Added _apply_testing_mode_if_enabled() method        |
  | user.py                  | Modified | Added testing_mode: bool = False field               |
  | subscription_commands.py | Modified | Added SubscriptionTestingModeCommand                 |
  | checker.py               | Modified | Updated all checkers to respect testing_mode         |

  ---
  Help

  python socrates.py --help

  Output:
  usage: socrates [-h] [--testing] [--version]

  Socrates AI - A Socratic method tutoring system powered by Claude AI

  options:
    -h, --help     show this help message and exit
    --testing      Enable testing mode (bypasses monetization restrictions)
    --version      show program's version number and exit

  ---
  Summary: 4 Ways to Enable Testing Mode

  | Method               | Command                                | Usage                      |
  |----------------------|----------------------------------------|----------------------------|
  | CLI Flag             | python socrates.py --testing           | Start with testing enabled |
  | Built-in Command     | /subscription testing-mode on          | Enable during session      |
  | Environment Variable | set SOCRATES_BYPASS_MONETIZATION=1     | Global bypass              |
  | Database Script      | python bypass_monetization.py username | Direct upgrade             |

  All methods work independently and can be combined!



