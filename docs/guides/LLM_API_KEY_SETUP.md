# Complete API Key Management Setup Guide

This guide walks you through setting up API keys for LLM providers in Socrates so the system can connect to Claude, OpenAI, Gemini, or Ollama.

## Overview

Socrates now has complete multi-provider LLM support with:
- ✅ UI form for entering API keys (Settings → LLM Providers)
- ✅ CLI commands for API key management
- ✅ Encrypted database storage (Fernet encryption)
- ✅ Automatic LLM client creation with user's API key

## Prerequisites

1. **Start the Socrates backend and frontend**
   ```bash
   # Terminal 1: Start backend
   cd backend
   python -m socrates_api.main

   # Terminal 2: Start frontend
   cd socrates-frontend
   npm run dev
   ```

2. **Encryption is enabled in `.env`**
   ```env
   SECURITY_DATABASE_ENCRYPTION=true
   DATABASE_ENCRYPTION_KEY=SocrateMasterKey32CharacterString123456
   ```

## Method 1: Web UI (Recommended for Users)

### Step 1: Login to Socrates
- Navigate to http://localhost:3000
- Login with your account

### Step 2: Go to Settings
- Click your profile/avatar (top-right)
- Select **Settings**

### Step 3: Select LLM Providers Tab
- You'll see a "LLM Providers" tab with 4 providers:
  - **Claude** (Anthropic) - No API key required (uses subscription)
  - **OpenAI** - Requires API key
  - **Gemini** (Google) - Requires API key
  - **Ollama** (Local) - No API key required

### Step 4: Add API Key

For **Claude** (if using API key instead of subscription):
1. Click the **+** button on the Claude card to expand
2. Paste your Claude API key from https://console.anthropic.com
3. Click **Save API Key**
4. Select your preferred model
5. Click **Set as Default**

For **OpenAI**:
1. Click the **+** button to expand the OpenAI card
2. Paste your OpenAI API key from https://platform.openai.com/api-keys
3. Click **Save API Key**
4. Select your preferred model (gpt-4-turbo, gpt-4, gpt-3.5-turbo)
5. Click **Set as Default** (if you want OpenAI as default)

For **Gemini**:
1. Click the **+** button to expand the Gemini card
2. Paste your Google Gemini API key from https://ai.google.dev
3. Click **Save API Key**
4. Click **Set as Default** (if you want Gemini as default)

### Step 5: Verify Configuration
- Check the "Current Configuration" section at top
- You should see your default provider selected
- Badge should show "✓ Active" on the provider card

---

## Method 2: Terminal CLI Commands

### Step 1: List Available Providers
```bash
/llm list
```

Output shows all 4 providers with their models and capabilities.

### Step 2: Add API Key

**Add Claude API Key:**
```bash
/llm key add claude sk-ant-... # Replace with your actual API key
```

**Add OpenAI API Key:**
```bash
/llm key add openai sk-... # Replace with your actual OpenAI key
```

**Add Gemini API Key:**
```bash
/llm key add gemini AIzaSy... # Replace with your actual Gemini key
```

**Add Ollama (if running locally):**
```bash
# No API key needed - Ollama uses local connection
/llm set ollama
/llm use ollama llama2
```

### Step 3: Set Default Provider
```bash
/llm set openai  # Sets OpenAI as default
/llm set claude  # Sets Claude as default
```

### Step 4: Select Specific Model
```bash
/llm use openai gpt-4-turbo      # Use GPT-4 Turbo for OpenAI
/llm use claude claude-3-5-sonnet-20241022  # Use Sonnet for Claude
```

### Step 5: Verify Configuration
```bash
/llm config
```

Shows your current default provider, configured providers, and models.

---

## Security & Encryption

### How API Keys Are Stored

1. **Encryption**: All API keys are encrypted using Fernet symmetric encryption
   - Master key: `DATABASE_ENCRYPTION_KEY` environment variable
   - Storage: SQLite database with `encrypted_key` field
   - Format: Keys stored with "enc:" prefix to indicate encryption

2. **Protection**:
   - Keys are NEVER logged or exposed in responses
   - Keys are NEVER included in API responses
   - Only the `APIKeyRecord.to_dict()` output excludes the encrypted key
   - Hash verification without decryption is possible

3. **Access Control**:
   - Each user's API key is associated with their user_id
   - Keys are retrieved only when making LLM requests for that user
   - Keys are NOT visible to other users

### Environment Variables
```env
# Enable/disable encryption
SECURITY_DATABASE_ENCRYPTION=true

# 32-character master encryption key (generate new one for production!)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
DATABASE_ENCRYPTION_KEY=your-32-char-key-here
```

---

## How It Works End-to-End

### User Flow:
1. **User enters API key** via UI (Settings → LLM Providers) or CLI (`/llm key add provider key`)
2. **Key is encrypted** using Fernet with master encryption key
3. **Key is stored** in database with user_id and provider
4. **Key is retrieved** when user asks a question (creates LLM client)
5. **LLM processes request** using user's API key
6. **Key is NOT logged** or exposed anywhere

### Example Request Flow:

```
User asks question in chat
    ↓
Backend receives request with user_id
    ↓
Orchestrator retrieves user's stored API key for default provider
    ↓
API key is decrypted from database
    ↓
LLMClient created with decrypted API key
    ↓
SocraticCounselor uses LLMClient to generate question
    ↓
Question returned to user
    ↓
API key is NOT stored in response or logs
```

---

## Testing API Key Setup

### Test 1: Verify Key is Encrypted in Database
```python
# Python script to verify encryption
from socratic_system.database import DatabaseSingleton
from socratic_system.database.encryption import decrypt_field

db = DatabaseSingleton.get_instance()
api_key = db.get_api_key(user_id="testuser", provider="openai")
print(f"Retrieved key: {api_key[:10]}...")  # Shows first 10 chars only
```

### Test 2: Verify LLM Connection Works
1. Add an API key via UI or CLI
2. Go to Chat page
3. Ask a question in the socratic dialogue
4. You should get AI-generated questions instead of hardcoded fallback

### Test 3: Verify Key is Used for Requests
Enable debug logging:
```python
import logging
logging.getLogger("socratic_system").setLevel(logging.DEBUG)
logging.getLogger("socrates_api").setLevel(logging.DEBUG)
```

You should see logs like:
```
Using user API key for user {user_id} with provider openai/gpt-4-turbo
LLM client created successfully
```

---

## Troubleshooting

### Issue: "No API Key Provided" / Hardcoded Questions Still Appearing

**Cause**: API key hasn't been saved or isn't being retrieved

**Solution**:
1. Verify encryption is enabled: Check `.env` has `SECURITY_DATABASE_ENCRYPTION=true`
2. Verify you added the key: `/llm config` should show `api_key_configured: true`
3. Check database directly:
   ```python
   from socratic_system.database import DatabaseSingleton
   db = DatabaseSingleton.get_instance()
   key = db.get_api_key("your_username", "claude")
   print("Key found:", key is not None)
   ```

### Issue: "Invalid API Key" / Request Fails

**Cause**: API key is incorrect or provider is unreachable

**Solution**:
1. Verify the API key is correct (copy from provider's website)
2. Check provider is available:
   - Claude: https://api.anthropic.com must be reachable
   - OpenAI: https://api.openai.com must be reachable
   - Gemini: https://generativelanguage.googleapis.com must be reachable
3. Check rate limits on provider's account

### Issue: Encryption Not Working

**Cause**: `DATABASE_ENCRYPTION_KEY` not set or invalid

**Solution**:
1. Generate a new encryption key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Add to `.env`:
   ```env
   DATABASE_ENCRYPTION_KEY=<paste-generated-key>
   ```
3. Restart the application
4. Re-add API keys (old ones won't decrypt with new key)

---

## API Endpoints Reference

All endpoints require authentication (JWT token).

### List Providers
```
GET /llm/providers
Response: {
  "providers": [
    {
      "name": "claude",
      "display_name": "Anthropic Claude",
      "requires_api_key": false,
      "is_configured": true,
      "models": ["claude-3-5-sonnet-20241022", ...],
      ...
    }
  ]
}
```

### Add API Key
```
POST /llm/api-key?provider=openai&api_key=sk-...
Response: {"success": true, "data": {"provider": "openai"}}
```

### Get Configuration
```
GET /llm/config
Response: {
  "default_provider": "claude",
  "current_model": "claude-3-5-sonnet-20241022",
  "api_key_configured": true,
  "using_global_key": false
}
```

### Remove API Key
```
DELETE /llm/api-key/{provider}
Response: {"success": true, "message": "API key removed for {provider}"}
```

---

## Summary

✅ **Complete Infrastructure in Place**:
- Provider metadata with all 4 providers (Claude, OpenAI, Gemini, Ollama)
- UI form with expandable provider cards and API key input
- CLI commands for terminal-based setup
- Encrypted database storage with Fernet
- Automatic LLM client creation with user's API key

✅ **Users Can Now**:
1. Add API keys via Web UI or Terminal
2. Select default provider
3. Choose preferred models
4. Get AI-generated responses instead of hardcoded questions
5. Have keys safely encrypted in database

**Next Step**: Open Socrates, go to Settings → LLM Providers, and add your first API key!
