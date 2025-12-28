# Frontend Implementation Plan: Missing Features

**Date**: 2025-12-27
**Status**: In Progress
**Target**: Implement 45+ missing CLI commands as Frontend features

---

## ARCHITECTURE PATTERNS TO FOLLOW

### Page Structure Pattern
```typescript
// 1. Use hooks: useParams, useState, useEffect
// 2. Use stores: useProjectStore, useAuthStore, custom stores
// 3. API calls: apiClient.get/post/put/delete
// 4. Components from ../../components/
// 5. Handle states: loading, error, data
// 6. Layout: MainLayout, PageHeader
```

### Store Pattern
```typescript
// Create stores in socrates-frontend/src/stores/
// Use zustand or similar state management
// Export from stores/index.ts
// Include: state, actions, selectors
```

### API Pattern
```typescript
// Create API functions in socrates-frontend/src/api/
// Use apiClient for HTTP calls
// Handle errors gracefully
// Return typed responses
```

---

## IMPLEMENTATION SEQUENCE

### PHASE 1: Quick Wins (Low Effort, High Value)

#### 1.1 Subscription Management UI
**Files to Modify**:
- socrates-frontend/src/pages/settings/SettingsPage.tsx
- Add subscription tier management section

**Files to Create**: None (enhance existing)

**Expected Changes**:
- Add upgrade/downgrade buttons
- Add plan comparison modal
- Display current tier and billing info

**Verification**:
- [ ] Settings page loads
- [ ] Subscription tier displays correctly
- [ ] Upgrade/downgrade buttons present
- [ ] Plan comparison modal works

**Endpoints Used**:
- GET /subscription/status
- POST /subscription/upgrade
- POST /subscription/downgrade
- GET /subscription/compare

---

#### 1.2 Notes/Memory System
**Files to Create**:
- socrates-frontend/src/pages/notes/NotesPage.tsx
- socrates-frontend/src/stores/notesStore.ts
- socrates-frontend/src/api/notes.ts
- socrates-frontend/src/components/notes/NoteCard.tsx
- socrates-frontend/src/components/notes/NoteForm.tsx
- socrates-frontend/src/components/notes/NotesGrid.tsx

**Files to Modify**:
- socrates-frontend/src/App.tsx (add route)
- socrates-frontend/src/components/layout/Sidebar.tsx (add nav item)
- socrates-frontend/src/stores/index.ts (export notesStore)

**Expected Components**:
- NoteCard: Display individual note
- NoteForm: Create/edit note form
- NotesGrid: Grid of notes
- NotesPage: Main page

**Verification**:
- [ ] NotesPage route works
- [ ] Can create notes
- [ ] Can view notes list
- [ ] Can search notes
- [ ] Can delete notes
- [ ] Sidebar nav shows Notes

**Endpoints Used**:
- GET /notes
- POST /notes
- DELETE /notes/{id}
- PUT /notes/{id}

---

### PHASE 2: High Priority Features

#### 2.1 Project Analysis Suite
**Files to Create**:
- socrates-frontend/src/pages/projects/ProjectAnalysisPage.tsx
- socrates-frontend/src/components/analysis/AnalysisActionPanel.tsx
- socrates-frontend/src/components/analysis/AnalysisResultsDisplay.tsx
- socrates-frontend/src/api/projectAnalysis.ts
- socrates-frontend/src/stores/projectAnalysisStore.ts

**Files to Modify**:
- socrates-frontend/src/App.tsx (add route)
- socrates-frontend/src/components/layout/Sidebar.tsx (enhance Analysis item)
- socrates-frontend/src/pages/projects/ProjectDetailPage.tsx (add Analysis tab)

**Expected Components**:
- AnalysisActionPanel: Buttons for analyze/review/test/validate/diff/fix
- AnalysisResultsDisplay: Display analysis results
- ProjectAnalysisPage: Main page

**Verification**:
- [ ] ProjectAnalysisPage route works
- [ ] Can trigger project analysis
- [ ] Can trigger code review
- [ ] Can view analysis results
- [ ] Diff viewer works

**Endpoints Used**:
- POST /projects/{projectId}/analyze
- POST /projects/{projectId}/review
- POST /projects/{projectId}/test
- POST /projects/{projectId}/validate
- POST /projects/{projectId}/diff
- POST /projects/{projectId}/fix

---

#### 2.2 Maturity & Progress Tracking
**Files to Modify**:
- socrates-frontend/src/pages/analytics/AnalyticsPage.tsx (add maturity tab)
- socrates-frontend/src/components/analytics/MaturityOverview.tsx (enhance)
- Create MaturityHistoryChart component

**Files to Create**:
- socrates-frontend/src/components/analytics/MaturityHistoryChart.tsx
- socrates-frontend/src/api/maturity.ts
- socrates-frontend/src/stores/maturityStore.ts

**Expected Components**:
- MaturityHistoryChart: Show maturity progression over time
- Enhanced MaturityOverview: Show more detailed metrics
- ProgressVisualization: Show project progress

**Verification**:
- [ ] Maturity metrics display
- [ ] Historical data shows
- [ ] Charts render correctly
- [ ] Progress visualization works

**Endpoints Used**:
- GET /projects/{projectId}/maturity
- GET /maturity/history
- GET /analytics/status

---

#### 2.3 GitHub Integration
**Files to Create**:
- socrates-frontend/src/pages/github/GitHubPage.tsx
- socrates-frontend/src/api/github.ts
- socrates-frontend/src/stores/githubStore.ts
- socrates-frontend/src/components/github/RepoImportModal.tsx
- socrates-frontend/src/components/github/SyncStatusWidget.tsx
- socrates-frontend/src/components/github/RepoSelector.tsx

**Files to Modify**:
- socrates-frontend/src/App.tsx (add route)
- socrates-frontend/src/components/layout/Sidebar.tsx (add GitHub nav item)

**Expected Components**:
- RepoImportModal: Import GitHub repository
- SyncStatusWidget: Show sync status
- RepoSelector: Select repository to import
- GitHubPage: Main page

**Verification**:
- [ ] GitHubPage route works
- [ ] Can import repository
- [ ] Sync status displays
- [ ] Pull/push operations work
- [ ] Bi-directional sync works

**Endpoints Used**:
- POST /github/import
- POST /github/sync
- POST /github/pull
- POST /github/push
- GET /github/status

---

### PHASE 3: Medium Priority Features

#### 3.1 Advanced Search
**Files to Create**:
- socrates-frontend/src/pages/search/SearchPage.tsx
- socrates-frontend/src/api/search.ts
- socrates-frontend/src/stores/searchStore.ts
- socrates-frontend/src/components/search/SearchBar.tsx
- socrates-frontend/src/components/search/SearchResultsGrid.tsx
- socrates-frontend/src/components/search/SearchFilters.tsx

**Files to Modify**:
- socrates-frontend/src/App.tsx (add route)
- socrates-frontend/src/components/layout/Sidebar.tsx (add Search nav item - optional)

**Expected Components**:
- SearchBar: Search input with suggestions
- SearchResultsGrid: Display search results
- SearchFilters: Filter search results
- SearchPage: Main page

**Verification**:
- [ ] SearchPage route works
- [ ] Full-text search works
- [ ] Conversation search works
- [ ] Filter functionality works
- [ ] Results display correctly

**Endpoints Used**:
- GET /search?q={query}
- GET /conversations/search?q={query}
- GET /knowledge/search?q={query}
- GET /notes/search?q={query}

---

## VERIFICATION CHECKLIST

### For Each Feature:
- [ ] All required files created
- [ ] All routes added to App.tsx
- [ ] All sidebar nav items added
- [ ] API calls use correct endpoints
- [ ] Error handling implemented
- [ ] Loading states show
- [ ] Empty states handled
- [ ] Responsive design works
- [ ] Store integration works
- [ ] No TypeScript errors

### Integration Tests:
- [ ] Navigation between pages works
- [ ] Data persists across navigation
- [ ] Auth token passes on all API calls
- [ ] Error messages display
- [ ] Success messages display
- [ ] Mobile responsive

---

## ROLLBACK STRATEGY

Each feature is self-contained:
1. Feature-specific files can be deleted
2. Routes can be removed from App.tsx
3. Nav items can be removed from Sidebar.tsx
4. Stores can be removed from exports
5. No shared code changes except routes/nav

---

## SUCCESS CRITERIA

- ✅ All 45+ missing features have UI equivalents
- ✅ All pages follow existing patterns
- ✅ No TypeScript errors
- ✅ All API endpoints integrated
- ✅ Responsive design works
- ✅ Auth protection in place
- ✅ Error handling consistent
- ✅ Loading states present
- ✅ Empty states handled
- ✅ Sidebar navigation updated

---

## TIMELINE ESTIMATE

- Phase 1 (Quick Wins): 6-8 hours
- Phase 2 (High Priority): 12-15 hours
- Phase 3 (Medium Priority): 8-10 hours
- **Total**: 26-33 hours

---

## NOTES

- Follow existing code style and patterns
- Always check API endpoints exist
- Verify stores before using
- Test navigation before moving to next feature
- Commit after each major feature
