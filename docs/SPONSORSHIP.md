# Support Socrates Development via GitHub Sponsors

Thank you for considering supporting the development of Socrates! Your sponsorship directly funds development, maintenance, and new features.

## How Sponsorship Works

### 1. **Sponsor on GitHub**

Visit the [Socrates GitHub Sponsors page](https://github.com/sponsors/Nireus79) to become a sponsor.

**Available Tiers:**

| Tier | Amount | Socrates Tier Granted | Benefits |
|------|--------|----------------------|----------|
| **Supporter** | $5/month | Pro | 10 projects, 5 team members, 100GB storage |
| **Contributor** | $15/month | Enterprise | Unlimited projects, unlimited team members, unlimited storage |
| **Custom** | $25+/month | Enterprise+ | All Enterprise features + priority support |

### 2. **Connect Your Sponsorship to Socrates**

Once you sponsor on GitHub:

1. **Create a Socrates Account** (if you don't have one)
   - Use the same username as your GitHub account for automatic linking
   - Or manually link your GitHub account in Socrates settings

2. **Wait for Webhook Processing** (usually instant)
   - Our system automatically detects your sponsorship
   - Your Socrates tier is upgraded within seconds
   - You receive a confirmation email

3. **Access Your New Features**
   - Your account is immediately upgraded
   - All new features are available
   - Create additional projects, add team members, get more storage

### 3. **Verify Your Sponsorship**

In Socrates, navigate to **Settings → Subscription** to:
- View your active sponsorship status
- See your tier and monthly sponsorship amount
- Check expiration date
- View payment history and methods
- Track tier changes and upgrades

## Sponsorship Benefits

### **Pro Tier ($5/month)**
- ✅ 10 projects
- ✅ 5 team members per project
- ✅ 100GB storage
- ✅ Basic collaboration features
- ✅ Community support

### **Enterprise Tier ($15/month)**
- ✅ Unlimited projects
- ✅ Unlimited team members
- ✅ Unlimited storage
- ✅ Advanced collaboration
- ✅ Priority support
- ✅ Sponsor badge on profile

### **Enterprise+ Tier ($25+/month)**
- ✅ Everything in Enterprise
- ✅ Priority email support
- ✅ Direct communication channel
- ✅ Feature requests considered
- ✅ Custom configuration options

## Frequently Asked Questions

### Q: How long does sponsorship activation take?
**A:** Usually instant (within seconds). If not activated within 5 minutes:
1. Check your Socrates account username matches your GitHub username
2. Verify your sponsorship is active on GitHub
3. Try logging out and back in to Socrates
4. Contact support if still not working

### Q: Can I change my sponsorship tier?
**A:** Yes! You can upgrade or downgrade your sponsorship on GitHub at any time.
- **Upgrades** are activated immediately
- **Downgrades** take effect at the start of your next billing cycle

### Q: What happens if I cancel my sponsorship?
**A:** Your tier will downgrade to Free at the next billing cycle. You'll have until then to export your projects and data.

### Q: Can I sponsor with a different GitHub account?
**A:** Yes! Create a Socrates account and link it to your GitHub account in **Settings → GitHub Integration**.

### Q: Is my payment secure?
**A:** Yes. All payments are processed by GitHub directly. We never see your payment information. See [GitHub Sponsors Security](https://docs.github.com/en/billing/managing-billing-for-github-sponsors/about-github-sponsors).

### Q: Can I get a refund?
**A:** GitHub Sponsors are billed monthly. You can cancel anytime, and you won't be charged for the next month. For specific refund questions, contact GitHub Support.

### Q: What payment methods are accepted?
**A:** GitHub Sponsors accepts all major payment methods supported by your GitHub account. See [Supported Payment Methods](https://docs.github.com/en/billing/managing-your-github-billing-settings/viewing-your-payment-methods).

## Sponsorship in Socrates

### Check Your Sponsorship Status

**Via API:**
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
    "payment_methods_on_file": 1
  }
}
```

### View Payment History

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/payments \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Tier Change History

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/tier-history \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Comprehensive Analytics

**Via API:**
```bash
curl -X GET http://localhost:8000/api/v1/sponsorships/analytics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Management & Support

### Manage Your Sponsorship

1. **Change Tier**: Visit [GitHub Sponsors page](https://github.com/sponsors/Nireus79) → Manage sponsorship
2. **Cancel Sponsorship**: Same page → Stop sponsoring
3. **Pause Sponsorship**: Temporarily pause without cancelling

### Need Help?

- **Sponsorship Issues**: Check [GitHub Sponsors Support](https://docs.github.com/en/billing/managing-billing-for-github-sponsors)
- **Socrates Issues**: Open an issue on [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- **Urgent Support**: Sponsored users can reach out directly

## Thank You! 💜

Your sponsorship directly enables:
- ✨ New features and improvements
- 🐛 Faster bug fixes
- 📚 Better documentation
- 🚀 Performance optimizations
- 🤝 Better community support

Every dollar supports open-source development and helps Socrates grow.

---

**Other Ways to Support:**
- ⭐ Star the repository on GitHub
- 🐛 Report bugs and request features
- 📝 Contribute code and documentation
- 🔗 Share Socrates with others
- 💬 Participate in discussions

Thank you for being part of the Socrates community! 🙏
