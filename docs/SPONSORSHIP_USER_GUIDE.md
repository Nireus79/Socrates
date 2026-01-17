# Sponsorship User Guide - Quick Reference

Quick guide for Socrates users to understand sponsorship and access premium features.

## TL;DR - Get Started in 3 Steps

1. **Sponsor on GitHub**: Visit [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)
2. **Your account upgrades automatically** within seconds
3. **Enjoy premium features** immediately - no additional setup needed!

---

## Sponsorship Tiers

```
💰 GitHub Sponsors                      Socrates Tier          Features
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Free                                    Free                   1 project, 1 member, 5GB
$5/month (Supporter)                    Pro                    10 projects, 5 members, 100GB
$15/month (Contributor)                 Enterprise             Unlimited projects, members, storage
$25+/month (Custom)                     Enterprise+            All Enterprise + priority support
```

---

## In Socrates UI

### Check Your Sponsorship Status

1. Click **Settings** (⚙️ icon, top-right)
2. Click **Subscription** tab
3. View:
   - Current tier
   - Sponsorship status
   - When it expires
   - Your usage/quotas

### View Payment History

1. **Settings** → **Subscription**
2. Click **Payment History** button
3. See all past payments and amounts

### View Tier Changes

1. **Settings** → **Subscription**
2. Click **Tier Change History** button
3. See timeline of upgrades/downgrades

### Check Storage Usage

1. **Settings** → **Subscription**
2. Look at **Storage** section
3. See:
   - Total allocation
   - Current usage
   - Remaining space

---

## API Endpoints

### Check Sponsorship Status

```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "username": "yourname",
    "github_username": "yourname",
    "sponsorship_amount": 5,
    "tier_granted": "Pro",
    "sponsored_since": "2024-01-15T10:30:00",
    "expires_at": "2025-01-15T10:30:00",
    "days_remaining": 365,
    "payment_methods_on_file": 1,
    "payment_methods": [...]
  }
}
```

### Get Payment History

```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/payments \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Tier Change History

```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/tier-history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Sponsorship Analytics

```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/analytics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Sponsorship Info (Public)

```bash
# No authentication required!
curl -X GET http://localhost:8000/api/v1/sponsorships/info
```

**Returns:**
- Tier information
- Features per tier
- How sponsorship works
- FAQ

---

## Common Tasks

### Upgrade My Tier

**Steps:**
1. Visit [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)
2. Click on a higher tier ($5 → $15, or $15 → $25+)
3. Complete payment on GitHub
4. Your Socrates tier upgrades automatically (within seconds)
5. Refresh your Socrates browser tab to see changes

### Downgrade My Tier

**Steps:**
1. Visit [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)
2. Click "Manage sponsorship"
3. Select lower tier or "Cancel sponsorship"
4. Confirm
5. Downgrade takes effect at next billing cycle (30 days notice)

### Cancel Sponsorship

**Steps:**
1. Visit [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)
2. Click "Manage sponsorship"
3. Click "Stop sponsoring"
4. Your tier downgrades at end of billing cycle
5. Export important data before downgrade!

### Link GitHub Account

If using different username in Socrates:

1. **Settings** → **GitHub Integration**
2. Click "Link GitHub Account"
3. Authorize GitHub connection
4. Your Socrates account is now linked
5. Sponsorships are now tracked!

### View All Payment Methods

1. **Settings** → **Subscription**
2. Click **Payment Methods**
3. See all cards and payment methods on file
4. (To change, update in GitHub account settings)

---

## Quotas Explained

### Projects

| Tier | Limit |
|------|-------|
| Free | 1 project you own |
| Pro | 10 projects you own |
| Enterprise | Unlimited |

**Note:** Projects you collaborate on don't count toward your limit!

### Team Members

| Tier | Limit per project |
|------|-------------------|
| Free | 1 (just you) |
| Pro | 5 (you + 4 others) |
| Enterprise | Unlimited |

### Storage

| Tier | Limit |
|------|-------|
| Free | 5 GB |
| Pro | 100 GB |
| Enterprise | Unlimited |

---

## Troubleshooting

### Sponsorship Not Activating?

**Checklist:**
- ✅ Did you sponsor on GitHub? (Not just view the page)
- ✅ Is your GitHub username same as Socrates username?
- ✅ Has it been more than 5 minutes?
- ✅ Try logging out and back in

**If still not working:**
1. Check sponsorship status: GET `/sponsorships/verify`
2. Verify on GitHub Sponsors page that sponsorship shows as "active"
3. Open an issue on [GitHub Issues](https://github.com/Nireus79/Socrates/issues)

### Can't Create More Projects?

**You've hit your limit!**

1. Check how many projects you have: **Settings** → **Subscription**
2. **Delete** a project you don't need (you own)
3. Or **upgrade your tier** for more capacity

**Note:** Collaborating on others' projects doesn't count!

### Running Out of Storage?

**Solution:**
1. **Settings** → **Subscription** → **Storage**
2. See which projects use most space
3. Delete large files or export the project
4. Or **upgrade to Pro/Enterprise** for more space

### Payment Issue?

**Contact GitHub Support:**
- GitHub Sponsors payments are handled entirely by GitHub
- We don't process or see your payment info
- Visit [GitHub Sponsors Help](https://docs.github.com/en/billing/managing-billing-for-github-sponsors)

---

## Features Across Tiers

### All Tiers Include:

✅ Code generation
✅ Code analysis
✅ GitHub integration
✅ Real-time collaboration
✅ Knowledge management
✅ Socratic guidance
✅ Team collaboration
✅ Analytics & reports
✅ Chat sessions
✅ Export functionality

**The only difference is quotas (how much you can do), not what you can do!**

---

## Questions?

**More detailed info:**
- [SPONSORSHIP.md](../SPONSORSHIP.md) - Complete sponsorship guide
- [TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md) - Detailed tier info
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute

**Need help?**
- [GitHub Issues](https://github.com/Nireus79/Socrates/issues) - Report problems
- [GitHub Discussions](https://github.com/Nireus79/Socrates/discussions) - Ask questions
- [GitHub Sponsors](https://github.com/sponsors/Nireus79) - Sponsorship options

---

## Key Takeaways

1. **All features available in all tiers** - differentiation is by quota only
2. **Sponsorship is automatic** - GitHub Sponsors payment → Socrates upgrade (no extra steps)
3. **Payment is secure** - GitHub handles everything, Socrates never sees payment info
4. **Easy management** - check status, view history, manage subscription all in Settings
5. **Community focused** - free tier is fully functional, premium is optional but appreciated

**Thank you for supporting open-source! 💜**
