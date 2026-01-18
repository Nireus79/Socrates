# FAQ by Scenario

Frequently asked questions organized by what you're trying to do.

---

## Getting Started

### Q: How do I install Socrates on Windows?
**A**: See [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) for complete step-by-step instructions. Download the .exe file and run it—automatic installation.

### Q: What are the system requirements?
**A**:
- Python 3.8+ (or download Windows .exe)
- 4 GB RAM
- 500 MB free disk space
- Internet connection (for Claude API)

### Q: How do I get an API key?
**A**:
1. Go to https://console.anthropic.com
2. Sign up or login
3. Navigate to "API Keys"
4. Click "Create new key"
5. Copy and set environment variable: `export ANTHROPIC_API_KEY="sk-ant-..."`

### Q: Do I need a GitHub account?
**A**: No, GitHub is optional. Socrates works standalone. GitHub account is only needed if sponsoring.

### Q: Can I use Socrates offline?
**A**: No, Socrates requires internet connection to call Claude API for dialogue and code generation.

---

## Creating & Managing Projects

### Q: How do I create my first project?
**A**: See [USER_GUIDE.md](USER_GUIDE.md#creating-your-first-project). Quick version:
```bash
/project create "My Project"
/continue  # Start answering questions
```

### Q: How many projects can I create?
**A**:
- Free tier: 5 projects
- Sponsored tier: 20+ projects
- Check with: `/subscription status`

### Q: Can I rename a project?
**A**: Not directly, but you can:
1. Export the project: `/project export "Old Name"`
2. Delete the old one: `/project delete "Old Name"`
3. Create new one: `/project create "New Name"`
4. Import: `/project import Old_Name_export.json`

### Q: How do I share a project with my team?
**A**:
- v1.3.0: Export and share JSON file
- v1.4.0: Team collaboration features coming
- Workaround: Use shared data directory

### Q: Can I import a project from file?
**A**: Yes: `/project import <filename>.json`

### Q: What happens if I delete a project?
**A**: **Permanent deletion** - no undo! Always backup first:
```bash
/project export <name>  # Backup first!
/project delete <name>
```

---

## Dialogue & Questioning

### Q: What is the Socratic method?
**A**: Asking questions to help you think deeply about your project. Instead of giving answers, Socrates asks clarifying questions to ensure you've thought through all aspects.

### Q: How many questions will I answer?
**A**: Depends on your project complexity. Typically 10-30 questions across all phases.

### Q: Can I skip phases?
**A**: No, you must complete discovery → analysis → design → implementation in order. Each builds on the previous.

### Q: What if I don't know the answer to a question?
**A**:
- Say "I don't know" or "Not sure yet"
- Ask for hint: `/hint`
- Move on to next question: `/continue`
- Come back later

### Q: Can I change my answers?
**A**: Yes:
1. Go back: `/back`
2. Re-answer question
3. Continue from there

### Q: What does maturity score mean?
**A**: % of how ready your project is to advance to the next phase:
- 0-25%: Incomplete (missing critical info)
- 25-50%: Partial (some info covered)
- 50-75%: Developing (most info there)
- 75-90%: Ready (nearly ready for next phase)
- 90-100%: Complete (all areas covered)

### Q: Why can't I advance to the next phase?
**A**: Your project hasn't reached enough maturity. Complete more questions or provide more details. Use `/hint` to see what's missing.

---

## Code Generation

### Q: When can I generate code?
**A**: After completing the implementation phase (when maturity is 90%+).

### Q: What programming languages does Socrates support?
**A**: All languages! You specify during dialogue or set in config:
```python
config = ConfigBuilder("sk-ant-...") \
    .with_model("claude-opus-4-5-20251101")  # More capable
    .build()
```

### Q: Is the generated code production-ready?
**A**: Near-production quality, but always review:
1. Test thoroughly
2. Add error handling
3. Implement proper logging
4. Add unit tests
5. Code review before deployment

### Q: Can I regenerate code?
**A**: Yes: `/code generate` multiple times. Each regeneration uses latest project context.

### Q: How can I fix generated code?
**A**:
1. Edit it directly
2. Or describe issue and regenerate
3. Or provide code review feedback

### Q: What if generated code is in wrong language?
**A**: Specify in dialogue or in config. See [CONFIGURATION.md](CONFIGURATION.md).

---

## Performance & Troubleshooting

### Q: Why is Socrates slow?
**A**:
- Claude API takes 2-5 seconds per response
- Large projects take longer
- Your internet speed matters
- Solutions: Use faster model (Haiku), smaller projects, or wait

### Q: How much does this cost?
**A**: Depends on Claude API pricing:
- Haiku model: ~$0.01-0.05 per request
- Typical project: $1-5 total
- See token usage: `/status`

### Q: "Port already in use" error - what do I do?
**A**:
1. Kill other Socrates instances: `pkill -f socrates`
2. Or use different port: `python socrates.py --api --port 9000`

### Q: Browser won't connect
**A**:
1. Wait 15 seconds (app needs time to start)
2. Manually go to http://localhost:5173
3. If still fails, check logs: `tail ~/.socrates/logs/socratic.log`

### Q: "Database locked" error
**A**: Another Socrates instance is running:
```bash
pkill -f socrates  # Kill all instances
sleep 2
python socrates.py  # Restart
```

### Q: How do I enable debug mode?
**A**: `/debug on` (shows detailed logs)

### Q: Where are logs stored?
**A**: `~/.socrates/logs/socratic.log`

---

## Data & Storage

### Q: How much storage do I need?
**A**:
- Minimum: 500 MB free space
- Typical: 100-500 MB for 5-20 projects
- Check usage: `du -sh ~/.socrates`

### Q: Where is my data stored?
**A**: By default: `~/.socrates/` (Linux/macOS) or `%USERPROFILE%\.socrates` (Windows)

### Q: Can I change storage location?
**A**: Yes: `export SOCRATES_DATA_DIR="/custom/path"`

### Q: How do I backup my projects?
**A**: Three methods:
```bash
# 1. Export projects
/project export <name>

# 2. Backup entire directory
zip -r ~/backup.zip ~/.socrates

# 3. Via Git
git add *_export.json && git commit -m "Backup"
```

### Q: Can I restore from backup?
**A**: Yes: `/project import <name>_export.json`

### Q: What if I'm out of storage quota?
**A**:
1. Archive old projects: `/project archive <name>`
2. Delete unnecessary projects: `/project delete <name>`
3. Sponsor/upgrade tier

### Q: Are my projects encrypted?
**A**: Data is at rest on your disk (not encrypted by default). Use system-level encryption (BitLocker, FileVault, etc.) for security.

---

## API & Integration

### Q: Can I use Socrates programmatically?
**A**: Yes! See [API_REFERENCE.md](API_REFERENCE.md) for complete documentation.

### Q: How do I authenticate API calls?
**A**: Bearer token in Authorization header:
```python
headers = {"Authorization": f"Bearer {token}"}
```

### Q: Can I listen to events?
**A**: Yes! See [INTEGRATIONS.md](INTEGRATIONS.md) for webhook setup.

### Q: Can I integrate with Slack/Jira/GitHub?
**A**: Via custom integration. See [INTEGRATIONS.md](INTEGRATIONS.md) for examples. Built-in integrations coming v1.4+.

---

## Sponsorship & Tiers

### Q: What does sponsoring do?
**A**: Unlocks premium features:
- More storage
- More projects
- Priority support
- Early access to features

### Q: How do I sponsor?
**A**: https://github.com/sponsors/Nireus79

### Q: How much does sponsorship cost?
**A**: Multiple tiers from $5-50/month. See [SPONSORSHIP.md](../SPONSORSHIP.md).

### Q: When do I get sponsor benefits?
**A**: Usually instant (5 seconds). If delayed, try `/subscription refresh`.

### Q: Can I cancel anytime?
**A**: Yes, cancel on GitHub Sponsors anytime.

### Q: Do I get a refund?
**A**: See [SPONSORSHIP.md](../SPONSORSHIP.md) refund policy.

---

## Windows-Specific

### Q: Where is the .exe file?
**A**:
- After installation: `C:\Program Files\Socrates\socrates.exe`
- Or download from releases page

### Q: How do I run from command line?
**A**:
```cmd
"C:\Program Files\Socrates\socrates.exe" --full
```

### Q: Can I set it to run on startup?
**A**: Yes, Windows Scheduled Task:
1. Task Scheduler → Create Basic Task
2. Trigger: At startup
3. Action: Run `C:\Program Files\Socrates\socrates.exe --full`

### Q: How do I uninstall on Windows?
**A**: See [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md#uninstalling)

---

## Advanced Usage

### Q: Can I use a different Claude model?
**A**: Yes:
```python
config = ConfigBuilder("sk-ant-...") \
    .with_model("claude-opus-4-5-20251101")  # More capable
    .build()
```

### Q: How do I add custom knowledge?
**A**:
```bash
/document import /path/to/doc.pdf
# Or
/knowledge add "My custom knowledge"
```

### Q: Can I have multiple instances?
**A**: Yes, use different data directories:
```python
config1 = ConfigBuilder("sk-ant-...") \
    .with_data_dir("/data/project1") \
    .build()
```

### Q: Can I run in headless mode?
**A**: Yes: `python socrates.py --api` (API only, no UI)

### Q: How do I contribute to Socrates?
**A**: See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) and [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## Errors & Issues

### Q: "API key required" error
**A**: Set environment variable: `export ANTHROPIC_API_KEY="sk-ant-..."`

### Q: "401 Unauthorized" error
**A**:
1. Check API key is valid
2. Clear browser cache
3. Restart application
See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#401-unauthorized-error-web-frontend)

### Q: "Project not found" error
**A**:
1. Check spelling: `/project list`
2. Use exact project name
3. Project may have been deleted

### Q: Python version error
**A**: Upgrade Python: `python --version` should be 3.8+

### Q: Module not found error
**A**:
1. Install dependencies: `pip install -r requirements.txt`
2. Or upgrade: `pip install --upgrade socrates-ai`

### Q: Still having issues?
**A**:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Enable debug: `/debug on`
3. Check logs: `tail ~/.socrates/logs/socratic.log`
4. Open GitHub issue with debug logs

---

## Best Practices

### Q: How often should I backup?
**A**: At least weekly, or before major changes:
```bash
/project export <name>
# Or automate:
0 2 * * * zip -r ~/socrates_backup_$(date +\%Y\%m\%d).zip ~/.socrates
```

### Q: Should I use Haiku or Opus model?
**A**:
- **Haiku**: Fast, cheap, for dialogue and simple tasks (default)
- **Sonnet**: Balanced, best for most use cases
- **Opus**: Complex analysis and code generation

### Q: How detailed should my answers be?
**A**: More is better! The system generates better code with:
- Specific user needs, not vague ones
- Explicit constraints and budget
- Technical preferences
- Performance requirements

### Q: Should I commit exports to Git?
**A**: Yes! Track important exports:
```bash
git add *_export.json
git commit -m "Backup exports"
git push
```

### Q: How do I optimize performance?
**A**:
1. Use Haiku model (faster)
2. Reduce context: `SOCRATES_MAX_CONTEXT=4000`
3. Disable debug logging
4. Close other apps

---

## Getting More Help

| Need | Go To |
|---|---|
| Installation help | [INSTALLATION.md](INSTALLATION.md) or [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) |
| Usage help | [USER_GUIDE.md](USER_GUIDE.md) |
| Troubleshooting | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| API documentation | [API_REFERENCE.md](API_REFERENCE.md) |
| Project management | [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md) |
| Integrations | [INTEGRATIONS.md](INTEGRATIONS.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Contributing | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| Report bug | [GitHub Issues](https://github.com/Nireus79/Socrates/issues) |
| Ask question | [GitHub Discussions](https://github.com/Nireus79/Socrates/discussions) |

---

**Last Updated**: January 2026
**Version**: 1.3.0
