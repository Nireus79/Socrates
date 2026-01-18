# FAQ - Socrates AI

## Frequently Asked Questions

Got a question? We probably have the answer.

---

## Getting Started

### Q: What is Socrates AI?
**A**: Socrates AI is an intelligent development companion that uses the Socratic method (asking thoughtful questions) to help you clarify project requirements, then generates production-ready code from your specifications.

### Q: Do I need any programming experience?
**A**: Yes, some programming experience is helpful. Socrates generates code for developers. You should understand the basics of your chosen language.

### Q: Is Socrates AI free?
**A**: Yes! The free tier includes everything you need to start. Paid tiers unlock advanced features like team collaboration and more storage.

### Q: What programming languages are supported?
**A**: Python, JavaScript/TypeScript, Go, Rust, Java, C#, C++, and more. You choose the language during code generation.

### Q: How long does it take to generate code?
**A**:
- Dialogue phase: 30 minutes to 2 hours (depending on project complexity)
- Code generation: 10-30 seconds
- Total time to production code: 1-3 hours

### Q: Is the generated code production-ready?
**A**: Nearly! Generated code is high-quality and well-documented, but you should:
- Review the code
- Add tests
- Test with real data
- Deploy to staging first
- Then deploy to production

---

## Features & Capabilities

### Q: What's the Socratic method?
**A**: Instead of just telling you what to build, Socrates asks thoughtful questions to help you think deeply about:
- What problem you're solving
- Who your users are
- What the constraints are
- How the system should work

This ensures you've thought through all important aspects before writing code.

### Q: What does conflict detection do?
**A**: It automatically identifies contradictions in your specifications like:
- Requirements that conflict with each other
- Goals that conflict with constraints
- Tech stack incompatibilities
- Unrealistic time/budget combinations

It catches these during planning instead of during development.

### Q: Can Socrates handle complex projects?
**A**: Socrates works best for:
- New applications (10-1000 lines of code)
- Well-defined scope
- Standard architecture
- Public-facing services

Socrates is not ideal for:
- Complex embedded systems
- Real-time systems
- Scientific computing
- Machine learning pipelines (v1.4 coming)

### Q: Can I modify generated code?
**A**: Yes! The generated code is just a starting point. You can:
- Edit the code
- Add more features
- Integrate with other services
- Deploy as-is
- Use as reference

---

## Pricing & Plans

### Q: How much does it cost?
**A**:
- **Free**: $0 (+ your Claude API costs, ~$1-5 per project)
- **Basic**: $5/month (+ API costs)
- **Pro**: $15/month (+ API costs)
- **Enterprise**: Custom pricing

### Q: What are Claude API costs?
**A**: Socrates uses Claude API for code generation. You pay Anthropic directly:
- Typical project: $1-5 in API costs
- Dialogue: $0.01-0.05 per question
- Code generation: $0.50-2.00 per project
- Prices shown at https://www.anthropic.com/pricing

### Q: Can I upgrade/downgrade anytime?
**A**: Yes! No lock-in contracts. Upgrade or downgrade anytime. Changes take effect next billing cycle.

### Q: Is there a free trial for paid tiers?
**A**:
- Free tier is a full-featured trial
- Pro tier: 30-day money-back guarantee
- No credit card required for free tier

### Q: Do you offer student discounts?
**A**: Yes! 50% off Pro tier for students with .edu email. Contact [hello@socrates-ai.com](mailto:hello@socrates-ai.com)

### Q: What about open source projects?
**A**: Open source projects get free Pro tier access. [Contact us](mailto:hello@socrates-ai.com) with proof (GitHub stars, PyPI downloads, etc.)

---

## Account & Data

### Q: Where is my data stored?
**A**:
- **Free/Pro tiers**: AWS cloud (encrypted)
- **Enterprise**: Your choice (self-hosted or custom region)
- **Local-only**: Run on your machine (open source)

### Q: Is my data encrypted?
**A**: Yes! AES-256 encryption at rest, TLS 1.3 in transit. Optional: Encrypt locally with BitLocker/FileVault.

### Q: What if I delete my account?
**A**: All your data is deleted within 30 days. You can export everything before deleting.

### Q: Can I export my projects?
**A**: Yes! Export as JSON, CSV, or markdown. No vendor lock-in.

### Q: Can I use Socrates offline?
**A**: Almost! Code generation requires Claude API (internet), but processing happens locally. Coming v1.5: offline local models.

### Q: How do I change my password?
**A**: Account Settings → Security → Change Password. Simple process, takes 1 minute.

---

## Collaboration & Teams

### Q: Can multiple people use Socrates?
**A**:
- **Free/Basic**: 1 person
- **Pro**: Invite up to 5 team members
- **Enterprise**: Unlimited team members

### Q: How do I invite team members?
**A**: Pro tier: Settings → Team → Invite Members → Enter email addresses

### Q: Can team members see each other's projects?
**A**: Only projects shared explicitly. By default, projects are private.

### Q: Can we collaborate in real-time?
**A**: Yes! Pro tier has real-time collaboration:
- Multiple people answering questions
- Shared specifications
- Live updates

---

## Integration & API

### Q: Can I integrate with GitHub?
**A**:
- Coming v1.4: Native GitHub integration
- Today: Use REST API to sync projects
- You can: Auto-create repos, auto-commit code

### Q: Can I integrate with Jira?
**A**:
- Coming v1.4: Native Jira integration
- Today: Use REST API to create issues
- You can: Auto-create tickets from specs

### Q: Can I integrate with Slack?
**A**:
- Coming v1.4: Native Slack integration
- Today: Use webhooks to post updates
- You can: Notify your team

### Q: What's the API rate limit?
**A**:
- Free: 100 requests/day
- Basic: 1,000 requests/day
- Pro: 10,000 requests/day
- Enterprise: Custom limits

### Q: Can I use Socrates programmatically?
**A**: Yes! Full REST API available. See [API Documentation](api-docs-link)

---

## Code Generation

### Q: What quality is the generated code?
**A**: High quality:
- Follows best practices
- Includes error handling
- Has comments and docstrings
- Passes basic testing
- Production-ready

But always review before deploying.

### Q: Can I regenerate code?
**A**: Yes, as many times as you want. Each regeneration uses current specifications.

### Q: What if the code doesn't match my requirements?
**A**:
- Review the specification
- Update if needed
- Regenerate
- Rinse and repeat

### Q: Can it generate code for my specific business logic?
**A**: Socrates generates architectural code and scaffolding. You fill in business logic:
- Data models → [YES] Generated
- API structure → [YES] Generated
- Database schema → [YES] Generated
- Business logic → You add this

### Q: How do I integrate generated code into my project?
**A**:
- Download/copy code
- Place in your project
- Install dependencies
- Run tests
- Deploy

---

## Performance & System

### Q: How fast is code generation?
**A**:
- Questions: ~2-5 seconds each
- Code generation: 10-30 seconds
- Depends on: Spec size, model choice, internet speed

### Q: What are system requirements?
**A**:
- **RAM**: 4 GB minimum
- **Disk**: 500 MB free
- **Internet**: Required (for API calls)
- **Browser**: Any modern browser
- **OS**: Windows, macOS, Linux

### Q: Can I run Socrates on my server?
**A**:
- Free/Pro: Cloud-only
- Enterprise: Self-hosted available
- Open source: Self-host as desired

### Q: Does Socrates work offline?
**A**: Partial! Processing is local, but code generation needs Claude API (internet required).

---

## Support & Help

### Q: How do I get support?
**A**:
- **Free tier**: Community (Discord, GitHub)
- **Basic**: Email (48-hour response)
- **Pro**: Email (24-hour response)
- **Enterprise**: Dedicated support (2-hour response)

### Q: Where can I get help?
**A**:
- [Documentation](docs-link)
- [Discord Community](discord-link)
- [GitHub Issues](github-issues)
- [FAQ (this page)](faq-link)
- [Email Support](mailto:support@socrates-ai.com)

### Q: How do I report a bug?
**A**:
1. Check [GitHub Issues](github-issues) (might be known)
2. Provide: Reproduction steps, error message, logs
3. File new issue with details
4. We respond within 24 hours (usually faster)

### Q: How do I request a feature?
**A**:
1. Check [GitHub Discussions](discussions-link)
2. Post your idea
3. Get community feedback
4. We prioritize based on interest

### Q: Is there a Discord community?
**A**: Yes! Join 100+ developers: [Join Discord](discord-link)

---

## Security & Privacy

### Q: Is my API key safe?
**A**: Your key is never stored by us. Only transmitted to Claude API. Keep it secret like a password.

### Q: Can you train AI models on my code?
**A**: No! We explicitly don't train models on user data. This is a core promise.

### Q: Is my data shared with third parties?
**A**: No. We use AWS (infrastructure) and Stripe (payments), but no data is sold or shared.

### Q: Is Socrates GDPR compliant?
**A**: Yes! EU data residency available. Data deletion implemented. Full GDPR support.

### Q: What's your security track record?
**A**:
- No known breaches
- Regular security audits
- Vulnerability disclosure program
- SOC 2 certification (coming Q2 2026)

---

## Miscellaneous

### Q: What's the open source license?
**A**: MIT License. You can use, modify, and distribute freely. See [License](license-link)

### Q: Who built Socrates?
**A**: Built by Hermes Soft, a team of experienced developers and AI enthusiasts passionate about improving development productivity.

### Q: Can I contribute to Socrates?
**A**: Yes! We welcome:
- Code contributions
- Bug reports
- Feature requests
- Documentation improvements
- Translations

See [Contributing Guide](contributing-link)

### Q: What's the roadmap?
**A**:
- **v1.4** (Q1 2026): GitHub/Jira integration
- **v1.5** (Q2 2026): VS Code extension, offline models
- **v2.0** (Q3 2026): Multi-service architecture
- [Full Roadmap →](roadmap-link)

### Q: Is Socrates AI affiliated with the Socrates AI blog?
**A**: No, we're separate projects. Our name comes from the philosophical method, not another project.

### Q: Can I sponsor Socrates?
**A**: Yes! Support on [GitHub Sponsors](https://github.com/sponsors/Nireus79). Sponsors get access to premium features.

### Q: How do I stay updated?
**A**:
- Follow on GitHub
- Join Discord
- Subscribe to newsletter: [hello@socrates-ai.com](mailto:hello@socrates-ai.com)
- Check [Blog](blog-link)

---

## Still Have Questions?

### Documentation
[Browse Full Docs →](docs-link)

### Community
[Join Discord →](discord-link)

### Direct Support
[Email Us →](mailto:support@socrates-ai.com)

### Report Issue
[GitHub Issues →](github-issues)

---

**Last Updated**: January 2026
**Version**: 1.3.0

**Didn't find your answer? Ask us!**
[support@socrates-ai.com](mailto:support@socrates-ai.com) or [Discord](discord-link)
