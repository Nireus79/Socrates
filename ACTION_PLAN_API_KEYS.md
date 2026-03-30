# Action Plan: Enable API Key Input & Connect to LLM

## Current Status

✅ **Backend code updated**: Provider metadata fix deployed
✅ **Encryption configured**: Database encryption enabled in .env
✅ **CLI commands ready**: `/llm key add ...` works (if backend restarted)
❌ **UI input field**: Not visible until backend is restarted

## Why UI Input Not Showing

The old backend (still running) returns incomplete provider data:
- Missing `label`, `models[]`, `requires_api_key` fields
- Frontend can't render API key input without these fields

## Fix: Restart Backend (2 steps)

### Step 1: Stop & Restart Backend
```bash
# Kill old backend process
# Ctrl+C in the terminal where backend is running

# Then restart with new code
cd backend
python -m socrates_api.main
```

**Expected output**:
```
INFO: Socrates API Server starting...
INFO: Updated /llm/providers endpoint with complete metadata ✓
INFO: Orchestrator initialized with real agents
```

### Step 2: Refresh Frontend
- Go to http://localhost:3000
- **Hard refresh**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)

---

## Test: API Key Input Should Now Appear

### In Browser:
1. Click **Settings** (top right corner)
2. Click **LLM Providers** tab
3. You should see 4 provider cards:
   - Claude (Anthropic)
   - OpenAI
   - Gemini (Google)
   - Ollama (Local)
4. Click **[+]** button on any card to expand
5. You should now see:
   ```
   API Key
   Paste your API key here
   [Input field here] [👁 Show]
   [Save API Key] [Remove]
   ```

### If You See the Input Field ✅

1. Get your API key:
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Claude**: https://console.anthropic.com
   - **Gemini**: https://ai.google.dev
   - **Ollama**: No key needed (local)

2. Paste key into the input field

3. Click **Save API Key**

4. Go to **Chat** page

5. Ask a question

6. **You should get AI-generated response!**

---

## Complete End-to-End Flow

```
You (User)
    ↓
Browser: Settings → LLM Providers
    ↓
[+] Click to expand provider → API Key input appears ✓
    ↓
Paste: sk-your-actual-api-key
    ↓
[Save API Key] button
    ↓
Key sent to: POST /llm/api-key
    ↓
Backend: Database saves encrypted key
    ↓
Key stored as: enc:fernet-encrypted-data
    ↓
Go to Chat page
    ↓
Ask: "How do I build a Python calculator?"
    ↓
Backend retrieves your saved key
    ↓
Creates LLMClient with your key
    ↓
SocraticCounselor generates AI question:
"Well, to build a calculator, what programming
language are you thinking of using?"
    ↓
No more hardcoded questions! ✓
```

---

## What Happens Behind the Scenes

### When You Save API Key:
1. Frontend sends: `POST /llm/api-key?provider=openai&api_key=sk-...`
2. Backend receives request with user_id
3. Database encrypts key with master encryption key
4. Stores in database: `(user_id, provider, encrypted_key, key_hash)`
5. Response: `{"success": true, "data": {"provider": "openai"}}`

### When You Ask Question:
1. Request arrives with your user_id
2. Backend retrieves your default provider
3. Database retrieves & decrypts your stored API key
4. Creates: `LLMClient(provider="openai", model="gpt-4-turbo", api_key=your_key)`
5. SocraticCounselor uses LLMClient to generate question
6. Question returned (not hardcoded!)

### Security:
- ✅ Keys encrypted (Fernet) in database
- ✅ Keys decrypted only when needed
- ✅ Never logged or exposed
- ✅ Only used for your requests
- ✅ Inaccessible to other users

---

## Files You Need To Know About

### Documentation (Read These)
- **`QUICKSTART_API_KEYS.md`** ← Start here (5 min read)
- **`LLM_API_KEY_SETUP_GUIDE.md`** ← Detailed guide (full reference)
- **`FIX_NO_API_KEY_INPUT.md`** ← Troubleshooting
- **`IMPLEMENTATION_SUMMARY.md`** ← Technical details

### Code Changed
- **`backend/src/socrates_api/orchestrator.py`** ← Provider metadata endpoint
- **`.env`** ← Encryption configuration

### Test Script
- **`test_llm_api_key_setup.py`** ← Run to verify everything works

---

## 30-Second Summary

1. **Stop backend** (Ctrl+C)
2. **Restart backend** (`cd backend && python -m socrates_api.main`)
3. **Refresh browser** (Ctrl+Shift+R)
4. **Go to Settings → LLM Providers**
5. **Click [+] on a provider**
6. **Paste API key and save**
7. **Go to Chat and ask a question**
8. **Get AI response** ✓

---

## Verify It's Working

### Quick Test
```bash
/llm config
```

Should show:
```
Default Provider: openai
✓ API Key Configured
Model: gpt-4-turbo
```

### Full Test
```bash
python test_llm_api_key_setup.py
```

All 6 tests should PASS.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Still no API key input field | Restart backend, hard refresh (Ctrl+Shift+R) |
| "Invalid API key" error | Check key copied correctly from provider |
| Still getting hardcoded questions | Verify `/llm config` shows `api_key_configured: true` |
| Backend won't start | Check: `python --version` (need 3.8+), `pip install -r requirements.txt` |
| Backend starts but API key not working | Check `.env` has encryption settings, restart backend |

---

## Success Criteria

✓ Go to Settings → LLM Providers
✓ See provider cards with [+] buttons
✓ Click [+] to expand provider
✓ See "API Key" input field
✓ Paste and save API key
✓ Go to Chat
✓ Ask a question
✓ Get AI-generated response (not hardcoded)
✓ Backend logs show "Using user API key..."

---

## Next Steps After Success

1. **Try different models**:
   ```bash
   /llm use openai gpt-4-turbo
   /llm use claude claude-3-5-sonnet-20241022
   ```

2. **Set default provider**:
   ```bash
   /llm set claude
   ```

3. **Check costs**:
   ```bash
   /llm stats openai 7
   ```

4. **Use in Socratic dialogue**:
   - Ask questions in chat
   - Get AI-guided learning
   - System tracks your progress

---

## Documentation Structure

```
FIX_NO_API_KEY_INPUT.md
    ↑
    └─ Read this first if input field not showing

ACTION_PLAN_API_KEYS.md (this file)
    ↑
    └─ High-level overview & next steps

QUICKSTART_API_KEYS.md
    ↑
    └─ 5-minute setup guide

LLM_API_KEY_SETUP_GUIDE.md
    ↑
    └─ Complete reference (all details)

IMPLEMENTATION_SUMMARY.md
    ↑
    └─ Technical architecture (for developers)

test_llm_api_key_setup.py
    ↑
    └─ Automated verification script
```

---

## Final Checklist

- [ ] Restarted backend ✓
- [ ] Refreshed frontend ✓
- [ ] Can see provider cards ✓
- [ ] Can expand providers ✓
- [ ] Can see API key input field ✓
- [ ] Can save API key ✓
- [ ] Can ask question in chat ✓
- [ ] Getting AI response (not hardcoded) ✓
- [ ] Backend logs show "Using user API key..." ✓

**When all checked**: You're ready to use Socrates with LLM support!

---

## Support

If something doesn't work:

1. **Check the logs**:
   - Backend terminal: Look for errors
   - Browser console (F12): Look for JavaScript errors

2. **Run the test**:
   ```bash
   python test_llm_api_key_setup.py
   ```

3. **Read the guide**:
   - `FIX_NO_API_KEY_INPUT.md` - Most common issues
   - `LLM_API_KEY_SETUP_GUIDE.md` - Full reference

4. **Check network tab**:
   - F12 → Network tab
   - Look for `/llm/providers` request
   - Check response has `label`, `requires_api_key`, `models`

---

**You're all set! 🚀 Start using Socrates with AI-powered guidance!**
