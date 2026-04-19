# Debug & Subscription Testing-Mode Endpoints Analysis

## Executive Summary

Both systems implement testing-mode and debug endpoints, but with different architectures:
- **Monolithic**: CLI-based commands that affect global state
- **Modular**: REST API endpoints with middleware-based enforcement

The core mechanisms are the same, but integration points differ significantly.

---

## 1. TESTING-MODE ENDPOINTS

### Monolithic Implementation
- **Command**: `/subscription testing-mode on|off`
- **Mechanism**: CLI command that sets `user.testing_mode = True/False`
- **Effect**: Bypasses ALL subscription restrictions
- **File**: `socratic_system/ui/commands/subscription_commands.py`

### Modular Implementation
- **Endpoint**: `PUT /subscription/Romani Ite Domum?enabled=true|false`
- **Mechanism**: REST API route that sets `user.testing_mode = True/False`
- **Effect**: Bypasses ALL subscription restrictions via middleware
- **File**: `backend/src/socrates_api/routers/subscription.py` (lines 441-508)

### What Testing-Mode Does

When **ENABLED**:
1. Bypasses project creation limits
2. Bypasses team member limits
3. Bypasses storage quota limits
4. Bypasses question/month limits
5. Disables feature flag restrictions
6. Disables cost tracking

When **DISABLED**:
1. Re-enables all subscription tier enforcement
2. Reinstates all quota limitations
3. Enforces feature access based on tier

### Enforcement Mechanism

**Middleware check** (subscription.py, lines 194-197):
```python
@require_subscription_feature(feature_name)
def protected_endpoint(...):
    # BEFORE checking subscription
    if getattr(user, "testing_mode", False):
        logger.debug(f"Testing mode enabled, bypassing subscription check")
        return await func(*args, **kwargs)

    # Then check subscription tiers/features
    ...
```

---

## 2. DEBUG MODE ENDPOINTS

### Monolithic Implementation
- **Commands**:
  - `/debug on` - Enable debug logging
  - `/debug off` - Disable debug logging
  - `/debug` - Toggle debug mode
- **Mechanism**: Changes console logging level from ERROR to DEBUG
- **File**: `socratic_system/ui/commands/debug_commands.py`

### Modular Implementation
- **Endpoints**:
  - `POST /system/debug/toggle?enabled=true&scope=global|user` - Toggle debug
  - `GET /system/debug/status` - Get current debug status
  - `DELETE /system/debug/clear` - Clear per-user debug setting
  - `GET /system/debug/users` - List users with debug mode
- **Mechanism**: Manages in-memory state + optional database persistence
- **File**: `backend/src/socrates_api/routers/system.py` (lines 746-948)

### What Debug Mode Does

When **ENABLED**:
1. Console logging level: ERROR → DEBUG
2. All debug-level logs printed to console
3. Module-based colored output
4. Real-time system diagnostics visible

When **DISABLED**:
1. Console logging level: DEBUG → ERROR
2. Only ERROR level messages to console
3. File logging continues at DEBUG level regardless

### Scope Options (Modular Only)

**Global Debug Mode**:
- Affects ALL users
- Single `_debug_mode_global` variable
- Persists in-memory during session

**Per-User Debug Mode**:
- Overrides global setting for specific user
- User setting takes precedence
- Optional database persistence

---

## 3. KEY DIFFERENCES

| Feature | Monolithic | Modular |
|---------|-----------|---------|
| **Interface** | CLI commands | REST API endpoints |
| **Testing Mode Path** | `/subscription testing-mode` | `PUT /subscription/Romani Ite Domum` |
| **Testing Mode Scope** | Single user | Single user (CLI-based) |
| **Debug Path** | `/debug on\|off` | `POST /system/debug/toggle` |
| **Debug Scope** | Global only | Global + per-user |
| **State Storage** | Logger singleton | In-memory + optional database |
| **Persistence** | Always persistent to DB | In-memory for session |
| **Enforcement** | (To be migrated to middleware) | Centralized middleware decorators |
| **Security** | Hidden from help | Hidden from OpenAPI docs + obfuscated name |

---

## 4. CURRENT STATUS IN MODULAR SYSTEM

### ✅ IMPLEMENTED
- Testing-mode endpoint exists and toggles the flag
- Debug-mode endpoint exists and manages logging state
- Middleware decorators check `user.testing_mode` before subscription checks
- Per-user debug mode supported

### ❓ POTENTIALLY BROKEN
1. **Testing Mode Enforcement**: Is `testing_mode` checked in ALL protected endpoints?
2. **Debug Logging**: Is the debug mode toggle actually changing console logging levels?
3. **Scope Issues**: Does global debug mode affect all users correctly?
4. **Persistence**: Are per-user debug settings persisted to database?
5. **Integration**: Are all subscription decorators using the middleware checks?

---

## 5. INTEGRATION POINTS TO VERIFY

### Testing Mode Integration
Should be checked BEFORE every subscription validation:
1. `@require_subscription_tier(tier)`
2. `@require_subscription_feature(feature)`
3. `@require_quota(resource_name)`
4. `@limit_projects_per_user()`

### Debug Mode Integration
Should affect:
1. All module loggers (via Python logging system)
2. Console handler level changes
3. Real-time logging visibility

---

## 6. CRITICAL IMPLEMENTATION DETAILS

### Testing Mode Flag Storage
```python
# Located on User model
user.testing_mode: bool = False

# Persisted to database
db.save_user(user)

# Checked before EVERY subscription validation
if getattr(user, "testing_mode", False):
    # Bypass subscription check
    return
```

### Debug Mode State Management
```python
# Global state
_debug_mode_global: bool = False
_debug_mode_users: Dict[str, bool] = {}

# Effective state calculation
effective_debug = _debug_mode_users.get(user_id, _debug_mode_global)

# Logging level change
if effective_debug:
    console_handler.setLevel(logging.DEBUG)
else:
    console_handler.setLevel(logging.ERROR)
```

---

## 7. POTENTIAL ISSUES

### Issue 1: Testing Mode Not Checked Everywhere
**Symptom**: Some protected endpoints bypass testing mode check
**Location**: Any `@require_subscription_*` decorator without middleware integration
**Fix**: Ensure ALL subscription checks go through middleware that verifies testing_mode

### Issue 2: Debug Mode Doesn't Affect Logging
**Symptom**: `/system/debug/toggle` endpoint works but logs don't change
**Location**: Logging handler configuration not being updated
**Fix**: Verify handler levels are actually being changed in logging system

### Issue 3: Per-User Debug Not Persistent
**Symptom**: Per-user debug mode resets on app restart
**Location**: State stored only in-memory, not in database
**Fix**: Add database persistence for per-user debug settings

### Issue 4: Scope Conflicts
**Symptom**: Global debug affecting per-user settings incorrectly
**Location**: Calculation of effective_debug state
**Fix**: Ensure per-user settings properly override global settings

---

## 8. ACTION ITEMS FOR TESTING

1. **Test Testing Mode**:
   - Enable testing mode: `PUT /subscription/Romani Ite Domum?enabled=true`
   - Try creating project beyond limit
   - Try adding team members beyond limit
   - Verify no restriction messages appear

2. **Test Debug Mode Global**:
   - Enable global: `POST /system/debug/toggle?scope=global&enabled=true`
   - Check console output becomes verbose
   - Check logs show DEBUG level messages
   - Disable and verify goes back to ERROR level

3. **Test Debug Mode Per-User**:
   - Enable for specific user: `POST /system/debug/toggle?scope=user&enabled=true`
   - Verify only that user's logs are verbose
   - Verify other users remain at ERROR level
   - Check status: `GET /system/debug/status`

4. **Test Obfuscation**:
   - Verify `/subscription/Romani Ite Domum` not in OpenAPI docs
   - Verify endpoint name not in help/swagger
   - Production environment should block this endpoint

---

## 9. RECOMMENDATIONS

### For Immediate Testing
1. Call `/subscription/Romani Ite Domum?enabled=true` to enable testing mode
2. Call `POST /system/debug/toggle?scope=user&enabled=true` to enable debug for current user
3. Perform normal operations and verify restrictions are bypassed
4. Check console output shows DEBUG level logs

### For Production Safety
1. Keep `Romani Ite Domum` endpoint hidden from documentation
2. Add audit logging for testing mode toggles
3. Require special authentication for global debug mode
4. Add time-limit expiration for testing mode
5. Log who enabled/disabled testing or debug modes

---

## 10. FILES TO CHECK

- ✅ `/backend/src/socrates_api/routers/subscription.py` - Testing mode endpoint (implemented)
- ✅ `/backend/src/socrates_api/routers/system.py` - Debug mode endpoints (implemented)
- ⚠️ `/backend/src/socrates_api/middleware/subscription.py` - Verify testing_mode check
- ⚠️ All `@require_subscription_*` decorators - Verify they use middleware
- ⚠️ Logging configuration - Verify handler levels change with debug toggle

