"""
Core Integration Tests - Library, Cache, and Data Flow Validation

Tests the core integration without external dependencies.
Validates library singleton injection, caching, and data flows.
"""

import pytest
import time
from socrates_api.library_cache import (
    LibrarySingletons,
    get_analyzer_service,
    get_rag_service,
    get_learning_service,
    get_knowledge_service,
)
from socrates_api.services.query_cache import get_query_cache
from socrates_api.services.cache_keys import CacheKeys, CacheInvalidation
from socrates_api.models_local import (
    AnalyzerIntegration,
    RAGIntegration,
    LearningIntegration,
    KnowledgeManager,
)


class TestLibrarySingletonIntegration:
    """Test library singleton initialization and reuse"""

    def setup_method(self):
        """Reset singletons before each test"""
        LibrarySingletons.reset_all()
        get_query_cache().clear()

    def test_analyzer_singleton_initialized_once(self):
        """Verify AnalyzerIntegration singleton is initialized once"""
        analyzer1 = get_analyzer_service()
        analyzer2 = get_analyzer_service()

        assert analyzer1 is analyzer2
        assert isinstance(analyzer1, AnalyzerIntegration)

    def test_rag_singleton_initialized_once(self):
        """Verify RAGIntegration singleton is initialized once"""
        rag1 = get_rag_service()
        rag2 = get_rag_service()

        assert rag1 is rag2
        assert isinstance(rag1, RAGIntegration)

    def test_learning_singleton_initialized_once(self):
        """Verify LearningIntegration singleton is initialized once"""
        learning1 = get_learning_service()
        learning2 = get_learning_service()

        assert learning1 is learning2
        assert isinstance(learning1, LearningIntegration)

    def test_knowledge_singleton_initialized_once(self):
        """Verify KnowledgeManager singleton is initialized once"""
        km1 = get_knowledge_service()
        km2 = get_knowledge_service()

        assert km1 is km2
        assert isinstance(km1, KnowledgeManager)

    def test_all_singletons_different_instances(self):
        """Verify all singletons are different from each other"""
        analyzer = get_analyzer_service()
        rag = get_rag_service()
        learning = get_learning_service()
        km = get_knowledge_service()

        # All should be different instances
        assert analyzer is not rag
        assert analyzer is not learning
        assert analyzer is not km
        assert rag is not learning
        assert rag is not km
        assert learning is not km

    def test_singleton_reset_clears_all_instances(self):
        """Verify singleton reset creates new instances"""
        analyzer1 = get_analyzer_service()
        rag1 = get_rag_service()

        LibrarySingletons.reset_all()

        analyzer2 = get_analyzer_service()
        rag2 = get_rag_service()

        # Should be different instances after reset
        assert analyzer1 is not analyzer2
        assert rag1 is not rag2


class TestCacheLayerIntegration:
    """Test query cache layer integration"""

    def setup_method(self):
        """Clear caches before each test"""
        get_query_cache().clear()

    def test_query_cache_stores_and_retrieves(self):
        """Verify query cache can store and retrieve values"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        # Cache should be empty initially
        assert cache.get(key) is None

        # Store value
        projects = [{"id": "p1", "name": "Project 1"}]
        cache.set(key, projects)

        # Should retrieve stored value
        retrieved = cache.get(key)
        assert retrieved == projects

    def test_query_cache_ttl_expiration(self):
        """Verify cache entries expire after TTL"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        # Store with 1 second TTL
        cache.set(key, ["project"], ttl_seconds=1)
        assert cache.get(key) == ["project"]

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get(key) is None

    def test_query_cache_hit_tracking(self):
        """Verify cache tracks hit/miss statistics"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        # First access - miss
        cache.get(key)

        # Store value
        cache.set(key, ["project"])

        # Multiple hits
        for _ in range(5):
            cache.get(key)

        # Check stats
        stats = cache.get_stats()
        assert stats["cached_entries"] == 1
        assert stats["total_hits"] == 5
        assert stats["total_misses"] == 1

    def test_cache_invalidation_removes_entry(self):
        """Verify cache invalidation removes entries"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        # Store value
        cache.set(key, ["project"])
        assert cache.get(key) is not None

        # Invalidate
        cache.invalidate(key)
        assert cache.get(key) is None

    def test_coordinated_cache_invalidation(self):
        """Verify coordinated invalidation removes all related caches"""
        cache = get_query_cache()

        # Store multiple related caches
        project_id = "proj1"
        cache.set(CacheKeys.project_detail(project_id), {"name": "Project 1"})
        cache.set(CacheKeys.team_members(project_id), [{"user": "alice"}])
        cache.set(CacheKeys.knowledge_documents(project_id), [{"doc": "doc1"}])

        # All should exist
        assert cache.get(CacheKeys.project_detail(project_id)) is not None
        assert cache.get(CacheKeys.team_members(project_id)) is not None
        assert cache.get(CacheKeys.knowledge_documents(project_id)) is not None

        # Invalidate all project-related caches
        keys_to_invalidate = CacheInvalidation.invalidate_project_caches(project_id)
        cache.invalidate_many(keys_to_invalidate)

        # All should be invalidated
        assert cache.get(CacheKeys.project_detail(project_id)) is None
        assert cache.get(CacheKeys.team_members(project_id)) is None
        assert cache.get(CacheKeys.knowledge_documents(project_id)) is None

    def test_cache_key_patterns(self):
        """Verify standardized cache key patterns work correctly"""
        cache = get_query_cache()

        # Test user projects pattern
        user_key = CacheKeys.user_projects("alice")
        assert "user_projects" in user_key
        assert "alice" in user_key

        # Test project detail pattern
        project_key = CacheKeys.project_detail("proj123")
        assert "project_detail" in project_key
        assert "proj123" in project_key

        # Test team members pattern
        team_key = CacheKeys.team_members("proj456")
        assert "team_members" in team_key
        assert "proj456" in team_key

        # All keys should be unique
        assert user_key != project_key
        assert user_key != team_key
        assert project_key != team_key


class TestLibraryComponentPresence:
    """Test that library components are properly integrated"""

    def setup_method(self):
        """Reset singletons before each test"""
        LibrarySingletons.reset_all()

    def test_analyzer_has_library_components(self):
        """Verify AnalyzerIntegration has library components"""
        analyzer = get_analyzer_service()

        # Should have library components
        assert hasattr(analyzer, "analyzer")  # socratic_analyzer component
        assert hasattr(analyzer, "metrics_calculator")
        assert hasattr(analyzer, "quality_scorer")
        assert hasattr(analyzer, "security_analyzer")

    def test_rag_has_library_components(self):
        """Verify RAGIntegration has library components"""
        rag = get_rag_service()

        # Should have library components
        assert hasattr(rag, "rag_client")  # socratic_rag component
        assert hasattr(rag, "document_store")
        assert hasattr(rag, "retriever")

    def test_learning_has_library_components(self):
        """Verify LearningIntegration has library components"""
        learning = get_learning_service()

        # Should have library components
        assert hasattr(learning, "engine")  # socratic_learning component
        assert hasattr(learning, "pattern_detector")
        assert hasattr(learning, "metrics_collector")

    def test_knowledge_has_library_components(self):
        """Verify KnowledgeManager has library components"""
        km = get_knowledge_service()

        # Should have library components
        assert hasattr(km, "knowledge_base")  # socratic_knowledge component
        assert hasattr(km, "document_store")
        assert hasattr(km, "search_engine")
        assert hasattr(km, "rbac_manager")


class TestPerformanceOptimizations:
    """Test that performance optimizations are working"""

    def setup_method(self):
        """Reset singletons and caches"""
        LibrarySingletons.reset_all()
        get_query_cache().clear()

    def test_singleton_caching_performance(self):
        """Verify singleton caching provides performance improvement"""
        # First access - initializes
        start = time.time()
        analyzer1 = get_analyzer_service()
        first_time = time.time() - start

        # Subsequent access - should be much faster
        start = time.time()
        analyzer2 = get_analyzer_service()
        second_time = time.time() - start

        assert analyzer1 is analyzer2
        # Subsequent access should be nearly instant (< first initialization)
        assert second_time < first_time

    def test_query_cache_hit_performance(self):
        """Verify cached queries are much faster"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(100)]

        # Cache miss
        start = time.time()
        cache.get(key)  # Miss
        miss_time = time.time() - start

        # Store in cache
        cache.set(key, projects)

        # Cache hit
        start = time.time()
        result = cache.get(key)
        hit_time = time.time() - start

        assert result == projects
        # Cache hit should be much faster
        assert hit_time < miss_time

    def test_cache_hit_rate(self):
        """Verify expected cache hit rates"""
        cache = get_query_cache()
        key = CacheKeys.user_projects("testuser")

        data = ["project1", "project2"]
        cache.set(key, data)

        # Simulate access pattern with hits and misses
        for _ in range(80):
            cache.get(key)  # Hits

        # Check stats
        stats = cache.get_stats()
        assert stats["cached_entries"] >= 1
        # Should have high hit rate
        assert stats["total_hits"] >= 70


class TestIntegrationFlow:
    """Test complete integration flows"""

    def setup_method(self):
        """Setup for integration tests"""
        LibrarySingletons.reset_all()
        get_query_cache().clear()

    def test_library_initialization_flow(self):
        """Test complete library initialization flow"""
        # Step 1: First request gets singletons
        analyzer = get_analyzer_service()
        rag = get_rag_service()

        # Step 2: Verify they're initialized
        assert analyzer is not None
        assert rag is not None

        # Step 3: Verify subsequent requests reuse
        analyzer2 = get_analyzer_service()
        assert analyzer is analyzer2

        # Step 4: Verify they're different instances
        assert analyzer is not rag

    def test_cache_integration_flow(self):
        """Test complete cache integration flow"""
        cache = get_query_cache()

        # Step 1: Initial query cache miss
        key = CacheKeys.user_projects("alice")
        assert cache.get(key) is None

        # Step 2: Store result
        projects = [{"id": "p1", "name": "Project 1"}]
        cache.set(key, projects)

        # Step 3: Cache hit
        result = cache.get(key)
        assert result == projects

        # Step 4: Invalidate
        cache.invalidate(key)
        assert cache.get(key) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
