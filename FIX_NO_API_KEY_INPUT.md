# Fix: No API Key Input Field in UI

## The Problem

The API key input field exists in the code but doesn't show in the running application.

## Root Cause

The backend `/llm/providers` endpoint returns incomplete provider data:

**Old (broken) format**:
```json
{
  "name": "anthropic",
  "model": "claude-3-sonnet",      // ← Wrong: should be array
  "configured": true,               // ← Wrong: should be is_configured
  "status": "active"                // ← Missing all other fields
}
```

**New (fixed) format**:
```json
{
  "name": "claude",
  "label": "Anthropic Claude",       // ← NEW: Display name
  "models": ["claude-3-5-sonnet-20241022", ...],  // ← NEW: Array
  "requires_api_key": false,         // ← NEW: Determines if input shows
  "is_configured": true,             // ← FIXED: Correct field name
  "description": "Fast and efficient Claude...",  // ← NEW
  "context_window": 200000,          // ← NEW
  // ... plus other fields
}
```

The frontend component expects `requires_api_key` to show the input field (line 309).

## Solution

### Step 1: Stop Old Backend
```bash
# If backend is running, stop it (Ctrl+C)
# This kills the old process with incomplete provider data
```

### Step 2: Pull Latest Code
```bash
cd /path/to/Socrates
git pull
```

### Step 3: Restart Backend
```bash
cd backend
python -m socrates_api.main
```

You should see in the logs:
```
INFO: Updated /llm/providers endpoint to return complete metadata ✓
```

### Step 4: Refresh Frontend
- Go to http://localhost:3000
- Full page refresh: **Ctrl+Shift+R** (or Cmd+Shift+R on Mac)
- Clear browser cache if needed

### Step 5: Navigate to Settings
1. Click Settings (top right)
2. Click **LLM Providers** tab
3. You should now see provider cards

### Step 6: Expand Provider and Add Key
1. Click the **[+]** button on a provider card
2. You should now see:
   ```
   ┌─────────────────────────────┐
   │ OpenAI                  [X] │
   ├─────────────────────────────┤
   │ API Key                     │
   │ Enter your API key...       │
   │ [Input field] [👁 icon]     │
   │ [Save API Key] [Remove]     │
   └─────────────────────────────┘
   ```

---

## Verify the Fix

### Check 1: Backend Logs
Look for this message when backend starts:
```
INFO: Updated /llm/providers endpoint ✓
```

### Check 2: Network Tab
In browser DevTools (F12):
1. Go to Network tab
2. Refresh the settings page
3. Look for request to `/llm/providers`
4. Click it and check Response
5. Should contain `"label"`, `"models"`, `"requires_api_key"`

**Old response** ❌:
```json
{"providers": [{"name": "anthropic", "model": "claude-3-sonnet", ...}]}
```

**New response** ✅:
```json
{
  "providers": [{
    "name": "claude",
    "label": "Anthropic Claude",
    "models": ["claude-3-5-sonnet-20241022"],
    "requires_api_key": false,
    ...
  }]
}
```

### Check 3: Frontend Console
In browser DevTools (F12 → Console):
- No errors should appear
- Provider data should log correctly

---

## If Still Not Working

### Option 1: Hard Reset Frontend Cache
```bash
# Clear all browser data for localhost:3000
# In Chrome: Settings → Privacy → Clear browsing data
# Select: Cookies and cached images/files
# Time range: All time
# Then refresh page
```

### Option 2: Rebuild Frontend
```bash
cd socrates-frontend
npm run build
npm run dev
```

### Option 3: Check Backend is Running Correctly
```bash
# In backend terminal, look for:
# ✓ Orchestrator initialized with real agents
# ✓ Updated /llm/providers endpoint ✓

# If you see errors, check:
python -c "from socratic_system.models.llm_provider import list_available_providers; print(list_available_providers())"
```

### Option 4: Manual Database Test
```python
from socratic_system.database import DatabaseSingleton
from socratic_system.models.llm_provider import list_available_providers

# Check providers
providers = list_available_providers()
print(f"Found {len(providers)} providers")
for p in providers:
    print(f"  - {p.display_name}: requires_api_key={p.requires_api_key}")
```

---

## What Changed

**File modified**: `backend/src/socrates_api/orchestrator.py`

**Change**: Lines 723-755 (list_providers action)

**Before**:
```python
# Returned hardcoded incomplete data
providers = []
if self.llm_client:
    providers.append({
        "name": "anthropic",
        "model": "claude-3-sonnet",
        "configured": True,
        "status": "active",
    })
```

**After**:
```python
# Returns complete provider metadata from database
from socratic_system.models.llm_provider import list_available_providers

for provider_meta in list_available_providers():
    provider_dict = provider_meta.to_dict()

    # Check if user configured (has API key)
    if user_id:
        user_api_key = db.get_api_key(user_id, provider_meta.provider)
        provider_dict["is_configured"] = bool(user_api_key)
    else:
        provider_dict["is_configured"] = False

    providers.append(provider_dict)
```

---

## Quick Checklist

- [ ] Stopped old backend (Ctrl+C)
- [ ] Restarted backend with new code
- [ ] Refreshed frontend (Ctrl+Shift+R)
- [ ] See provider cards in Settings → LLM Providers
- [ ] Can expand provider cards with [+] button
- [ ] See "API Key" input field when expanded
- [ ] Can paste and save API key
- [ ] Backend logs show "Using user API key..."

---

## Now You Should Be Able To:

✓ Go to Settings → LLM Providers
✓ Click [+] on a provider card
✓ See input field: "Paste your API key here"
✓ Paste API key and click Save
✓ Backend uses the key for requests
✓ Get AI-generated responses (no more hardcoded questions!)

---

## Still Issues?

1. **Provider cards not showing at all**
   - Clear browser cache (Ctrl+Shift+Delete)
   - Hard refresh (Ctrl+Shift+R)
   - Check Network tab for `/llm/providers` response

2. **Backend not starting**
   - Check Python version: `python --version` (need 3.8+)
   - Check dependencies: `pip install -r requirements.txt`
   - Check logs for specific error

3. **API key input field still missing**
   - Check Network tab - are provider cards getting `requires_api_key: true`?
   - Open browser console (F12) - any errors?
   - Run test: `python test_llm_api_key_setup.py`

---

## Contact

If you're still stuck:
1. Run: `python test_llm_api_key_setup.py`
2. Check backend logs for errors
3. Check browser console (F12 → Console) for JavaScript errors
4. Verify `/llm/providers` response in Network tab
