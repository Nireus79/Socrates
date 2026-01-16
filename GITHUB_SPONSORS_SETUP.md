# GitHub Sponsors Integration for Socrates

Complete guide for integrating GitHub Sponsors with Socrates monetization system.

## Overview

**GitHub Sponsors Profile:** https://github.com/sponsors/Nireus79

When users sponsor you on GitHub, Socrates automatically upgrades their tier based on sponsorship amount:
- **$5/month** → Pro tier (10 projects, 5 team members, 100GB storage)
- **$15/month** → Enterprise tier (unlimited projects, members, storage)

## How It Works

### 1. User Sponsors You

User visits your GitHub Sponsors page and selects a sponsorship tier:
```
https://github.com/sponsors/Nireus79
```

### 2. GitHub Sends Webhook

When sponsorship is created/updated, GitHub sends a webhook event to your Socrates API:
```
POST /sponsorships/webhooks/github-sponsors
```

### 3. Webhook Handler Processes Event

The webhook handler:
1. Verifies GitHub's signature using `GITHUB_WEBHOOK_SECRET`
2. Extracts sponsorship amount ($5, $15, etc.)
3. Maps amount to Socrates tier (Pro, Enterprise)
4. Updates user's subscription tier in database
5. Sets subscription expiry date (1 year)
6. Returns success response

### 4. User Gets Tier Access

User automatically receives:
- Upgraded subscription tier
- All corresponding features unlocked
- Tier valid for 12 months from sponsorship date

---

## Setup Instructions

### Step 1: Configure Environment Variables

Add to your `.env.local` or deployment configuration:

```bash
# GitHub Webhook Secret - Generate a random string for security
GITHUB_WEBHOOK_SECRET=your-random-secret-here

# Example: Generate with openssl
openssl rand -hex 32
```

### Step 2: Register Webhook with GitHub

1. Go to your GitHub repository settings:
   ```
   https://github.com/Nireus79/Socrates/settings
   ```

2. Click "Webhooks" in the left sidebar

3. Click "Add webhook"

4. Configure webhook:
   - **Payload URL**: `https://your-socrates-api.com/sponsorships/webhooks/github-sponsors`
   - **Content type**: `application/json`
   - **Secret**: Paste your `GITHUB_WEBHOOK_SECRET` value
   - **Events**: Select `Sponsorship`
   - **Active**: ✓ Check this box

5. Click "Add webhook"

### Step 3: Test Webhook Delivery

GitHub provides webhook delivery history at:
```
https://github.com/Nireus79/Socrates/settings/hooks
```

You'll see recent webhook deliveries with:
- Status code (200 = success)
- Response body
- Timestamp

### Step 4: Create Test Sponsorship (Development)

For testing without real sponsorships:
1. Use GitHub's webhook testing tools
2. Manually POST to webhook endpoint:

```bash
curl -X POST http://localhost:8000/sponsorships/webhooks/github-sponsors \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$(echo -n '{"action":"created","sponsorship":{"sponsor":{"login":"testuser","id":123},"tier":{"monthly_price_in_cents":500}}}' | openssl dgst -sha256 -hmac 'your-secret' | cut -d' ' -f2 | sed 's/^/sha256=/')" \
  -d '{
    "action": "created",
    "sponsorship": {
      "sponsor": {"login": "testuser", "id": 123},
      "tier": {"monthly_price_in_cents": 500}
    }
  }'
```

---

## API Endpoints

### Webhook Endpoint

```
POST /sponsorships/webhooks/github-sponsors
```

**Headers:**
- `X-Hub-Signature-256`: GitHub signature (required)
- `Content-Type`: `application/json`

**Payload:**
```json
{
  "action": "created",
  "sponsorship": {
    "sponsor": {
      "login": "github_username",
      "id": 12345
    },
    "tier": {
      "monthly_price_in_cents": 500  // $5.00
    }
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "status": "success",
  "message": "Sponsorship processed: testuser upgraded to pro",
  "data": {
    "github_username": "testuser",
    "previous_tier": "free",
    "new_tier": "pro",
    "sponsorship_amount": "$5/month",
    "tier_expires": "2025-01-16T12:34:56"
  }
}
```

### Verify Sponsorship

Check if user has an active sponsorship:

```
GET /sponsorships/verify
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "status": "success",
  "message": "Active sponsorship verified",
  "data": {
    "username": "testuser",
    "github_username": "testuser",
    "sponsorship_amount": 5,
    "tier_granted": "pro",
    "sponsored_since": "2025-01-16T00:00:00",
    "expires_at": "2026-01-16T00:00:00",
    "days_remaining": 365
  }
}
```

### Sponsorship History

Get all sponsorships for a user:

```
GET /sponsorships/history
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "success": true,
  "status": "success",
  "message": "Sponsorship history retrieved",
  "data": {
    "username": "testuser",
    "sponsorships": [
      {
        "id": 1,
        "username": "testuser",
        "github_username": "testuser",
        "sponsorship_amount": 5,
        "socrates_tier_granted": "pro",
        "sponsorship_status": "active",
        "sponsored_at": "2025-01-16T00:00:00",
        "tier_expires_at": "2026-01-16T00:00:00"
      }
    ],
    "total_sponsored": 1
  }
}
```

---

## Database Schema

**Table: `sponsorships`**

```sql
CREATE TABLE sponsorships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,                    -- Socrates username
    github_username TEXT NOT NULL,             -- GitHub username
    github_sponsor_id INTEGER,                 -- GitHub user ID
    sponsorship_amount INTEGER NOT NULL,       -- Dollars per month
    socrates_tier_granted TEXT NOT NULL,       -- "pro" or "enterprise"
    sponsorship_status TEXT DEFAULT 'active',  -- "active", "cancelled"
    sponsored_at TIMESTAMP,                    -- When sponsorship started
    tier_expires_at TIMESTAMP,                 -- When tier expires
    last_payment_at TIMESTAMP,                 -- Last successful payment
    payment_id TEXT,                           -- GitHub transaction ID
    webhook_event_id TEXT,                     -- GitHub event ID
    notes TEXT,                                -- Admin notes

    FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
);
```

---

## Sponsorship Tier Mapping

| Sponsorship Amount | Socrates Tier | Projects | Team Members | Storage |
|--------------------|---------------|----------|--------------|---------|
| $5/month           | Pro           | 10       | 5            | 100GB   |
| $15/month          | Enterprise    | Unlimited | Unlimited   | Unlimited |
| Custom $5-$14      | Pro           | 10       | 5            | 100GB   |
| Custom $15+        | Enterprise    | Unlimited | Unlimited   | Unlimited |

---

## Webhook Security

### Signature Verification

GitHub sends `X-Hub-Signature-256` header with each webhook:

```
X-Hub-Signature-256: sha256=<hash>
```

**Verification Process:**

1. Get raw request body (bytes)
2. Get `GITHUB_WEBHOOK_SECRET` from environment
3. Calculate HMAC-SHA256 hash:
   ```
   hash = HMAC-SHA256(secret, body)
   expected = "sha256=" + hex(hash)
   ```
4. Compare with header value using constant-time comparison
5. Reject if signatures don't match

**Implementation:**

```python
from socratic_system.sponsorships.webhook import verify_github_signature

# In your webhook handler:
if not verify_github_signature(payload_bytes, signature_header):
    raise HTTPException(status_code=401, detail="Invalid signature")
```

---

## Frontend Integration

### Display Sponsor Badge

Add to user profile/dashboard:

```jsx
import { useQuery } from '@tanstack/react-query';

function SponsorBadge() {
  const { data: sponsorship } = useQuery({
    queryKey: ['sponsorship'],
    queryFn: () => api.get('/sponsorships/verify')
  });

  if (!sponsorship?.data?.days_remaining) {
    return null;
  }

  return (
    <div className="sponsor-badge">
      ⭐ Sponsor: {sponsorship.data.tier_granted}
      <small>Expires in {sponsorship.data.days_remaining} days</small>
    </div>
  );
}
```

### Sponsorship CTA

Add button to upgrade page:

```jsx
<button onClick={() => {
  window.open('https://github.com/sponsors/Nireus79', '_blank');
}}>
  Become a Sponsor on GitHub
</button>
```

---

## Troubleshooting

### Webhook Not Being Called

1. **Verify webhook is registered:**
   ```
   https://github.com/Nireus79/Socrates/settings/hooks
   ```

2. **Check webhook delivery history:**
   - Click webhook, scroll to "Recent Deliveries"
   - See response status and body
   - Look for error messages

3. **Verify webhook URL is correct:**
   - Webhook URL must be publicly accessible
   - Test with: `curl https://your-api.com/sponsorships/webhooks/github-sponsors`
   - Should return 405 Method Not Allowed (POST required)

4. **Check network connectivity:**
   - GitHub servers must reach your API
   - No firewall blocking
   - No redirects (GitHub doesn't follow them)

### Signature Verification Failing

1. **Verify GITHUB_WEBHOOK_SECRET is set:**
   ```bash
   echo $GITHUB_WEBHOOK_SECRET
   ```

2. **Check secret matches webhook configuration:**
   - Go to webhook settings
   - Verify "Secret" field matches your env variable

3. **Ensure secret is correct type:**
   - Must be plain text string
   - No quotes or extra whitespace

### User Not Upgraded

1. **Check database sponsorship record:**
   ```sql
   SELECT * FROM sponsorships WHERE github_username = 'username';
   ```

2. **Check user subscription tier:**
   ```sql
   SELECT username, subscription_tier FROM users WHERE username = 'username';
   ```

3. **Check if sponsorship is active and not expired:**
   ```sql
   SELECT * FROM sponsorships
   WHERE username = 'username'
   AND sponsorship_status = 'active'
   AND tier_expires_at > datetime('now');
   ```

4. **Check API logs:**
   ```bash
   tail -f /app/logs/socrates.log | grep sponsorship
   ```

---

## Manual User Upgrade (Admin)

If webhook fails but sponsorship is confirmed, manually upgrade user:

```sql
-- Update user tier
UPDATE users
SET subscription_tier = 'pro',
    subscription_status = 'active',
    subscription_start = datetime('now'),
    subscription_end = datetime('now', '+1 year')
WHERE username = 'github_username';

-- Record sponsorship
INSERT INTO sponsorships (
    username, github_username, sponsorship_amount,
    socrates_tier_granted, sponsorship_status, sponsored_at, tier_expires_at
) VALUES (
    'github_username', 'github_username', 5,
    'pro', 'active', datetime('now'), datetime('now', '+1 year')
);
```

---

## Monitoring

### Key Metrics to Track

1. **Webhook success rate:**
   ```sql
   SELECT sponsorship_status, COUNT(*)
   FROM sponsorships
   GROUP BY sponsorship_status;
   ```

2. **Active sponsors:**
   ```sql
   SELECT tier_granted, COUNT(*) as count
   FROM sponsorships
   WHERE sponsorship_status = 'active'
   AND tier_expires_at > datetime('now')
   GROUP BY tier_granted;
   ```

3. **Revenue potential:**
   ```sql
   SELECT
       SUM(CASE WHEN socrates_tier_granted = 'pro' THEN 5 ELSE 15 END) as monthly_mrr
   FROM sponsorships
   WHERE sponsorship_status = 'active'
   AND tier_expires_at > datetime('now');
   ```

---

## Support

- **GitHub Issues:** https://github.com/Nireus79/Socrates/issues
- **Documentation:** See `/docs` directory
- **GitHub Sponsors Help:** https://docs.github.com/en/sponsors

---

## Related Files

- Tier definitions: `socratic_system/sponsorships/tiers.py`
- Webhook handler: `socratic_system/sponsorships/webhook.py`
- API endpoint: `socrates-api/src/socrates_api/routers/sponsorships.py`
- Database schema: `socratic_system/database/schema_v2.sql`
- Environment config: `deployment/configurations/.env.example`
