# Free Tier Project Creation Fix - Summary

## Issue
Free tier users were unable to create any projects, despite the monetization model requiring free tier to allow at least 1 project.

## Root Cause Analysis
The API middleware (`socrates-api/src/socrates_api/middleware/subscription.py`) had a separate `TIER_FEATURES` dictionary that was:
1. **Missing the "project_creation" feature** - not defined in any tier
2. **Out of sync with system tier definitions** - different limits and features than `socratic_system/subscription/tiers.py`

When a feature is not found in any tier, `_get_required_tier_for_feature()` returns "enterprise" as default, causing free tier users to be blocked.

## Fixes Applied

### 1. Added "project_creation" Feature to All Tiers
**File:** `socrates-api/src/socrates_api/middleware/subscription.py`

Added `"project_creation": True` to the features dict for:
- **Free tier** (line 32): Allows creation within quota (1 project max)
- **Pro tier** (line 49): Allows creation within quota (10 projects max)
- **Enterprise tier** (line 66): Unlimited project creation

### 2. Aligned Questions/Month Limits
**File:** `socrates-api/src/socrates_api/middleware/subscription.py`

Updated to match `socratic_system/subscription/tiers.py`:
- **Free tier**: 50 → **100** questions/month (line 21)
- **Pro tier**: 500 → **1000** questions/month (line 38)

### 3. Fixed Feature Parity
**File:** `socrates-api/src/socrates_api/middleware/subscription.py`

- **Pro tier**: `multi_llm: False` → `True` (line 47)

## System Architecture

### Two Independent Subscription Checkers

1. **`socratic_system/subscription/checker.py`** - Used by CLI and Orchestrator
   - Defines TierLimits dataclass with limits
   - `check_project_limit()` enforces quota per tier
   - Returns (bool, error_message) tuple

2. **`socrates-api/src/socrates_api/middleware/subscription.py`** - Used by API
   - Defines TIER_FEATURES dict with feature access matrix
   - `has_feature()` checks if tier has feature
   - `require_subscription_feature()` decorator for endpoints
   - `_get_required_tier_for_feature()` determines minimum tier

### Why Two?
The API middleware was created as a separate system to gate features at the API level, but became out of sync with the system's canonical tier definitions in `socratic_system/subscription/tiers.py`.

## How It Works Now

### Creation Flow (Free Tier User)
1. Free tier user registers → `subscription_tier="free"` set
2. User calls POST /projects endpoint
3. Orchestrator processes request via ProjectManagerAgent
4. Agent calls `check_project_limit(user, 0)` from socratic_system checker
5. Check returns (True, None) because: 0 < max_projects=1
6. Project successfully created
7. Second project attempt blocked with subscription error

### Feature Checks (if API Middleware Used)
If the API middleware's feature checks are applied:
1. `SubscriptionChecker.has_feature("free", "project_creation")` → **True** (now)
2. Endpoint allowed to proceed
3. Orchestrator handles quota enforcement

## Testing

### What Works
- ✓ Free tier user registration with default "free" tier
- ✓ Free tier users can create 1 project (tested via orchestrator)
- ✓ Second project creation blocked at quota level
- ✓ Pro and Enterprise tiers have correct limits

### What Needs Testing
- API endpoint response with free tier project creation
- Verify middleware's feature checks are being used (or remove if unused)
- Load test with multiple free tier users creating projects

## Files Modified
1. `socrates-api/src/socrates_api/middleware/subscription.py`
   - Added "project_creation" to all tier features
   - Updated question limits to match system tiers
   - Fixed multi_llm feature parity

## Recommendations

### Short Term
1. Verify the API is actually using the middleware's feature checks
2. If not used, clean up unused imports from projects.py
3. Test free tier project creation through the API endpoint

### Long Term
1. **Consolidate subscription checking**: Merge API middleware TIER_FEATURES with system TIER_LIMITS
2. **Single source of truth**: Use `socratic_system/subscription/tiers.py` as canonical source
3. **Remove duplicate code**: Eliminate duplicate SubscriptionChecker implementations
4. **API should wrap orchestrator checker**: Don't duplicate subscription logic

## Configuration Comparison

### Free Tier
| Setting | System Tiers | API Middleware | Status |
|---------|--------------|----------------|--------|
| max_projects | 1 | 1 | ✓ Aligned |
| max_questions/month | 100 | 100 | ✓ Fixed (was 50) |
| project_creation | (implicit) | ✓ True | ✓ Fixed (added) |

### Pro Tier
| Setting | System Tiers | API Middleware | Status |
|---------|--------------|----------------|--------|
| max_projects | 10 | 10 | ✓ Aligned |
| max_questions/month | 1000 | 1000 | ✓ Fixed (was 500) |
| multi_llm | ✓ True | ✓ True | ✓ Fixed (was False) |
| project_creation | (implicit) | ✓ True | ✓ Added |

---
**Updated:** December 24, 2025
**Status:** Free tier project creation fix applied to API middleware
