# Local GitHub Sponsors Webhook Testing with ngrok

Guide to test GitHub Sponsors webhook integration locally using ngrok.

## Prerequisites

1. **Socrates running locally**: `http://localhost:8000`
2. **Python installed** with `requests` library: `pip install requests`
3. **ngrok installed**: Download from https://ngrok.com/download
4. **GitHub API Key**: Set as `GITHUB_API_KEY` environment variable
5. **Webhook Secret**: Already in `.env.local` (or generate new: `openssl rand -hex 32`)

---

## Step 1: Start ngrok

ngrok exposes your local server to the internet so GitHub can reach it.

### Mac/Linux:
```bash
# If ngrok is installed globally
ngrok http 8000

# Or if installed locally
./ngrok http 8000
```

### Windows (PowerShell):
```powershell
# If ngrok is in PATH
ngrok http 8000

# Or navigate to ngrok folder
.\ngrok.exe http 8000
```

**Output will show:**
```
ngrok                                                       (Ctrl+C to quit)

Session Status                online
Account                       you@example.com
Version                       3.x.x
Region                        us (United States)
Latency                       15ms
Web Interface                 http://127.0.0.1:4040

Forwarding                    https://abc123xyz.ngrok.io -> http://localhost:8000
```

**Copy the HTTPS URL**: `https://abc123xyz.ngrok.io`

---

## Step 2: Register Webhook with GitHub

Now register the webhook pointing to your ngrok URL.

### Option A: Using the Setup Script (Recommended)

```bash
python setup_github_sponsors_webhook.py \
  --url https://abc123xyz.ngrok.io \
  --secret $(cat deployment/configurations/.env.local | grep GITHUB_WEBHOOK_SECRET | cut -d= -f2)
```

### Option B: Manual Setup

```bash
# Set variables
NGROK_URL="https://abc123xyz.ngrok.io"
WEBHOOK_SECRET=$(cat deployment/configurations/.env.local | grep GITHUB_WEBHOOK_SECRET | cut -d= -f2)

# Register webhook
python setup_github_sponsors_webhook.py \
  --url $NGROK_URL \
  --secret $WEBHOOK_SECRET
```

### Option C: Manual GitHub UI Setup

1. Go to: https://github.com/Nireus79/Socrates/settings/hooks
2. Click "Add webhook"
3. **Payload URL**: `https://abc123xyz.ngrok.io/sponsorships/webhooks/github-sponsors`
4. **Content type**: `application/json`
5. **Secret**: Paste your `GITHUB_WEBHOOK_SECRET` value
6. **Events**: Select "Sponsorship"
7. **Active**: ✓ Check
8. Click "Add webhook"

---

## Step 3: Test the Webhook

### View Webhook in Web Interface

ngrok provides a web interface to see all HTTP requests:

```
http://127.0.0.1:4040
```

You'll see:
- All requests to your local server
- Request/response headers
- Request/response body
- Status codes

### Send Test Webhook

Use the provided test script or curl:

```bash
# Using our test helper
python -c "
import requests
import hmac
import hashlib
import json

# Read webhook secret from .env.local
with open('deployment/configurations/.env.local') as f:
    for line in f:
        if 'GITHUB_WEBHOOK_SECRET=' in line:
            secret = line.split('=')[1].strip()
            break

# Create test payload
payload = json.dumps({
    'action': 'created',
    'sponsorship': {
        'sponsor': {'login': 'testuser', 'id': 12345},
        'tier': {'monthly_price_in_cents': 500}
    }
}).encode()

# Calculate signature
sig = 'sha256=' + hmac.new(
    secret.encode(), payload, hashlib.sha256
).hexdigest()

# Send request
headers = {
    'Content-Type': 'application/json',
    'X-Hub-Signature-256': sig
}

response = requests.post(
    'http://localhost:8000/sponsorships/webhooks/github-sponsors',
    data=payload,
    headers=headers
)

print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
"
```

Or using curl:

```bash
#!/bin/bash

SECRET=$(cat deployment/configurations/.env.local | grep GITHUB_WEBHOOK_SECRET | cut -d= -f2)
PAYLOAD='{"action":"created","sponsorship":{"sponsor":{"login":"testuser","id":12345},"tier":{"monthly_price_in_cents":500}}}'

# Calculate signature
SIG="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)"

# Send request
curl -X POST http://localhost:8000/sponsorships/webhooks/github-sponsors \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: $SIG" \
  -d "$PAYLOAD"
```

---

## Step 4: Verify in ngrok Web Interface

1. Open http://127.0.0.1:4040
2. Look for POST request to `/sponsorships/webhooks/github-sponsors`
3. Check **Status**: Should be `200 OK`
4. Check **Response body**: Should show success message

---

## Step 5: Check Database

Verify the sponsorship was recorded:

```bash
# Connect to database
sqlite3 socrates.db

# Check sponsorships table
SELECT * FROM sponsorships WHERE github_username = 'testuser';

# Check if user tier was updated
SELECT username, subscription_tier, subscription_status FROM users WHERE username = 'testuser';
```

---

## Troubleshooting

### Webhook Not Receiving Requests

1. **Check ngrok is running**:
   ```bash
   curl https://abc123xyz.ngrok.io/docs
   ```
   Should return Socrates API documentation

2. **Check webhook registered**:
   ```bash
   python setup_github_sponsors_webhook.py --list
   ```

3. **Check ngrok URL correct**:
   - Make sure webhook URL in GitHub = your ngrok URL
   - Check for typos in https://github.com/Nireus79/Socrates/settings/hooks

### 403 Forbidden Error

**Cause**: Invalid webhook signature

1. **Verify secret matches**:
   ```bash
   echo $GITHUB_WEBHOOK_SECRET
   # Should match what's in GitHub webhook settings
   ```

2. **Verify .env.local loaded**:
   ```bash
   cat deployment/configurations/.env.local | grep GITHUB_WEBHOOK_SECRET
   ```

3. **Re-generate secret if needed**:
   ```bash
   openssl rand -hex 32 > /tmp/new_secret.txt
   cat /tmp/new_secret.txt
   # Update in .env.local AND GitHub webhook settings
   ```

### 404 Not Found

**Cause**: ngrok URL not accessible

1. **Check ngrok status**: Look at terminal where ngrok is running
2. **Check Socrates is running**: `curl http://localhost:8000/docs`
3. **Check ngrok forwarding**: Terminal should show `Forwarding: https://xxx.ngrok.io -> http://localhost:8000`

### 500 Internal Server Error

**Cause**: Error in webhook handler

1. **Check Socrates logs**:
   ```bash
   tail -f /path/to/socrates.log | grep sponsorship
   ```

2. **Check database tables exist**:
   ```bash
   sqlite3 socrates.db ".tables" | grep sponsorship
   ```

3. **Verify environment variable**:
   ```bash
   python -c "import os; print(os.getenv('GITHUB_WEBHOOK_SECRET'))"
   ```

---

## Example: Full Test Flow

```bash
#!/bin/bash
set -e

echo "🚀 Starting Socrates GitHub Sponsors Webhook Test"
echo ""

# 1. Start ngrok
echo "1️⃣  Starting ngrok..."
ngrok http 8000 > /tmp/ngrok.log &
NGROK_PID=$!
sleep 2

# Extract ngrok URL
NGROK_URL=$(grep -oP 'https://[a-z0-9]+\.ngrok\.io' /tmp/ngrok.log | head -1)
echo "   ngrok URL: $NGROK_URL"

# 2. Get webhook secret
SECRET=$(grep GITHUB_WEBHOOK_SECRET deployment/configurations/.env.local | cut -d= -f2)
echo "2️⃣  Using webhook secret: ${SECRET:0:8}..."

# 3. Register webhook
echo "3️⃣  Registering webhook..."
python setup_github_sponsors_webhook.py --url $NGROK_URL --secret $SECRET

# 4. Send test webhook
echo "4️⃣  Sending test webhook..."
PAYLOAD='{"action":"created","sponsorship":{"sponsor":{"login":"testuser","id":12345},"tier":{"monthly_price_in_cents":2500}}}'
SIG="sha256=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)"

curl -s -X POST http://localhost:8000/sponsorships/webhooks/github-sponsors \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: $SIG" \
  -d "$PAYLOAD" | python -m json.tool

# 5. Check database
echo "5️⃣  Checking database..."
sqlite3 socrates.db "SELECT github_username, sponsorship_amount, socrates_tier_granted FROM sponsorships WHERE github_username = 'testuser';"

# Cleanup
kill $NGROK_PID
echo ""
echo "✅ Test complete!"
```

---

## Production Deployment

When deploying to production:

1. **Use production domain**:
   ```bash
   python setup_github_sponsors_webhook.py \
     --url https://api.yourdomain.com \
     --secret your-production-secret
   ```

2. **Generate new secret** for production:
   ```bash
   openssl rand -hex 32
   # Update in production .env file
   # Update in GitHub webhook settings
   ```

3. **Update webhook** in GitHub if URL changes:
   - List existing: `python setup_github_sponsors_webhook.py --list`
   - Delete old: `python setup_github_sponsors_webhook.py --delete <id>`
   - Create new with production URL

---

## Related Documentation

- [GitHub Sponsors Setup Guide](GITHUB_SPONSORS_SETUP.md)
- [Socrates Sponsorships API](socrates-api/src/socrates_api/routers/sponsorships.py)
- [ngrok Documentation](https://ngrok.com/docs)
- [GitHub Webhooks Docs](https://docs.github.com/en/developers/webhooks-and-events/webhooks)

---

## Support

- **Issues**: https://github.com/Nireus79/Socrates/issues
- **ngrok Issues**: https://github.com/inconshreveable/ngrok/issues
- **GitHub API Docs**: https://docs.github.com/en/rest
