# Socrates Subscription System

## Overview

The Socrates subscription system provides tiered access to features and enforces usage limits. This is a production-ready implementation copied from Socrates-M.

**Location:** `socratic_system/subscription/`

## Files

- **checker.py** - Core subscription validation and feature gating
- **tiers.py** - Tier definitions and limit configurations
- **storage.py** - Storage quota management
- **__init__.py** - Module exports

## Three-Tier Model

### Free Tier
- **Projects:** 1 maximum
- **Team Members:** 1 (solo only)
- **Storage:** 5 GB
- **Monthly Questions:** Unlimited
- **Cost:** $0

### Pro Tier
- **Projects:** 10 maximum
- **Team Members:** 5
- **Storage:** 100 GB
- **Monthly Questions:** Unlimited
- **Cost:** $4.99/month

### Enterprise Tier
- **Projects:** Unlimited
- **Team Members:** Unlimited
- **Storage:** Unlimited
- **Monthly Questions:** Unlimited
- **Cost:** $9.99/month

## Usage

### SubscriptionChecker Methods

#### check_question_limit(user: User) -> Tuple[bool, Optional[str]]
Check if user can ask another question this month.

```python
from socratic_system.subscription import SubscriptionChecker

user = database.load_user("alice")
can_ask, error_msg = SubscriptionChecker.check_question_limit(user)

if not can_ask:
    print(error_msg)  # Shows upgrade message
```

#### check_project_limit(user: User, current_count: int) -> Tuple[bool, Optional[str]]
Check if user can create another project.

```python
can_create, error_msg = SubscriptionChecker.check_project_limit(user, current_project_count)
```

#### check_team_member_limit(user: User, team_size: int) -> Tuple[bool, Optional[str]]
Check if user can add another team member.

```python
can_add, error_msg = SubscriptionChecker.check_team_member_limit(user, current_team_size)
```

#### check_command_access(user: User, command_name: str) -> Tuple[bool, Optional[str]]
Check if user has access to a specific command based on their tier.

```python
has_access, error_msg = SubscriptionChecker.check_command_access(user, "collab add")
```

### Storage Quota Manager

```python
from socratic_system.subscription.storage import StorageQuotaManager

# Check if user can upload a document
can_upload, error = StorageQuotaManager.can_upload_document(
    user,
    database,
    document_size_bytes=5000000
)

# Get detailed storage usage report
report = StorageQuotaManager.get_storage_usage_report("alice", database)
print(f"Storage used: {report['storage_used_gb']}/{report['storage_limit_gb']}")
```

## User Model Integration

The `User` model in `socratic_system/models/user.py` includes subscription fields:

```python
@dataclass
class User:
    subscription_tier: str = "free"  # "free", "pro", "enterprise"
    subscription_status: str = "active"  # "active", "expired", "cancelled"
    subscription_start: Optional[datetime.datetime] = None
    subscription_end: Optional[datetime.datetime] = None

    # Usage tracking (resets monthly)
    questions_used_this_month: int = 0
    usage_reset_date: Optional[datetime.datetime] = None

    # Testing mode - bypasses all limits
    testing_mode: bool = False

    def reset_monthly_usage_if_needed(self):
        """Reset monthly usage if we've passed the reset date."""

    def increment_question_usage(self):
        """Increment question usage counter."""
```

## Testing Mode

Users can enable testing mode to bypass all subscription restrictions during development/testing:

```python
user.testing_mode = True
database.save_user(user)

# Now all limit checks will pass
can_ask, _ = SubscriptionChecker.check_question_limit(user)
assert can_ask  # True
```

## Integration with socratic-agents

The `socratic-agents` library imports the subscription checker from Socrates:

```python
# In socratic-agents code:
from socratic_agents.subscription.checker import SubscriptionChecker

# This automatically resolves to:
from socratic_system.subscription.checker import SubscriptionChecker
```

A bridge module in the virtual environment ensures seamless integration.

## Feature Gating

Define which commands require which features in `tiers.py`:

```python
FEATURE_TIER_REQUIREMENTS = {
    "team_collaboration": "pro",  # Requires Pro tier
}

COMMAND_FEATURE_MAP = {
    "collab add": "team_collaboration",
    "collab remove": "team_collaboration",
    # ... other commands
}
```

## Friendly Error Messages

When users hit limits, they see formatted error messages:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monthly Question Limit Reached

Your Free tier allows unlimited questions per month.
You've used 0 questions this month.

💡 Upgrade to Pro for unlimited access!
Run: /subscription upgrade pro
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

**Imported from:** Socrates-M (github.com/Nireus79/Socrates-M)
**Date:** 2026-05-05
**Status:** Production-Ready
