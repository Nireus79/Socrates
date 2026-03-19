# ⚠️ Package Deprecation Notice

**Date**: March 19, 2026
**Status**: DEPRECATED - Do not use for new projects

---

## Deprecated Packages

### 1. socrates-ai (v1.3.4) - DEPRECATED ❌

**Status**: Deprecated in favor of modular architecture
**Last Updated**: January 16, 2026
**Support**: Critical bug fixes only

#### What to Do

```bash
# DON'T use this
pip install socrates-ai

# USE these instead
pip install socratic-core>=0.1.1
pip install socratic-learning>=0.1.1
```

#### Why It's Deprecated

- **Monolithic architecture**: Single large package with everything
- **Inefficient**: You can't install just what you need
- **Hard to maintain**: Updates affect all users even if they only need one feature
- **Better option**: Use modular `socratic-core`, `socratic-learning`, etc.

#### Migration Path

See [MIGRATION_GUIDE_PACKAGE_UPDATES.md](MIGRATION_GUIDE_PACKAGE_UPDATES.md)

---

### 2. socrates-ai-openclaw (v1.0.0) - BROKEN & DEPRECATED ❌❌

**Status**: BROKEN - Do not install
**Critical Issue**: Depends on non-existent `socrates-ai>=1.3.0`
**Last Updated**: February 25, 2026
**Support**: NONE - Package is broken

#### What Happens If You Try To Install It

```bash
$ pip install socrates-ai-openclaw
ERROR: Collecting socrates-ai>=1.3.0 (from socrates-ai-openclaw==1.0.0)
ERROR: No matching distribution found for socrates-ai>=1.3.0
```

**Result**: Installation fails. Package cannot be used.

#### Solution

Use the new package instead:

```bash
# Install working replacement
pip install socratic-openclaw-skill>=0.1.0
```

#### What Changed

| Aspect | Old | New |
|--------|-----|-----|
| Package Name | socrates-ai-openclaw | **socratic-openclaw-skill** |
| Version | 1.0.0 | **0.1.0** |
| Dependencies | ❌ Broken: `socrates-ai>=1.3.0` | ✅ Working: `socratic-core>=0.1.1` |
| Status | Broken | Production Ready |

---

## New Recommended Packages

### ✅ socratic-openclaw-skill (v0.1.0) - MODERN

**Status**: Production Ready (NEW)
**Released**: March 19, 2026
**Support**: Full support

```bash
pip install socratic-openclaw-skill
```

**Benefits**:
- ✅ Works with OpenClaw
- ✅ Uses modern `socratic-core` library
- ✅ Fixed dependency chain
- ✅ Better API
- ✅ Full documentation

---

### ✅ socrates-ai-langraph (v0.1.0) - NEW

**Status**: Production Ready (NEW)
**Released**: March 19, 2026
**Support**: Full support

```bash
pip install socrates-ai-langraph
```

**Benefits**:
- ✅ Works with LangGraph
- ✅ Framework-agnostic design
- ✅ Type-safe state management
- ✅ Modular agent system
- ✅ Full documentation

---

## Timeline

| Date | Event | Status |
|------|-------|--------|
| **Jan 16, 2026** | socrates-ai v1.3.4 released | ⚠️ Deprecated |
| **Feb 25, 2026** | socrates-ai-openclaw v1.0.0 released | ❌ Broken |
| **Mar 19, 2026** | New packages released + deprecation notice | ✅ **TODAY** |
| **Mar 20, 2026** | Old packages marked as deprecated on PyPI | ⏳ Pending |
| **Sep 19, 2026** | Support period ends (6 months) | ⏳ Future |
| **Sep 20, 2026** | Old packages removed from pip recommended installs | ⏳ Future |

---

## Current PyPI Status

### Deprecated (Still Available)

```bash
pip install socrates-ai  # ⚠️ Works but deprecated
pip install socrates-ai-openclaw  # ❌ Broken - DO NOT INSTALL
```

### New & Recommended

```bash
pip install socratic-core  # ✅ Latest foundation
pip install socratic-learning  # ✅ Latest learning engine
pip install socratic-openclaw-skill  # ✅ New OpenClaw integration
pip install socrates-ai-langraph  # ✅ New LangGraph integration
```

---

## FAQ

### Q: Can I still use socrates-ai?

**A**: Yes, but it's deprecated. Existing code will continue to work due to backward compatibility, but:
- No new features will be added
- Only critical security updates
- New projects should use `socratic-core` + modular libraries

### Q: Why is socrates-ai-openclaw broken?

**A**: It depends on `socrates-ai>=1.3.0`, but the main package was split into modular libraries. The dependency no longer exists at that version constraint.

### Q: Can I install socrates-ai-openclaw?

**A**: **No**. Installation will fail. Use `socratic-openclaw-skill` instead.

### Q: When will old packages be removed?

**A**: They'll remain available for 6 months (until September 19, 2026) with deprecation warnings. After that, they may be removed from PyPI's recommended installs.

### Q: How do I migrate?

**A**: See [MIGRATION_GUIDE_PACKAGE_UPDATES.md](MIGRATION_GUIDE_PACKAGE_UPDATES.md) for step-by-step instructions.

### Q: Are new packages production-ready?

**A**: Yes! Both new packages are thoroughly tested and production-ready.

### Q: What about backward compatibility?

**A**: The main `socrates-ai` package maintains 100% backward compatibility with old imports. However, it's still deprecated.

---

## Support

### For socrates-ai (deprecated)

- **Bug Reports**: Yes, critical fixes only
- **Feature Requests**: No, use new packages
- **Upgrade Path**: See migration guide
- **Recommendation**: Migrate within 6 months

### For socrates-ai-openclaw (broken)

- **Bug Reports**: No, package is broken
- **Feature Requests**: No, use new package
- **Upgrade Path**: Install `socratic-openclaw-skill` instead
- **Recommendation**: Migrate immediately

### For New Packages

- **socratic-openclaw-skill**: Full support, version 0.1.0+
- **socrates-ai-langraph**: Full support, version 0.1.0+
- **socratic-core**: Full support, version 0.1.1+
- **socratic-learning**: Full support, version 0.1.1+

---

## Migration Urgency Matrix

| Situation | Urgency | Action |
|-----------|---------|--------|
| Using socrates-ai for new project | 🔴 **CRITICAL** | Stop! Use socratic-core instead |
| Using socrates-ai in existing project | 🟡 **HIGH** | Plan migration within 6 months |
| Trying to install socrates-ai-openclaw | 🔴 **CRITICAL** | Use socratic-openclaw-skill instead |
| Want LangGraph support | 🟢 **LOW** | Try socrates-ai-langraph |
| Happy with old package | 🟡 **MEDIUM** | Plan migration eventually |

---

## Contact

- **GitHub Issues**: [Report problems](https://github.com/Nireus79/Socrates/issues)
- **Email**: support@socrates-ai.dev
- **Docs**: [Full documentation](https://github.com/Nireus79/Socrates)

---

## Summary

| Package | Status | Action |
|---------|--------|--------|
| **socrates-ai** | ⚠️ Deprecated | Migrate to modular libs |
| **socrates-ai-openclaw** | ❌ Broken | Switch to socratic-openclaw-skill |
| **socratic-openclaw-skill** | ✅ New | Use for OpenClaw |
| **socrates-ai-langraph** | ✅ New | Use for LangGraph |

**All users should plan to migrate to new packages within 6 months.**

---

**Last Updated**: March 19, 2026
**Version**: 1.0
**Status**: Active
