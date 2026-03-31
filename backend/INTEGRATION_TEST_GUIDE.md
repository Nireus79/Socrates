# Integration Test Guide

**Complete guide for running and understanding the E2E library integration tests**

---

## Quick Start

### Run All Integration Tests

```bash
# Run both test suites
pytest backend/tests/integration/test_e2e_library_integration.py backend/tests/integration/test_router_library_usage.py -v

# Run with detailed output
pytest backend/tests/integration/test_e2e_library_integration.py -v -s

# Run specific test class
pytest backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization -v

# Run specific test
pytest backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization::test_analyzer_singleton_initialized_once -v
```

---

## Test Files Overview

### 1. `test_e2e_library_integration.py` (26 test cases)

Tests complete end-to-end library integration and caching.

#### Test Classes

**TestLibrarySingletonInitialization** (6 tests)
- Verifies all 6 library singletons are initialized once
- Checks that subsequent accesses return same instance
- Validates singleton reset functionality

Tests:
- `test_analyzer_singleton_initialized_once` - AnalyzerIntegration singleton
- `test_rag_singleton_initialized_once` - RAGIntegration singleton
- `test_learning_singleton_initialized_once` - LearningIntegration singleton
- `test_knowledge_singleton_initialized_once` - KnowledgeManager singleton
- `test_workflow_singleton_initialized_once` - WorkflowIntegration singleton
- `test_documentation_singleton_initialized_once` - DocumentationGenerator singleton

**TestCacheLayerIntegration** (6 tests)
- Validates cache storage, retrieval, expiration
- Tests TTL-based cache behavior
- Verifies hit/miss rate tracking
- Tests coordinated cache invalidation

Tests:
- `test_query_cache_stores_and_retrieves` - Basic cache operations
- `test_query_cache_ttl_expiration` - Automatic TTL expiration
- `test_query_cache_hit_rate_tracking` - Hit/miss statistics
- `test_cache_invalidation_removes_entry` - Cache invalidation
- `test_coordinated_cache_invalidation` - Multi-cache invalidation
- `test_all_singletons_different_instances` - Singleton isolation

**TestAsyncOrchestrationIntegration** (2 tests)
- Verifies AsyncOrchestrator non-blocking execution
- Tests async request processing

Tests:
- `test_async_orchestrator_non_blocking` - AsyncOrchestrator instance
- `test_async_orchestrator_process_request` - Async execution

**TestDataFlowIntegration** (4 tests)
- Validates library component presence in integration classes
- Ensures all library methods are properly initialized
- Confirms no local code duplication

Tests:
- `test_analyzer_integration_uses_library_methods`
- `test_rag_integration_uses_library_methods`
- `test_learning_integration_uses_library_methods`
- `test_knowledge_manager_uses_library_methods`

**TestErrorHandlingNonFallback** (2 tests)
- Confirms routers don't have fallback patterns
- Validates fail-fast error handling

Tests:
- `test_no_try_except_fallbacks_in_routers`
- `test_library_initialization_fails_fast`

**TestPerformanceOptimizationsVerified** (3 tests)
- Measures singleton caching overhead reduction
- Validates cache hit performance improvement
- Checks cache hit rates

Tests:
- `test_singleton_caching_eliminates_overhead`
- `test_query_cache_hit_performance`
- `test_query_cache_hit_rate`

**TestEndToEndWorkflow** (3 tests)
- Tests complete workflows through all components
- Validates request → library → response flow

Tests:
- `test_code_analysis_workflow`
- `test_rag_workflow`
- `test_knowledge_management_workflow`

**TestIntegrationBoundaries** (1 test)
- Ensures proper separation of concerns
- Validates library encapsulation

---

### 2. `test_router_library_usage.py` (18 test cases)

Tests router-level library integration and dependency injection.

#### Test Classes

**TestAnalysisRouterLibraryUsage** (3 tests)
- Verifies analysis router uses AnalyzerIntegration
- Tests endpoint dependency injection
- Confirms no fallback code patterns

Tests:
- `test_analyze_code_uses_analyzer_singleton`
- `test_calculate_metrics_uses_analyzer_singleton`
- `test_analysis_no_local_fallback_code`

**TestRAGRouterLibraryUsage** (3 tests)
- Verifies RAG router uses RAGIntegration
- Tests document indexing and retrieval
- Confirms no fallback patterns

Tests:
- `test_index_document_uses_rag_singleton`
- `test_retrieve_context_uses_rag_singleton`
- `test_rag_no_local_fallback_code`

**TestLearningRouterLibraryUsage** (3 tests)
- Verifies learning router uses LearningIntegration
- Tests interaction logging and progress tracking
- Confirms no fallback patterns

Tests:
- `test_log_interaction_uses_learning_singleton`
- `test_get_progress_uses_learning_singleton`
- `test_learning_no_local_fallback_code`

**TestKnowledgeManagementRouterLibraryUsage** (2 tests)
- Verifies knowledge router uses KnowledgeManager and RAGIntegration
- Tests dual service injection
- Confirms no fallback patterns

Tests:
- `test_add_document_uses_km_and_rag_singletons`
- `test_knowledge_no_local_fallback_code`

**TestChatRouterAsyncIntegration** (1 test)
- Verifies chat router uses AsyncOrchestrator
- Tests non-blocking execution

Tests:
- `test_get_next_question_uses_async_orchestrator`

**TestLibraryComponentsImportedCorrectly** (4 tests)
- Validates all library components are imported
- Ensures proper library delegation
- Confirms no local implementations

Tests:
- `test_analyzer_integration_imports_socratic_analyzer`
- `test_rag_integration_imports_socratic_rag`
- `test_learning_integration_imports_socratic_learning`
- `test_knowledge_manager_imports_socratic_knowledge`

**TestDependencyInjectionPattern** (3 tests)
- Verifies FastAPI dependency injection in routers
- Checks proper parameter annotations
- Validates Depends() usage

Tests:
- `test_analyzer_router_endpoint_has_dependency`
- `test_rag_router_endpoint_has_dependency`
- `test_learning_router_endpoint_has_dependency`

**TestNoCodeDuplication** (3 tests)
- Confirms no duplicate implementations
- Validates delegation pattern
- Ensures routers delegate, don't implement

Tests:
- `test_no_duplicate_code_analysis_logic`
- `test_no_duplicate_rag_logic`
- `test_routers_delegate_not_implement`

---

## Test Execution Matrix

### Run by Category

```bash
# Singleton initialization tests only
pytest backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization -v

# Cache integration tests only
pytest backend/tests/integration/test_e2e_library_integration.py::TestCacheLayerIntegration -v

# Router dependency injection tests only
pytest backend/tests/integration/test_router_library_usage.py::TestDependencyInjectionPattern -v

# No code duplication tests
pytest backend/tests/integration/test_router_library_usage.py::TestNoCodeDuplication -v

# Performance verification tests
pytest backend/tests/integration/test_e2e_library_integration.py::TestPerformanceOptimizationsVerified -v
```

### Run by Priority

```bash
# Priority 1: Verify singletons work
pytest backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization -v

# Priority 2: Verify caching works
pytest backend/tests/integration/test_e2e_library_integration.py::TestCacheLayerIntegration -v

# Priority 3: Verify routers use libraries
pytest backend/tests/integration/test_router_library_usage.py::TestAnalysisRouterLibraryUsage -v
pytest backend/tests/integration/test_router_library_usage.py::TestRAGRouterLibraryUsage -v
pytest backend/tests/integration/test_router_library_usage.py::TestLearningRouterLibraryUsage -v

# Priority 4: Verify no duplication
pytest backend/tests/integration/test_router_library_usage.py::TestNoCodeDuplication -v

# Priority 5: Verify async works
pytest backend/tests/integration/test_e2e_library_integration.py::TestAsyncOrchestrationIntegration -v
```

---

## Understanding Test Output

### Successful Test Output

```
backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization::test_analyzer_singleton_initialized_once PASSED [5%]

✅ PASSED = Test assertion succeeded
✅ All library singletons properly initialized
✅ Dependency injection working correctly
```

### Test Failure

```
FAILED - AssertionError: analyzer1 is not analyzer2
Expected: Same instance (object identity)
Actual: Different instances
Issue: Singleton pattern not working - library re-initialized on each access
Fix: Check library_cache.py for proper singleton implementation
```

### What Each Test Validates

**Singleton Tests** ✅
- Library initialization happens once
- Subsequent accesses return same instance
- Memory efficiency (no re-creation)
- Dependency injection pattern works

**Cache Tests** ✅
- Cache stores and retrieves data
- TTL-based expiration works
- Hit/miss rates tracked correctly
- Coordinated invalidation clears related caches

**Router Tests** ✅
- Routers get library dependencies
- Correct library methods are called
- No fallback implementations exist
- No .available checks or try/except fallbacks

**Integration Tests** ✅
- Data flows through all layers
- Libraries are actually used (not mocked)
- Database persists correctly
- Async operations don't block

---

## Expected Test Results

### Full Test Suite (44 tests)

**Expected**: ALL PASS ✅

```
======================== 44 passed in X.XXs ========================

Test Summary:
- Singleton initialization: 6/6 PASS ✅
- Cache integration: 6/6 PASS ✅
- Async orchestration: 2/2 PASS ✅
- Data flow: 4/4 PASS ✅
- Error handling: 2/2 PASS ✅
- Performance: 3/3 PASS ✅
- E2E workflows: 3/3 PASS ✅
- Router analysis: 3/3 PASS ✅
- Router RAG: 3/3 PASS ✅
- Router learning: 3/3 PASS ✅
- Router knowledge: 2/2 PASS ✅
- Router chat: 1/1 PASS ✅
- Library imports: 4/4 PASS ✅
- Dependency injection: 3/3 PASS ✅
- Code duplication: 3/3 PASS ✅
```

### What Success Means

✅ **All 73 library components properly integrated**
✅ **All routers using dependency injection correctly**
✅ **All caching layers working properly**
✅ **No local code duplication**
✅ **No fallback implementations**
✅ **Async execution non-blocking**
✅ **Complete end-to-end data flows**
✅ **Production-ready integration**

---

## Troubleshooting Failed Tests

### Singleton Initialization Fails

```
test_analyzer_singleton_initialized_once FAILED
AssertionError: analyzer1 is not analyzer2
```

**Cause**: Singleton not properly implemented
**Fix**: Check `library_cache.py`:
- Verify `_analyzer_instance` class variable exists
- Check `get_analyzer()` checks `if _analyzer_instance is None`
- Ensure `get_analyzer_service()` returns result of `get_analyzer()`

### Cache Tests Fail

```
test_query_cache_stores_and_retrieves FAILED
AssertionError: None != ['project1']
```

**Cause**: Cache not storing values
**Fix**: Check `query_cache.py`:
- Verify `set()` method stores in `self.cache` dict
- Check `get()` returns value from dict
- Ensure CacheEntry is properly created

### Router Tests Fail

```
test_analyze_code_uses_analyzer_singleton FAILED
AssertionError: mock_get_analyzer not called
```

**Cause**: Router not using dependency injection
**Fix**: Check `analysis.py`:
- Add `analyzer: AnalyzerIntegration = Depends(get_analyzer_service)`
- Use `analyzer.method()` in endpoint implementation
- Remove any local library initialization

### TTL Expiration Fails

```
test_query_cache_ttl_expiration FAILED
AssertionError: ['project'] != None
```

**Cause**: Cache entry not expiring after TTL
**Fix**: Check `query_cache.py`:
- Verify `is_expired()` method checks age > ttl_seconds
- Check `get()` method deletes expired entries
- Ensure datetime tracking is correct

---

## Debugging Tips

### Enable Verbose Output

```bash
pytest backend/tests/integration/test_e2e_library_integration.py -v -s
```

`-v` = Verbose output
`-s` = Show print statements

### Run Single Test with Debugging

```bash
pytest backend/tests/integration/test_e2e_library_integration.py::TestLibrarySingletonInitialization::test_analyzer_singleton_initialized_once -v -s --tb=long
```

`--tb=long` = Detailed traceback

### Check Test Dependencies

```python
# In test file, add debugging
def test_example():
    analyzer = get_analyzer_service()
    print(f"Analyzer type: {type(analyzer)}")
    print(f"Has analyzer attr: {hasattr(analyzer, 'analyzer')}")
    print(f"Analyzer dir: {[x for x in dir(analyzer) if not x.startswith('_')]}")
```

### Verify Imports

```bash
# Test imports in Python shell
python -c "from socrates_api.services.library_cache import get_analyzer_service; analyzer = get_analyzer_service(); print(type(analyzer))"
```

---

## Integration Test Checklist

Before deploying to production:

- [ ] All 44 tests pass
- [ ] No import errors
- [ ] No timeout errors
- [ ] No database errors
- [ ] Singleton reuse confirmed
- [ ] Cache hits confirmed
- [ ] No fallback code patterns found
- [ ] All routers use dependency injection
- [ ] All 73 library components present
- [ ] Performance improvements measured

---

## Performance Baseline

### Expected Test Performance

| Test | Expected Time | Category |
|------|---|---|
| Singleton initialization | <10ms | Fast |
| Cache operations | <5ms | Very Fast |
| Router dependency injection | <50ms | Medium |
| TTL expiration | ~1100ms | Slow (includes sleep) |
| Coordinated invalidation | <10ms | Fast |
| Async orchestration | <100ms | Medium |
| Full E2E workflow | <200ms | Medium |

**Total expected runtime**: 30-60 seconds for full suite

If tests take significantly longer:
- Check system load
- Check database performance
- Check network latency
- Check for timeout issues

---

## Next Steps After Tests Pass

1. **Deploy to staging**
   ```bash
   git commit -m "Integration tests pass: all 73 library components verified"
   git push origin master
   ```

2. **Run health checks**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Verify endpoints work**
   ```bash
   curl -X POST http://localhost:8000/analysis/validate \
     -H "Content-Type: application/json" \
     -d '{"project_id":"test","code":"print()"}'
   ```

4. **Monitor cache stats**
   ```python
   from socrates_api.services.query_cache import get_query_cache
   stats = get_query_cache().get_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
   ```

5. **Load test**
   ```bash
   pytest backend/tests/performance/test_load.py -v
   ```

---

## Support

For issues with integration tests:

1. Check the error message and traceback
2. Review the corresponding implementation file
3. Run the specific failing test with `-v -s`
4. Add print statements for debugging
5. Check `INTEGRATION_VERIFICATION_COMPLETE.md` for architecture overview

---

**All tests should pass ✅ indicating 100% library integration**
