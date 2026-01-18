# Security & Privacy - Socrates AI

## Header

**Your data. Your control. Your privacy.**

Socrates takes security seriously. All your project data remains yours, encrypted, and under your control.

---

## Data Storage & Privacy

### Where Your Data is Stored

**Free/Basic/Pro Tiers (Cloud)**
- Your projects stored on secure cloud servers
- Default: AWS in US East region
- Option: EU region (GDPR compliance)
- Automatic daily backups
- Encrypted at rest and in transit

**Enterprise Tier**
- Self-hosted: Your own servers
- Your control: Complete data residency
- No cloud storage required
- No data shared with us

**Local Use (Open Source)**
- All data stored on your machine
- No cloud sync by default
- No data leaves your computer
- Optional: Backup to your own cloud

### Local-First Architecture

Socrates is designed to work locally first:
- [YES] Run entirely on your machine
- [YES] No internet required except for Claude API
- [YES] All computation happens locally
- [YES] Optional: Sync to cloud for backup

---

## Encryption

### In Transit
**TLS 1.3 Encryption**
- All data encrypted while traveling to/from servers
- Certificate pinning enabled
- Perfect forward secrecy
- 256-bit encryption

**API Calls**
- Claude API requests encrypted with TLS 1.3
- Your API key never stored by us
- Requests signed and validated

### At Rest
**Server Storage (Cloud Tiers)**
- AES-256 encryption for all project data
- Encrypted database backups
- Encrypted key storage
- Hardware security modules for key management

**Local Storage**
- Encrypt using your system's tools:
  - Windows: BitLocker
  - macOS: FileVault
  - Linux: LUKS/dm-crypt

### Key Management
- [YES] Keys encrypted and segregated
- [YES] Regular key rotation
- [YES] Keys never logged or transmitted
- [YES] Separate encryption keys per user/project

---

## Your API Key - Complete Control

### Your Claude API Key

**Important**: Your API key is YOUR responsibility.

**What we do:**
- [YES] Never store your API key on our servers
- [YES] Never log your API key
- [YES] Never share your API key with anyone
- [YES] Never use your key for anything except your requests

**What you do:**
- [YES] Keep your API key private (like a password)
- [YES] Regenerate if you suspect compromise
- [YES] Use API key rotation for security
- [YES] Never commit API keys to version control

**How to protect your key:**
1. Store in environment variable, not code
2. Use `.env` files with `.gitignore`
3. Never commit to Git
4. Regenerate if you accidentally expose it
5. Monitor usage at https://console.anthropic.com

---

## Compliance & Certifications

### GDPR (General Data Protection Regulation)
[YES] **GDPR Compliant**
- Data residency in EU available
- Right to deletion implemented
- Data portability enabled
- Privacy by design

### CCPA (California Consumer Privacy Act)
[YES] **CCPA Compliant**
- Transparent data practices
- No third-party data sales
- User rights respected

### SOC 2 (Security & Availability)
🔄 **In Progress** (Target: Q2 2026)
- Security controls documented
- Availability guarantees
- Confidentiality measures

### ISO 27001 (Information Security)
🔄 **Planned** (Target: Q4 2026)
- Enterprise security standard
- Ongoing compliance

---

## Data Collection & Usage

### What Data We Collect

**Essential (Necessary for Operation):**
- [YES] Project specifications and code (yours to delete anytime)
- [YES] Account credentials (email, hashed password)
- [YES] API key (never stored, never logged)
- [YES] Usage metrics (projects created, code generated)

**Optional (For Improvement):**
- [YES] Error logs (debug issues, improve service)
- [YES] Usage analytics (understand feature usage)
- [YES] Feedback (when you provide it)

**Never Collected:**
- [NO] Browsing history
- [NO] System information
- [NO] Location data
- [NO] Contact information (unless you provide it)

### How We Use Your Data

**Your Project Data:**
- **Only for you**: Stored, indexed, searchable
- **Never trained on**: Not used to train models
- **Never shared**: Never shared with third parties
- **Never sold**: We don't sell data

**Usage Metrics:**
- **For improvement**: Understand what features help
- **For monitoring**: Detect and prevent abuse
- **For billing**: Track API costs for your tier
- **Anonymous**: Can't be tied back to you

**Error Logs:**
- **For debugging**: Fix bugs and improve reliability
- **Automatically deleted**: After 30 days
- **Never human-reviewed**: Unless you report a specific issue

---

## Third-Party Services

### Services We Use

**Claude API (Anthropic)**
- [YES] Encrypted transmission
- [YES] We don't control their data practices
- [YES] They follow their privacy policy
- [YES] You control your API key

**AWS (Cloud Infrastructure)**
- [YES] Enterprise security
- [YES] SOC 2 certified
- [YES] DDoS protection
- [YES] Automatic backups

**Payment Processing (Stripe)**
- [YES] PCI-DSS compliant
- [YES] We never see full credit card
- [YES] Encrypted transmission
- [YES] Encrypted storage

### Services We DON'T Use
- [NO] Google Analytics (we use privacy-first analytics)
- [NO] Third-party ads
- [NO] Data brokers
- [NO] Third-party AI training

---

## User Rights

### Your Rights

**Access:**
- [YES] Download all your data anytime
- [YES] View what we store about you
- [YES] Export in standard formats

**Deletion:**
- [YES] Delete individual projects
- [YES] Delete your entire account
- [YES] Automated data purge within 30 days
- [YES] No hidden backups retained

**Portability:**
- [YES] Export to JSON, CSV
- [YES] Compatible with other tools
- [YES] No vendor lock-in
- [YES] Open source alternative available

**Correction:**
- [YES] Update account information
- [YES] Correct project details
- [YES] Modify specifications

**Opt-Out:**
- [YES] Opt out of analytics
- [YES] Opt out of improvement emails
- [YES] Disable data collection (local-only mode)

### How to Exercise Your Rights

**Data Access:**
1. Log in to your account
2. Settings → Privacy & Data
3. Click "Download My Data"
4. Receive JSON export within 24 hours

**Account Deletion:**
1. Log in to your account
2. Settings → Danger Zone
3. Click "Delete My Account"
4. Confirm deletion
5. All data deleted within 30 days

**Contact Privacy Team:**
[privacy@socrates-ai.com](mailto:privacy@socrates-ai.com)
Response time: 24 hours

---

## Security Practices

### Infrastructure Security

**Network Security:**
- [YES] DDoS protection (Cloudflare)
- [YES] Web application firewall (WAF)
- [YES] Intrusion detection (IDS)
- [YES] Intrusion prevention (IPS)

**Server Security:**
- [YES] Auto-patching
- [YES] Vulnerability scanning
- [YES] Intrusion detection
- [YES] Log aggregation and monitoring

**Database Security:**
- [YES] Encrypted backups
- [YES] Access controls
- [YES] SQL injection prevention
- [YES] Read replicas for redundancy

### Application Security

**Code Security:**
- [YES] Input validation
- [YES] Output encoding
- [YES] CSRF protection
- [YES] XSS prevention
- [YES] SQL injection prevention

**Authentication:**
- [YES] Secure password hashing (bcrypt)
- [YES] Session management
- [YES] Account lockout after failed attempts
- [YES] Two-factor authentication (Enterprise)

**Authorization:**
- [YES] Role-based access control
- [YES] Project-level permissions
- [YES] Team-level permissions
- [YES] API key scoping

### Monitoring & Incident Response

**Real-Time Monitoring:**
- [YES] 24/7 security monitoring
- [YES] Automated alerts
- [YES] Log aggregation
- [YES] Anomaly detection

**Incident Response:**
- [YES] Incident response team on-call
- [YES] Documented response procedures
- [YES] Public disclosure policy
- [YES] Affected users notified within 24 hours

---

## Vulnerability Disclosure

### Found a Security Issue?

**We appreciate responsible disclosure!**

**Please DO:**
- [YES] Email [security@socrates-ai.com](mailto:security@socrates-ai.com)
- [YES] Include detailed description
- [YES] Give us 90 days to fix before public disclosure
- [YES] Use PGP encryption if needed

**Please DON'T:**
- [NO] Public disclosure before fix
- [NO] Test on production without permission
- [NO] Access other users' data
- [NO] Test on network infrastructure

**Our Commitment:**
- [YES] Acknowledge receipt within 24 hours
- [YES] Keep you updated on progress
- [YES] Credit you in security advisory (if desired)
- [YES] Prioritize fixes based on severity

---

## Privacy Policy Summary

### Quick Version (Full policy below)

**What we collect:**
- Your account and project data
- Usage metrics (anonymized)
- Error logs (auto-deleted)

**What we don't do:**
- Sell your data
- Share with third parties
- Train AI on your data
- Use cookies for tracking

**Your rights:**
- Access your data
- Delete your account
- Export everything
- Control analytics

**Contact us:**
[privacy@socrates-ai.com](mailto:privacy@socrates-ai.com)

---

## FAQ - Security & Privacy

### Q: Is my data encrypted?
**A:** Yes! At rest (AES-256) and in transit (TLS 1.3). You can also encrypt locally using your OS.

### Q: Can you access my projects?
**A:** No. We can only access for debugging if you explicitly grant permission. You remain in control.

### Q: What if Socrates gets hacked?
**A:** We maintain encrypted backups and have incident response procedures. We'll notify you within 24 hours if your data is affected.

### Q: Is my API key safe with you?
**A:** We never store your API key. It's only used locally on your machine or transmitted to Claude API with encryption.

### Q: Can Socrates train AI models on my code?
**A:** No. We explicitly don't train models on user data. This is a core principle.

### Q: Will Socrates share data with third parties?
**A:** No. We only use third-party services (AWS, Stripe) that sign data protection agreements.

### Q: Can I use Socrates completely offline?
**A:** Almost! Generating code requires Claude API calls, but all processing happens locally. You can run entirely offline with a local model (coming in v1.5).

### Q: How long do you keep my data?
**A:** As long as your account is active. Delete your account and data is purged within 30 days.

### Q: Is there a privacy-first plan?
**A:** Yes! Install locally (open source) and run entirely on your machine. No cloud at all.

### Q: What about GDPR/CCPA?
**A:** We're fully compliant. EU data residency available. Right to deletion implemented.

### Q: Can I get a Data Processing Agreement?
**A:** Yes! Enterprise customers can request a DPA. [Contact sales](mailto:sales@socrates-ai.com)

---

## Contact & More Info

### Privacy Questions
**Email**: [privacy@socrates-ai.com](mailto:privacy@socrates-ai.com)
**Response Time**: 24 hours

### Security Issues
**Email**: [security@socrates-ai.com](mailto:security@socrates-ai.com)
**Response Time**: 2 hours

### Legal Requests
**Email**: [legal@socrates-ai.com](mailto:legal@socrates-ai.com)

### Full Documentation
- [Privacy Policy](full-policy-link)
- [Terms of Service](tos-link)
- [Data Processing Agreement](dpa-link)
- [Security Whitepaper](whitepaper-link)

---

**Last Updated**: January 2026
**Version**: 1.3.0

**We're committed to your privacy and security. Questions? We're here to help!**
