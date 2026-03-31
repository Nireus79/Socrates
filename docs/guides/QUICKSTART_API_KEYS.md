# Quick Start: Add Your First API Key (5 minutes)

## Option A: Web UI (Recommended)

### Step 1: Start Socrates
```bash
# Terminal 1: Backend
cd backend && python -m socrates_api.main

# Terminal 2: Frontend
cd socrates-frontend && npm run dev
```

### Step 2: Login
- Go to http://localhost:3000
- Login with your credentials

### Step 3: Add API Key
1. Click **Settings** (top right menu)
2. Click **LLM Providers** tab
3. Choose a provider:
   - **OpenAI**: Click [+], paste `sk-...` from https://platform.openai.com/api-keys
   - **Claude**: Click [+], paste from https://console.anthropic.com
   - **Gemini**: Click [+], paste from https://ai.google.dev
4. Click **Save API Key**
5. Click **Set as Default** (optional)

### Step 4: Test It
1. Go to **Chat**
2. Ask a question
3. ✓ You should get AI-generated responses (not hardcoded questions)

---

## Option B: Terminal CLI

### Add OpenAI API Key
```bash
/llm key add openai sk-your-actual-openai-key
/llm set openai  # Make it default
/llm config      # Verify it worked
```

### Add Claude API Key
```bash
/llm key add claude sk-ant-your-actual-claude-key
/llm set claude
```

### Add Gemini API Key
```bash
/llm key add gemini AIzaSy-your-actual-gemini-key
```

---

## Verify It's Working

### Check Configuration
```bash
/llm config
```

You should see:
```
Default Provider: openai
api_key_configured: true
using_global_key: false
```

### Test in Chat
1. Go to Chat page
2. Ask: "What's a Python decorator?"
3. If you get an AI-generated question → ✓ It works!
4. If you get "What do you already know..." → ❌ Key not configured

---

## Troubleshooting

### "Still getting hardcoded questions?"
1. Verify backend restarted (after adding key)
2. Refresh browser (Ctrl+Shift+R)
3. Check: `/llm config` shows `api_key_configured: true`
4. Try a different provider

### "Invalid API Key error?"
1. Copy key exactly from provider's website
2. No extra spaces or quotes
3. Check API key is still active on provider's account

### "Provider not found?"
```bash
/llm list  # See available providers
```

---

## What Gets Saved

✅ **Your API key** - Encrypted with Fernet encryption
✅ **Your preference** - Which provider to use by default
✅ **Your model choice** - Which model to use (gpt-4, claude-3-sonnet, etc.)

❌ **NOT saved in code** - No hardcoded keys
❌ **NOT in logs** - Keys never logged
❌ **NOT visible elsewhere** - Only you see your key

---

## Provider Costs

| Provider | Cost | Notes |
|----------|------|-------|
| **Claude** | $0.80/1M input tokens | Free trial: $5 credit |
| **OpenAI** | $0.01/1K input tokens | Pay-as-you-go |
| **Gemini** | $0.0005/1K input tokens | Cheapest option |
| **Ollama** | FREE | Run locally, no internet |

---

## API Key Locations

| Provider | Get Key From |
|----------|-------------|
| Claude | https://console.anthropic.com/account/keys |
| OpenAI | https://platform.openai.com/account/api-keys |
| Gemini | https://ai.google.dev/tutorials/setup |
| Ollama | Install locally at https://ollama.com |

---

## Done! 🎉

Your API key is now:
- ✓ Encrypted in the database
- ✓ Automatically used for all requests
- ✓ Never exposed or logged
- ✓ Ready to power intelligent responses

**Next**: Try asking Socrates a technical question and let the AI help guide you through it!
