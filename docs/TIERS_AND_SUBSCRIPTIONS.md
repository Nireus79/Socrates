# Socrates Subscription Tiers & Feature Access

Complete guide to understanding Socrates subscription tiers, feature access, and storage quotas.

## Tier Overview

Socrates uses a **freemium model** where features are unified across all tiers, but access is controlled by **quotas** (limits on usage).

### Available Tiers

| Aspect | Free | Pro | Enterprise |
|--------|------|-----|------------|
| **Monthly Cost** | $0 | $5 | $15+ |
| **Project Limit** | 1 | 10 | Unlimited |
| **Team Members** | 1 | 5 | Unlimited |
| **Storage** | 5 GB | 100 GB | Unlimited |
| **All Features** | ✅ | ✅ | ✅ |
| **Support** | Community | Community | Priority |

### Important: Features vs. Quotas

**All tiers have access to ALL features:**
- Code generation
- Code analysis
- GitHub integration
- Real-time collaboration
- Knowledge management
- Chat and Socratic guidance
- Team collaboration
- Analytics and reporting

**Quotas (limits) differ by tier:**
- Number of projects you can create
- Number of team members you can add
- Amount of storage space available

**Example:**
- A Free tier user CAN use code generation
- But they can only create 1 project
- Pro tier user has 10 projects and can use the same code generation
- Enterprise tier user has unlimited projects

---

## Feature Access

### Unified Feature Set

All features are available in all tiers because **Socrates believes every user should have access to powerful tools**, regardless of budget.

**Available in All Tiers:**
- ✅ Code generation and analysis
- ✅ Socratic methodology guidance
- ✅ GitHub integration (import, sync)
- ✅ Real-time collaboration
- ✅ Knowledge base creation
- ✅ Chat sessions
- ✅ Multi-agent orchestration
- ✅ Export and analytics
- ✅ Team collaboration
- ✅ Progress tracking

---

## Quota System

### Project Limits

| Tier | Owned Projects | Collaborative Projects | Action |
|------|----------------|------------------------|--------|
| Free | 1 | Unlimited | Can't create more; must delete to create new |
| Pro | 10 | Unlimited | Plenty of capacity for projects |
| Enterprise | Unlimited | Unlimited | No limits; maximum flexibility |

**How it Works:**
- Your "owned projects" count against your limit
- Projects you're invited to collaborate on don't count
- You can see and work in unlimited collaborative projects
- When hitting limit, you must delete a project before creating new one

### Team Member Limits

| Tier | Members Per Project | Action |
|------|---------------------|--------|
| Free | 1 | Just you; can't add team members |
| Pro | 5 | Add up to 4 collaborators per project |
| Enterprise | Unlimited | Add as many as needed |

**How it Works:**
- You always count as 1 member
- Limit applies per project
- Can't invite more than tier allows
- Different projects can have different members

### Storage Quotas

| Tier | Total Allocation | Per File Limit | Type |
|------|-----------------|----------------|------|
| Free | 5 GB | 100 MB | Documents, code, knowledge |
| Pro | 100 GB | 500 MB | Same as Free |
| Enterprise | Unlimited | No limit | No storage restrictions |

**Storage Counts Toward Quota:**
- Project files and documents
- Knowledge base entries
- Uploaded resources
- Chat history (if stored)
- Exported files

**What Doesn't Count:**
- Database metadata
- Temporary processing data
- API cache

---

## How to Check Your Tier

### In Socrates UI
1. Click **Settings** (gear icon)
2. Navigate to **Subscription** tab
3. View:
   - Current tier
   - Quotas and usage
   - Billing information
   - Team member count

### Via API

**Check current subscription status:**
```bash
curl -X GET http://localhost:8000/api/v1/subscription/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response example:**
```json
{
  "tier": "Pro",
  "subscription_status": "active",
  "subscription_start": "2024-01-15T10:30:00",
  "subscription_end": "2025-01-15T10:30:00",
  "quotas": {
    "projects": {"limit": 10, "used": 3, "remaining": 7},
    "team_members": {"limit": 5, "used": 2, "remaining": 3},
    "storage_gb": {"limit": 100, "used": 15.2, "remaining": 84.8}
  }
}
```

---

## Upgrading Your Tier

### From Free → Pro

**Option 1: GitHub Sponsors (Recommended)**
1. Visit [GitHub Sponsors - Nireus79](https://github.com/sponsors/Nireus79)
2. Select $5/month "Supporter" tier
3. Your Socrates account upgrades automatically (within seconds)

**Option 2: Manual Link**
1. Create Socrates account with your GitHub username
2. Or link your GitHub account in Settings
3. Start sponsoring on GitHub
4. Wait for webhook processing (usually instant)

### From Free/Pro → Enterprise

**Option 1: GitHub Sponsors (Recommended)**
1. Visit [GitHub Sponsors - Nireus79](https://github.com/sponsors/Nireus79)
2. Select $15/month "Contributor" tier
3. Your Socrates account upgrades automatically

**Option 2: Custom Amount**
1. Visit [GitHub Sponsors page](https://github.com/sponsors/Nireus79)
2. Set custom amount ($25+/month)
3. Your account upgrades to "Enterprise+"

---

## Downgrading Your Tier

### How Downgrade Works
1. **Cancel sponsorship** on GitHub Sponsors page
2. **Effective date**: Next billing cycle (usually in 30 days)
3. **Notification**: You'll receive notification before downgrade
4. **Action required**: Export/delete excess projects before downgrade completes

### What Happens After Downgrade

**Before Effective Date:**
- You still have current tier access
- You can delete projects or export data
- You have 30 days to adjust

**On Effective Date:**
- Tier downgrades automatically
- Exceeding quotas are enforced:
  - Can't access projects over limit
  - Can't add team members over limit
  - Can't upload over storage limit

**Prevention:**
- Export important projects
- Delete projects you no longer need
- Reduce team members
- Manage storage before downgrade

---

## Storage Management

### Checking Storage Usage

**In UI:**
1. Settings → Subscription
2. View "Storage" quota
3. See breakdown by project

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/subscription/storage \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Reducing Storage Usage

1. **Delete old projects** (permanently removes storage)
2. **Remove large files** from projects
3. **Clear chat history** if applicable
4. **Archive projects** instead of deletion (if available)
5. **Compress files** before uploading

### Storage Limit Behavior

**When approaching limit:**
- Upload blocked
- Warnings displayed
- Cleanup suggestions provided

**When at limit:**
- No new uploads allowed
- Existing features still work
- Must delete/export data to upload again

---

## Testing Mode

### What is Testing Mode?

A development feature that bypasses all subscription restrictions for **testing and development purposes**.

**When active:**
- All quotas are ignored
- Create unlimited projects
- Add unlimited team members
- Use unlimited storage
- All features enabled regardless of tier

**When inactive:**
- Normal subscription limits apply
- Your paid tier is respected

### Enabling Testing Mode

**Via Socrates Settings:**
1. Settings → Developer/Testing
2. Toggle "Testing Mode"
3. Confirm activation

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/subscription/testing-mode \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Important Notes

- **Local development only** - not for production use
- **Visible to user only** - no special privileges
- **Persists to database** - survives restarts
- **Intended for testing** - development/QA purposes

---

## Billing & Payment

### Payment Information

**Processor:** GitHub Sponsors
- Secure payment processing
- Automatic monthly billing
- Tax handling included
- No payment info stored in Socrates

### Viewing Payment History

**In Socrates:**
1. Settings → Subscription
2. Click "Payment History"
3. View all past payments

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/payments \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Invoice & Receipts

- Invoices sent to your GitHub email
- Accessible in GitHub Sponsors dashboard
- Tax deductible (varies by location)

---

## Tier Change History

### Tracking Your Tier Changes

**View in Socrates:**
1. Settings → Subscription
2. Click "Tier Change History"
3. See timeline of all changes

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/tier-history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Information included:**
- Change type (upgrade/downgrade/renewal)
- Previous and new tiers
- Amount change
- Effective date
- Reason for change

---

## Troubleshooting

### Sponsorship Not Activating

1. **Check GitHub username** matches Socrates username
2. **Verify sponsorship active** on GitHub Sponsors page
3. **Wait a few minutes** for webhook processing
4. **Log out and back in** to refresh session
5. **Check API status** via `/api/v1/sponsorships/verify`

### Can't Create Projects

1. **Check quota**: Settings → Subscription
2. **Delete old projects** if at limit
3. **Verify tier**: Should show Pro or Enterprise
4. **Check testing mode**: May interfere with checks

### Storage Issues

1. **Check usage**: Settings → Subscription → Storage
2. **Delete unused files** from projects
3. **Archive old projects** if available
4. **Export data** before deleting projects

### Payment Issues

1. **Check GitHub Sponsors** - payment method valid?
2. **Verify billing address** in GitHub
3. **Check spam email** for invoices
4. **Contact GitHub Support** for payment issues

---

## FAQ

### Q: Why do all tiers have all features?

**A:** Socrates believes powerful AI tools should be accessible to everyone. Features are unified; quotas provide the differentiation and sustainability model.

### Q: Can I upgrade mid-month?

**A:** Yes! Upgrade immediately on GitHub Sponsors. Your Socrates account upgrades instantly. Billing adjusts automatically.

### Q: What if I hit my project limit?

**A:** You must delete a project before creating a new one. Or upgrade your tier for more capacity.

### Q: Does collaboration count against my quota?

**A:** No! Projects you're invited to collaborate on don't count toward your project limit. Only projects you own count.

### Q: Can I recover deleted projects?

**A:** Not automatically. Export important projects before deletion. Deleted projects are permanently removed from storage.

### Q: What's the difference between Free and Pro?

**A:** Free: 1 project, 1 team member, 5GB storage
Pro: 10 projects, 5 team members, 100GB storage
(Same features, different quotas)

### Q: Is there an annual billing option?

**A:** GitHub Sponsors handles billing. You can check sponsorship settings for available options.

---

## Need Help?

- **Sponsorship Questions:** See [SPONSORSHIP.md](../SPONSORSHIP.md)
- **API Docs:** `/api/v1/docs` in running Socrates instance
- **GitHub Issues:** [Report issues](https://github.com/Nireus79/Socrates/issues)
- **Discussions:** [Community discussions](https://github.com/Nireus79/Socrates/discussions)

---

**Last Updated:** January 2024
