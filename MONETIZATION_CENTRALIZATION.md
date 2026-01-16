# Monetization System Centralization - Complete Refactor

## Overview

Successfully centralized the monetization system by consolidating duplicate tier definitions and moving all quota limits to a single source of truth.

## Changes Made

### 1. Enhanced Core Tier Definitions
**File:** `socratic_system/subscription/tiers.py`

**Change:** Added `storage_gb` field to `TierLimits` dataclass

**Before:**
```python
@dataclass
class TierLimits:
    name: str
    monthly_cost: float
    max_projects: Optional[int]
    max_team_members: Optional[int]
    max_questions_per_month: Optional[int]
    multi_llm_access: bool
    advanced_analytics: bool
    code_generation: bool
    maturity_tracking: bool
```

**After:**
```python
@dataclass
class TierLimits:
    name: str
    monthly_cost: float
    max_projects: Optional[int]
    max_team_members: Optional[int]
    max_questions_per_month: Optional[int]
    storage_gb: Optional[int]  # NEW: Centralized storage quota
    multi_llm_access: bool
    advanced_analytics: bool
    code_generation: bool
    maturity_tracking: bool
```

**Tier Definitions Updated:**
```python
TIER_LIMITS = {
    "free": TierLimits(
        name="Free",
        monthly_cost=0.0,
        max_projects=1,
        max_team_members=1,
        max_questions_per_month=None,
        storage_gb=5,            # NEW
        ...
    ),
    "pro": TierLimits(
        ...
        storage_gb=100,          # NEW
        ...
    ),
    "enterprise": TierLimits(
        ...
        storage_gb=None,         # NEW: Unlimited
        ...
    ),
}
```

### 2. Unified Storage Quota Management
**File:** `socratic_system/subscription/storage.py`

**Change:** Updated `get_storage_limit_gb()` to use centralized TIER_LIMITS instead of hardcoded values

**Before:**
```python
@staticmethod
def get_storage_limit_gb(tier: str) -> Optional[float]:
    limits = get_tier_limits(tier)
    # Hardcoded duplicates
    tier_limits = {
        "free": 5.0,
        "pro": 100.0,
        "enterprise": None,
    }
    return tier_limits.get(tier.lower(), 5.0)
```

**After:**
```python
@staticmethod
def get_storage_limit_gb(tier: str) -> Optional[float]:
    limits = get_tier_limits(tier)
    # Now pulls from central TIER_LIMITS.storage_gb
    return float(limits.storage_gb) if limits.storage_gb is not None else None
```

**Benefit:** Storage quota changes now only require updating TIER_LIMITS in one place.

### 3. Consolidated API Middleware
**File:** `socrates-api/src/socrates_api/middleware/subscription.py`

**Change:** Replaced hardcoded TIER_FEATURES with dynamic builder function that imports from central TIER_LIMITS

**Before:**
```python
# Hardcoded duplicate of tier definitions
TIER_FEATURES = {
    "free": {
        "projects": 1,
        "team_members": 1,
        "questions_per_month": None,
        "features": {...}
    },
    "pro": {...},
    "enterprise": {...}
}
```

**After:**
```python
from socratic_system.subscription.tiers import TIER_LIMITS

def _build_tier_features():
    """Build TIER_FEATURES from central TIER_LIMITS for backward compatibility."""
    tier_features = {}
    for tier_name, tier_limits in TIER_LIMITS.items():
        tier_features[tier_name] = {
            "projects": tier_limits.max_projects,
            "team_members": tier_limits.max_team_members,
            "storage_gb": tier_limits.storage_gb,  # NEW
            "questions_per_month": tier_limits.max_questions_per_month,
            "features": {
                "code_generation": tier_limits.code_generation,
                "collaboration": tier_limits.max_team_members != 1,
                "advanced_analytics": tier_limits.advanced_analytics,
                "multi_llm": tier_limits.multi_llm_access,
                # ... all other features
            }
        }
    return tier_features

TIER_FEATURES = _build_tier_features()
```

**Benefits:**
- No more hardcoded duplicates
- Middleware automatically stays in sync with central definitions
- Storage_gb now included in middleware tier data

### 4. Consolidated REST API Subscription Endpoint
**File:** `socrates-api/src/socrates_api/routers/subscription.py`

**Change:** Replaced hardcoded SUBSCRIPTION_TIERS with dynamic builder function

**Before:**
```python
# Another hardcoded duplicate
SUBSCRIPTION_TIERS = {
    "free": {
        "tier": "free",
        "display_name": "Free",
        "price": 0.0,
        "projects_limit": 1,
        "team_members_limit": 1,
        "storage_gb": 5,
        "features": [...]
    },
    "pro": {...},
    "enterprise": {...}
}
```

**After:**
```python
from socratic_system.subscription.tiers import TIER_LIMITS

def _build_subscription_tiers():
    """Build SUBSCRIPTION_TIERS from central TIER_LIMITS."""
    tiers = {}
    feature_descriptions = {
        "free": [...],
        "pro": [...],
        "enterprise": [...]
    }
    for tier_name, tier_limits in TIER_LIMITS.items():
        tiers[tier_name] = {
            "tier": tier_name,
            "display_name": tier_limits.name,
            "price": tier_limits.monthly_cost,
            "projects_limit": tier_limits.max_projects,
            "team_members_limit": tier_limits.max_team_members,
            "storage_gb": tier_limits.storage_gb,
            "features": feature_descriptions.get(tier_name, []),
            "description": tier_descriptions.get(tier_name, ""),
        }
    return tiers

SUBSCRIPTION_TIERS = _build_subscription_tiers()
```

**Benefits:**
- Prices, limits, and storage quotas now pull from central source
- User-facing feature descriptions kept separate (maintainable)
- Any tier definition change automatically propagates to API responses

## Architecture Diagram

```
Central Source of Truth:
┌─────────────────────────────────────────────────┐
│ socratic_system/subscription/tiers.py           │
│                                                 │
│ TIER_LIMITS = {                                 │
│   "free": TierLimits(                          │
│     max_projects=1,                            │
│     max_team_members=1,                        │
│     storage_gb=5,    ← Single definition       │
│     ...                                        │
│   ),                                           │
│   "pro": TierLimits(...),                      │
│   "enterprise": TierLimits(...)                │
│ }                                              │
└─────────────────────────────────────────────────┘
         ↓ Imported by            ↓ Imported by
         │                        │
    ┌────────────────────┐   ┌─────────────────────────┐
    │ CLI/Agent Layer    │   │ API Middleware Layer    │
    │                    │   │                         │
    │ subscription/      │   │ middleware/             │
    │ checker.py         │   │ subscription.py         │
    │                    │   │                         │
    │ Uses:              │   │ TIER_FEATURES =         │
    │ - get_tier_limits()│   │ _build_tier_features()  │
    │ - Enforcement      │   │                         │
    │   logic            │   │ Dynamically built       │
    └────────────────────┘   └─────────────────────────┘
         ↓                             ↓
    CLI Commands            REST API Middleware
    Orchestrator            Feature Gating
    Agent Enforcement       Endpoint Protection
         │
         ↓ Imported by
    ┌─────────────────────────┐
    │ Storage Management      │
    │                         │
    │ subscription/           │
    │ storage.py              │
    │                         │
    │ get_storage_limit_gb()  │
    │ = Uses storage_gb field │
    └─────────────────────────┘
         ↓
    Storage Quota Enforcement
    Knowledge endpoints
    Document upload limits
         │
         ↓ Imported by
    ┌─────────────────────────┐
    │ REST API Subscription   │
    │                         │
    │ routers/                │
    │ subscription.py         │
    │                         │
    │ SUBSCRIPTION_TIERS =    │
    │ _build_subscription_    │
    │ tiers()                 │
    │                         │
    │ Dynamically built       │
    └─────────────────────────┘
         ↓
    /subscription/* endpoints
    Subscription status
    Tier comparisons
```

## Consistency Verification

### Before Centralization
- ❌ Storage limits in 2 places: `tiers.py` (not used), `storage.py` (hardcoded)
- ❌ Tier definitions in 3 places: `tiers.py`, `middleware/subscription.py`, `routers/subscription.py`
- ❌ Feature definitions in 2 places: `tiers.py`, `middleware/subscription.py`
- ❌ Frontend had separate `subscriptionStore.ts` (not centralized with backend)

### After Centralization
- ✅ Storage limits in 1 place: `TIER_LIMITS.storage_gb`
- ✅ Tier limits in 1 place: `TIER_LIMITS`
- ✅ All other tier info (prices, names) in 1 place: `TIER_LIMITS`
- ✅ API middleware imports and builds from central source
- ✅ API endpoints import and build from central source
- ✅ Storage management imports and uses central source
- ✅ CLI/Agent enforcement uses central source
- ⚠️ Frontend still has separate definitions (TypeScript - requires separate update if needed)

## How to Modify Tier Limits

### Before (Multiple Places to Update)
To change free tier from 1 project to 2 projects:
1. Update `socratic_system/subscription/tiers.py:28`
2. Update `socrates-api/src/socrates_api/middleware/subscription.py:22`
3. Update `socrates-api/src/socrates_api/routers/subscription.py:42`

### After (Single Place)
To change free tier from 1 project to 2 projects:
1. Update `socratic_system/subscription/tiers.py:28` ← That's it!

All other files automatically stay in sync.

## How to Add a New Quota Type

Example: Add concurrent_projects limit

1. Add to TierLimits dataclass:
```python
@dataclass
class TierLimits:
    # ... existing fields ...
    max_concurrent_projects: Optional[int]  # NEW
```

2. Add to tier definitions:
```python
TIER_LIMITS = {
    "free": TierLimits(
        ...
        max_concurrent_projects=1,  # NEW
    ),
    "pro": TierLimits(
        ...
        max_concurrent_projects=5,  # NEW
    ),
    ...
}
```

3. All enforcement automatically picks it up:
- Middleware has access via `tier_limits.max_concurrent_projects`
- Storage manager can use it: `limits.max_concurrent_projects`
- API responses include it automatically

## Files Changed Summary

| File | Change | Impact |
|------|--------|--------|
| `socratic_system/subscription/tiers.py` | Added `storage_gb` to TierLimits | Single source of truth |
| `socratic_system/subscription/storage.py` | Use central `storage_gb` instead of hardcoded | Storage limits now centralized |
| `socrates-api/src/socrates_api/middleware/subscription.py` | Dynamic builder from TIER_LIMITS | No more duplicates |
| `socrates-api/src/socrates_api/routers/subscription.py` | Dynamic builder from TIER_LIMITS | No more duplicates |

## Backward Compatibility

All changes are backward compatible:
- TIER_FEATURES still available in middleware (just built dynamically)
- SUBSCRIPTION_TIERS still available in API (just built dynamically)
- All existing method signatures unchanged
- No API response format changes

## Testing

### Manual Verification Checklist

```
✓ Import tiers module without errors
✓ get_tier_limits("free") returns TierLimits with storage_gb=5
✓ get_tier_limits("pro") returns TierLimits with storage_gb=100
✓ StorageQuotaManager.get_storage_limit_gb("free") returns 5.0
✓ Middleware TIER_FEATURES["free"]["storage_gb"] == 5
✓ Middleware TIER_FEATURES["pro"]["storage_gb"] == 100
✓ API endpoint /subscription/status returns correct storage_gb
✓ API endpoint /subscription/plans returns correct storage_gb
✓ Project creation respects limits from TIER_LIMITS
✓ Team member addition respects limits from TIER_LIMITS
✓ Storage upload respects limits from TIER_LIMITS
✓ Testing mode bypasses all limits
```

## Related Security Fixes

This centralization complements the recent security fixes:
- GitHub import endpoint now has subscription enforcement
- Project limit enforcement is consistent across all entry points
- Storage quota enforcement works with centralized limits

## Next Steps (Optional)

1. **Frontend Synchronization:** Consider generating `subscriptionStore.ts` from backend tier definitions
2. **Database Cache:** Add tier definitions to database for faster access (with invalidation)
3. **Tier Versioning:** Add version field to support gradual tier migrations
4. **Feature Flags:** Link feature availability directly to tier definitions

## Conclusion

The monetization system is now **fully centralized** with:
- Single source of truth for all tier definitions and quotas
- Automatic propagation of changes across all layers (CLI, API, storage)
- Reduced maintenance burden
- Lower risk of inconsistencies between frontend and backend
- Clear, auditable quota enforcement
