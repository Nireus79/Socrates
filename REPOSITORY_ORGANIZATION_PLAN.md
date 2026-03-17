# Repository Organization Plan

**Date**: March 17, 2026
**Status**: Analysis Complete - Ready for Implementation
**Scope**: Both branches (master + feature/modular-platform-v2)

---

## Current State Analysis

### Branch 1: MASTER
**Purpose**: Socrates Ecosystem (8 published PyPI packages)
**Status**: Phase 4e Complete
**Focus**: Package distribution and monetization through PyPI + Openclaw + LangChain

**Root-Level Files**:
- `PLAN.md` (89KB) - Master plan for ecosystem
- `IMPLEMENTATION_SUMMARY.md` - Summary of implementation
- `SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md` - Ecosystem integration
- `SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md` - Architecture
- `API_ROUTE_DESIGN.md` - API design
- `DATA_MODELS_SPECIFICATION.md` - Data models
- `DEPLOYMENT_TEMPLATES.md` - Deployment
- `EXAMPLES.md` - Examples
- `NEXT_STEPS.md` - Next steps
- `PHASE_1_IMPLEMENTATION_GUIDE.md` - Phase 1 guide (obsolete context)
- `PROMOTION.md` - Promotion strategy
- `MARKETING_MATERIALS.md` - Marketing materials
- `COMMUNITY_ENGAGEMENT.md` - Community engagement
- `COMMUNITY_LAUNCH_ROADMAP.md` - Community launch
- `HERMESSOFT_WEBSITE_REDESIGN.md` - Website redesign
- `CHANGELOG.md` - Changelog
- `README.md` - README

**Docs Folder** (43 markdown files):
- Main docs: ARCHITECTURE.md, API_REFERENCE.md, INSTALLATION.md, etc.
- NO phase-specific folders
- NO marketing folder
- Subdirectories: adr/, database/, deployment/, guides/, operations/, rbac/

---

### Branch 2: FEATURE/MODULAR-PLATFORM-V2
**Purpose**: Main Socrates Platform (REST API + Phase 4 Services)
**Status**: Phase 5 Day 1 Complete
**Focus**: REST API implementation and production-ready deployment

**Root-Level Files**:
- `FUTURE_ROADMAP.md` (NEW) - Phases 5-8 feature roadmap
- `MONETIZATION_READINESS_AUDIT.md` (NEW) - Commercialization audit
- `EXECUTIVE_SUMMARY_MONETIZATION.md` (NEW) - Executive summary
- `CHANGELOG.md` - Changelog
- `README.md` - README

**Docs Folder** (60+ files including):
- Main docs: ARCHITECTURE.md, API_REFERENCE.md, etc.
- **Marketing folder**: PROMOTION.md, MARKETING_MATERIALS.md, etc.
- **Phase-specific folders**:
  - phase-1/ (5 files) - Module restructuring
  - phase-2/ (5 files) - Service layer implementation
  - phase-3/ (3 files) - EventBus & pub/sub
  - phase-4/ (3 files) - Skill ecosystem
  - phase-5/ (1 file) - REST API
- Subdirectories: adr/, api/, architecture/, database/, deployment/, guides/, operations/, rbac/

---

## Issues Identified

### 1. Duplicate Content Across Branches
- `PROMOTION.md` - On both master and feature branch
- `MARKETING_MATERIALS.md` - On both master and feature branch
- `COMMUNITY_ENGAGEMENT.md` - On both master and feature branch
- `COMMUNITY_LAUNCH_ROADMAP.md` - On both master and feature branch
- Multiple planning/architecture documents on master

### 2. Obsolete Documentation
**On feature/modular-platform-v2**:
- `docs/phase-1/PHASE_1_IMPLEMENTATION_GUIDE.md` - Phase 1 is DONE
- `docs/phase-2/PHASE_2_IMPLEMENTATION_GUIDE.md` - Phase 2 is DONE
- `docs/phase-3/` - Phase 3 is DONE
- `docs/phase-4/` - Phase 4 is DONE
- These should be archived, not active

### 3. Root-Level Clutter (Master Branch)
Too many planning documents at root level:
- `API_ROUTE_DESIGN.md`
- `DATA_MODELS_SPECIFICATION.md`
- `DEPLOYMENT_TEMPLATES.md`
- `IMPLEMENTATION_SUMMARY.md`
- `PHASE_1_IMPLEMENTATION_GUIDE.md`
- `SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md`
- `SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md`

These should be organized into docs/ folders.

### 4. No Clear Planning Documents
The new documents on feature branch are good, but:
- `FUTURE_ROADMAP.md` - Excellent, should be on both branches
- `MONETIZATION_READINESS_AUDIT.md` - Excellent, should be on both branches
- `EXECUTIVE_SUMMARY_MONETIZATION.md` - Excellent, should be on both branches

### 5. Marketing Documents Organization
Marketing is important but scattered:
- Root level on master: PROMOTION.md, MARKETING_MATERIALS.md, COMMUNITY_*.md
- docs/marketing/ on feature branch: Same files

Should consolidate to single location.

---

## Proposed Organization Structure

### Root Level (Clean)
Keep ONLY:
- `README.md` - Main project readme
- `LICENSE` - License file
- `.gitignore` - Git ignore
- `CHANGELOG.md` - Changelog
- `PLAN.md` (Master only) - Ecosystem master plan
- `CONTRIBUTING.md` - Contributing guidelines
- `FUTURE_ROADMAP.md` (Feature branch) - Future feature roadmap
- `MONETIZATION_READINESS_AUDIT.md` (Feature branch) - Audit document
- `EXECUTIVE_SUMMARY_MONETIZATION.md` (Feature branch) - Executive summary

Move everything else to docs/

### Docs/ Folder Structure

```
docs/
├── README.md (index/guide to all docs)
├── QUICK_START.md (5-minute start)
├── ARCHITECTURE.md (system architecture)
├── API_REFERENCE.md (API documentation)
├──
├── guides/
│   ├── INSTALLATION.md
│   ├── DEPLOYMENT.md
│   ├── CONFIGURATION.md
│   ├── DEVELOPER_GUIDE.md
│   ├── USER_GUIDE.md
│   ├── TROUBLESHOOTING.md
│   └── WINDOWS_SETUP.md
│
├── marketing/ (monetization & promotion)
│   ├── README.md (marketing guide index)
│   ├── MONETIZATION_STRATEGY.md (revenue models)
│   ├── PROMOTION.md (30+ channels)
│   ├── MARKETING_MATERIALS.md (templates & brands)
│   ├── COMMUNITY_ENGAGEMENT.md (community strategy)
│   ├── COMMUNITY_LAUNCH_ROADMAP.md (launch timeline)
│   └── CASE_STUDIES.md (customer examples)
│
├── technical/ (technical deep dives)
│   ├── API_DESIGN.md (formerly API_ROUTE_DESIGN.md)
│   ├── DATA_MODELS.md (formerly DATA_MODELS_SPECIFICATION.md)
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md (architecture)
│   ├── INTEGRATIONS.md
│   └── MATURITY_CALCULATION_SYSTEM.md
│
├── compliance/
│   ├── RBAC_DOCUMENTATION.md
│   ├── SECURITY.md
│   ├── SPONSORSHIP.md
│   └── TIERS_AND_SUBSCRIPTIONS.md
│
├── enterprise/ (on feature branch)
│   ├── MULTI_TENANCY.md
│   ├── ENTERPRISE_FEATURES.md
│   └── SLA_REQUIREMENTS.md
│
├── roadmap/ (on feature branch)
│   ├── README.md (roadmap guide)
│   ├── FUTURE_ROADMAP.md (moved from root)
│   └── PHASE_STATUS.md (consolidated phases)
│
├── archive/ (obsolete/completed phases)
│   ├── PHASE_1_COMPLETION.md
│   ├── PHASE_2_COMPLETION.md
│   ├── PHASE_3_COMPLETION.md
│   ├── PHASE_4_COMPLETION.md
│   └── PHASE_5_STATUS.md
│
├── api/ (API docs)
├── adr/ (Architecture Decision Records)
├── database/ (Database docs)
├── deployment/ (Deployment configs)
├── operations/ (Operations & monitoring)
└── rbac/ (RBAC documentation)
```

---

## Implementation Plan

### Phase 1: Analysis & Backup (Today)
1. Create comprehensive inventory (THIS DOCUMENT) ✅
2. Create git backup of both branches
3. Create detailed task list

### Phase 2: Master Branch Organization (Week 1)
1. Create docs/marketing/ folder
2. Create docs/technical/ folder
3. Create docs/roadmap/ folder
4. Move files from root to appropriate docs/ subfolders:
   - PROMOTION.md → docs/marketing/
   - MARKETING_MATERIALS.md → docs/marketing/
   - COMMUNITY_*.md → docs/marketing/
   - API_ROUTE_DESIGN.md → docs/technical/API_DESIGN.md
   - DATA_MODELS_SPECIFICATION.md → docs/technical/DATA_MODELS.md
   - DEPLOYMENT_TEMPLATES.md → docs/technical/DEPLOYMENT_ARCHITECTURE.md
   - IMPLEMENTATION_SUMMARY.md → docs/archive/ECOSYSTEM_IMPLEMENTATION.md
   - SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md → docs/technical/ECOSYSTEM_INTEGRATION.md
   - SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md → docs/technical/ARCHITECTURE_DETAIL.md
   - PHASE_1_IMPLEMENTATION_GUIDE.md → docs/archive/
5. Update root-level README with new structure

### Phase 3: Feature Branch Organization (Week 1)
1. Create docs/archive/ folder
2. Create docs/roadmap/ folder
3. Archive completed phases:
   - docs/phase-1/* → docs/archive/phase-1/
   - docs/phase-2/* → docs/archive/phase-2/
   - docs/phase-3/* → docs/archive/phase-3/
   - docs/phase-4/* → docs/archive/phase-4/
   - Keep only: docs/phase-5/ (current active phase)
4. Move marketing from docs/marketing/ → update structure (merge with docs/marketing/)
5. Create docs/roadmap/:
   - Move FUTURE_ROADMAP.md → docs/roadmap/
   - Create PHASE_STATUS.md showing current phase
6. Create docs/enterprise/ (for future multi-tenancy, etc):
   - MONETIZATION_READINESS_AUDIT.md → docs/roadmap/
   - EXECUTIVE_SUMMARY_MONETIZATION.md → docs/roadmap/

### Phase 4: Branch Merge Preparation (Week 2)
1. Ensure both branches have consistent structure
2. Create MERGE_GUIDE.md with conflict resolution strategy
3. Update both branch README files
4. Create comprehensive docs/README.md that explains structure

### Phase 5: Documentation Updates (Week 2)
1. Create docs/marketing/README.md (index)
2. Create docs/technical/README.md (index)
3. Create docs/roadmap/README.md (index)
4. Update main README.md with new structure
5. Create docs/README.md (master index)

---

## Specific Files to Move/Archive

### MASTER BRANCH - Move to docs/

| File | Move To | New Name | Reason |
|------|---------|----------|--------|
| PROMOTION.md | docs/marketing/ | (same) | Organize marketing |
| MARKETING_MATERIALS.md | docs/marketing/ | (same) | Organize marketing |
| COMMUNITY_ENGAGEMENT.md | docs/marketing/ | (same) | Organize marketing |
| COMMUNITY_LAUNCH_ROADMAP.md | docs/marketing/ | (same) | Organize marketing |
| API_ROUTE_DESIGN.md | docs/technical/ | API_DESIGN.md | Clarify purpose |
| DATA_MODELS_SPECIFICATION.md | docs/technical/ | DATA_MODELS.md | Shorten name |
| DEPLOYMENT_TEMPLATES.md | docs/technical/ | DEPLOYMENT_ARCHITECTURE.md | Clarify scope |
| IMPLEMENTATION_SUMMARY.md | docs/archive/ | ECOSYSTEM_IMPLEMENTATION.md | Archive completed |
| SOCRATES_AI_ECOSYSTEM_INTEGRATION_PLAN.md | docs/technical/ | ECOSYSTEM_INTEGRATION.md | Shorten name |
| SOCRATES_AI_MODULAR_PLATFORM_ARCHITECTURE.md | docs/technical/ | ARCHITECTURE_DETAIL.md | Shorten name |
| PHASE_1_IMPLEMENTATION_GUIDE.md | docs/archive/ | (same) | Archive completed |

### FEATURE BRANCH - Archive Phases

| Folder | Move To | Reason |
|--------|---------|--------|
| docs/phase-1/ | docs/archive/phase-1/ | Phase 1 complete |
| docs/phase-2/ | docs/archive/phase-2/ | Phase 2 complete |
| docs/phase-3/ | docs/archive/phase-3/ | Phase 3 complete |
| docs/phase-4/ | docs/archive/phase-4/ | Phase 4 complete |

### FEATURE BRANCH - Migrate to Root

| File | New Location | Reason |
|------|--------------|--------|
| FUTURE_ROADMAP.md | docs/roadmap/FUTURE_ROADMAP.md | Keep visible |
| MONETIZATION_READINESS_AUDIT.md | docs/roadmap/MONETIZATION_READINESS_AUDIT.md | Archive completed |
| EXECUTIVE_SUMMARY_MONETIZATION.md | docs/roadmap/EXECUTIVE_SUMMARY_MONETIZATION.md | Executive reference |

---

## Files to Keep at Root Level

### MASTER + FEATURE
- `README.md` - Main project readme
- `CHANGELOG.md` - Version changelog
- `LICENSE` - MIT license
- `.gitignore` - Git ignore rules
- `.github/` - GitHub workflows and templates
- `CONTRIBUTING.md` - Contributing guidelines

### FEATURE ONLY (Until Merge)
- `FUTURE_ROADMAP.md` - Keep visible at root for next phase planning
- Optionally move to docs/roadmap/ after this sprint

---

## Merge Strategy

When branches are merged (master ← feature/modular-platform-v2):

1. **Primary**: Take feature branch structure (it's more organized)
2. **Merge marketing docs**: Both have good content
   - Keep all from feature branch (docs/marketing/)
   - Add unique items from master
3. **Merge technical docs**: Reconcile duplicates
   - Keep most comprehensive versions
4. **Archive all completed phases**: In docs/archive/
5. **Create unified docs/README.md**: Explain new structure
6. **Update main README**: Link to new docs structure

---

## Quick Win Priority Order

### Week 1 - Quick Wins (2-3 hours)
1. ✅ Create docs/marketing/ folder
2. ✅ Create docs/archive/ folder
3. Move 6 marketing files (PROMOTION.md, MARKETING_MATERIALS.md, COMMUNITY_*.md)
4. Move API/Data/Deployment design docs

### Week 2 - Phase Archive (1-2 hours)
1. Create docs/archive/phase-* structure
2. Move phase-1 through phase-4 files
3. Create PHASE_STATUS.md

### Week 3 - Documentation (2-3 hours)
1. Create README files in each subdirectory
2. Update main README with new structure
3. Update CONTRIBUTING guidelines

---

## Files to Check Before Moving

Before moving files, verify:
- ✅ Each file is referenced in any PLAN.md or main docs
- ✅ Internal links in files are updated after move
- ✅ No hardcoded paths to moved files

### Commands to Find References

```bash
# Find references to files being moved
grep -r "PROMOTION.md" docs/ --include="*.md"
grep -r "MARKETING_MATERIALS" docs/ --include="*.md"
grep -r "phase-1" docs/ --include="*.md"
```

---

## Risk Mitigation

### Risks
1. **Breaking internal links** when files move
   - Mitigation: Use relative paths, test all links after move
2. **Losing file history** in git
   - Mitigation: Use `git mv` (preserves history), not delete+add
3. **Inconsistency between branches**
   - Mitigation: Document exact same structure on both

### Testing
- Verify all markdown links work after move
- Check git log on moved files shows full history
- Verify branch merge doesn't have conflicts

---

## Deliverables

### At End of Organization
- [ ] Both branches have clean root level (only essential files)
- [ ] docs/ folder has clear, logical structure
- [ ] All docs/ subfolders have README explaining contents
- [ ] All phase documentation archived but accessible
- [ ] Marketing docs consolidated and organized
- [ ] No broken internal links
- [ ] Git history preserved for all moved files
- [ ] Merge-ready branches (minimal conflicts expected)

---

## Next Steps

1. **Confirm Approach**: Review this plan with stakeholders
2. **Start Master Branch**: Move files on master first (lower risk)
3. **Start Feature Branch**: Mirror structure, archive phases
4. **Update README**: Ensure discoverability
5. **Test Merge**: Verify minimal conflicts before full merge

---

## Summary Table

| Category | Master Branch | Feature Branch | Action |
|----------|---------------|-----------------|--------|
| Root files | Too many | Good | Archive most files |
| docs/ structure | Flat | Somewhat organized | Create subfolders |
| Marketing | At root | In subfolder | Consolidate to docs/marketing/ |
| Phases | Not present | Multiple folders | Archive to docs/archive/ |
| Planning docs | Very thorough | Good | Organize into docs/roadmap/ |
| Duplicate content | Yes (marketing) | Yes (marketing) | Single source of truth |
| Ready to merge | 70% | 80% | Complete organization → 95% |

---

**Document Status**: Ready for Implementation
**Created**: March 17, 2026
**Ready to Execute**: Yes, after stakeholder approval

