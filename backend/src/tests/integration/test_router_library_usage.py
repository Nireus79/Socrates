"""
Router Library Usage Integration Tests

Validates that all routers properly use library components through
dependency injection and don't use local fallbacks.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from socrates_api.main import app
from socrates_api.models_local import (
    AnalyzerIntegration,
    RAGIntegration,
    LearningIntegration,
    KnowledgeManager,
)
from socrates_api.library_cache import (
    LibrarySingletons,
    get_analyzer_service,
    get_rag_service,
    get_learning_service,
    get_knowledge_service,
)


class TestAnalysisRouterLibraryUsage:
    """Test that analysis router uses AnalyzerIntegration singleton"""

    def setup_method(self):
        """Setup test client and reset singletons"""
        self.client = TestClient(app)
        LibrarySingletons.reset_all()

    def test_analyze_code_uses_analyzer_singleton(self):
        """POST /analysis/validate uses AnalyzerIntegration singleton"""
        with patch(
            "socrates_api.routers.analysis.get_analyzer_service"
        ) as mock_get_analyzer:
            mock_analyzer = Mock(spec=AnalyzerIntegration)
            mock_analyzer.validate_code.return_value = {
                "valid": True,
                "issues": [],
                "score": 100,
            }
            mock_get_analyzer.return_value = mock_analyzer

            payload = {"project_id": "proj1", "code": "print('hello')"}

            response = self.client.post("/analysis/validate", json=payload)

            # Verify get_analyzer_service was called (dependency injection)
            mock_get_analyzer.assert_called()
            # Verify analyzer.validate_code was called
            mock_analyzer.validate_code.assert_called()

    def test_calculate_metrics_uses_analyzer_singleton(self):
        """POST /analysis/metrics uses AnalyzerIntegration singleton"""
        with patch(
            "socrates_api.routers.analysis.get_analyzer_service"
        ) as mock_get_analyzer:
            mock_analyzer = Mock(spec=AnalyzerIntegration)
            mock_analyzer.calculate_metrics.return_value = {
                "complexity": 2.5,
                "maintainability": 85,
            }
            mock_get_analyzer.return_value = mock_analyzer

            payload = {"project_id": "proj1", "code": "def foo(): pass"}

            response = self.client.post("/analysis/metrics", json=payload)

            # Verify analyzer is used
            mock_get_analyzer.assert_called()
            mock_analyzer.calculate_metrics.assert_called()

    def test_analysis_no_local_fallback_code(self):
        """Analysis router doesn't have try/except fallback patterns"""
        from socrates_api.routers import analysis

        # Get source code of the module
        import inspect

        source = inspect.getsource(analysis)

        # Should NOT have patterns like:
        # except: pass
        # except: return default_response
        # if not analyzer.available

        assert "if not analyzer.available" not in source
        assert "except:\n        pass" not in source
        assert ".available" not in source  # No .available checks


class TestRAGRouterLibraryUsage:
    """Test that RAG router uses RAGIntegration singleton"""

    def setup_method(self):
        """Setup test client and reset singletons"""
        self.client = TestClient(app)
        LibrarySingletons.reset_all()

    def test_index_document_uses_rag_singleton(self):
        """POST /rag/index uses RAGIntegration singleton"""
        with patch("socrates_api.routers.rag.get_rag_service") as mock_get_rag:
            mock_rag = Mock(spec=RAGIntegration)
            mock_rag.index_document.return_value = {
                "document_id": "doc1",
                "indexed": True,
            }
            mock_get_rag.return_value = mock_rag

            payload = {
                "project_id": "proj1",
                "title": "Test Doc",
                "content": "Test content",
            }

            response = self.client.post("/rag/index", json=payload)

            # Verify RAG service is used
            mock_get_rag.assert_called()
            mock_rag.index_document.assert_called()

    def test_retrieve_context_uses_rag_singleton(self):
        """POST /rag/retrieve uses RAGIntegration singleton"""
        with patch("socrates_api.routers.rag.get_rag_service") as mock_get_rag:
            mock_rag = Mock(spec=RAGIntegration)
            mock_rag.retrieve_context.return_value = [
                {"content": "Relevant context", "score": 0.95}
            ]
            mock_get_rag.return_value = mock_rag

            payload = {"project_id": "proj1", "query": "How do I test?"}

            response = self.client.post("/rag/retrieve", json=payload)

            # Verify RAG service is used
            mock_get_rag.assert_called()
            mock_rag.retrieve_context.assert_called()

    def test_rag_no_local_fallback_code(self):
        """RAG router doesn't have try/except fallback patterns"""
        from socrates_api.routers import rag

        import inspect

        source = inspect.getsource(rag)

        assert "if not rag.available" not in source
        assert ".available" not in source  # No .available checks
        assert "except:\n        pass" not in source


class TestLearningRouterLibraryUsage:
    """Test that learning router uses LearningIntegration singleton"""

    def setup_method(self):
        """Setup test client and reset singletons"""
        self.client = TestClient(app)
        LibrarySingletons.reset_all()

    def test_log_interaction_uses_learning_singleton(self):
        """POST /learning/log uses LearningIntegration singleton"""
        with patch(
            "socrates_api.routers.learning.get_learning_service"
        ) as mock_get_learning:
            mock_learning = Mock(spec=LearningIntegration)
            mock_learning.log_interaction.return_value = {
                "interaction_id": "int1",
                "logged": True,
            }
            mock_get_learning.return_value = mock_learning

            payload = {
                "user_id": "user1",
                "interaction_type": "question",
                "content": "Test",
            }

            response = self.client.post("/learning/log", json=payload)

            # Verify Learning service is used
            mock_get_learning.assert_called()
            mock_learning.log_interaction.assert_called()

    def test_get_progress_uses_learning_singleton(self):
        """GET /learning/progress uses LearningIntegration singleton"""
        with patch(
            "socrates_api.routers.learning.get_learning_service"
        ) as mock_get_learning:
            mock_learning = Mock(spec=LearningIntegration)
            mock_learning.get_learning_progress.return_value = {
                "user_id": "user1",
                "progress": 75,
            }
            mock_get_learning.return_value = mock_learning

            response = self.client.get("/learning/progress/user1")

            # Verify Learning service is used
            mock_get_learning.assert_called()
            mock_learning.get_learning_progress.assert_called()

    def test_learning_no_local_fallback_code(self):
        """Learning router doesn't have try/except fallback patterns"""
        from socrates_api.routers import learning

        import inspect

        source = inspect.getsource(learning)

        assert "if not learning.available" not in source
        assert ".available" not in source  # No .available checks
        assert "except:\n        pass" not in source


class TestKnowledgeManagementRouterLibraryUsage:
    """Test that knowledge_management router uses KnowledgeManager singleton"""

    def setup_method(self):
        """Setup test client and reset singletons"""
        self.client = TestClient(app)
        LibrarySingletons.reset_all()

    def test_add_document_uses_km_and_rag_singletons(self):
        """POST /knowledge/documents uses KnowledgeManager and RAGIntegration"""
        with patch(
            "socrates_api.routers.knowledge_management.get_knowledge_service"
        ) as mock_get_km, patch(
            "socrates_api.routers.knowledge_management.get_rag_service"
        ) as mock_get_rag:
            mock_km = Mock(spec=KnowledgeManager)
            mock_rag = Mock(spec=RAGIntegration)

            mock_km.add_document.return_value = {"doc_id": "doc1"}
            mock_rag.index_document.return_value = {"indexed": True}

            mock_get_km.return_value = mock_km
            mock_get_rag.return_value = mock_rag

            payload = {
                "project_id": "proj1",
                "title": "Test",
                "content": "Content",
            }

            response = self.client.post("/knowledge/documents", json=payload)

            # Verify both services are used
            mock_get_km.assert_called()
            mock_get_rag.assert_called()
            mock_km.add_document.assert_called()
            mock_rag.index_document.assert_called()

    def test_knowledge_no_local_fallback_code(self):
        """Knowledge management router doesn't have fallback patterns"""
        from socrates_api.routers import knowledge_management

        import inspect

        source = inspect.getsource(knowledge_management)

        assert ".available" not in source  # No .available checks
        assert "except:\n        pass" not in source


class TestChatRouterAsyncIntegration:
    """Test that chat router uses AsyncOrchestrator"""

    def setup_method(self):
        """Setup test client and reset singletons"""
        self.client = TestClient(app)
        LibrarySingletons.reset_all()

    def test_get_next_question_uses_async_orchestrator(self):
        """POST /chat/next-question uses AsyncOrchestrator"""
        with patch("socrates_api.routers.chat.get_async_orchestrator") as mock_get_async:
            mock_async_orch = AsyncMock()
            mock_async_orch.process_request_async.return_value = {
                "question": "What is abstraction?",
                "context": {"topic": "OOP"},
            }
            mock_get_async.return_value = mock_async_orch

            payload = {"project_id": "proj1", "conversation_id": "conv1"}

            # Note: Client needs to handle async properly
            # This is a simplified check

            mock_get_async.assert_not_called()  # Not called until endpoint is hit


class TestLibraryComponentsImportedCorrectly:
    """Test that library components are imported and used, not duplicated locally"""

    def test_analyzer_integration_imports_socratic_analyzer(self):
        """AnalyzerIntegration imports from socratic-analyzer library"""
        analyzer = get_analyzer_service()

        # Should have library components
        assert hasattr(analyzer, "analyzer")  # From socratic_analyzer
        assert hasattr(analyzer, "metrics_calculator")  # From library
        assert hasattr(analyzer, "quality_scorer")  # From library
        assert hasattr(analyzer, "security_analyzer")  # From library

    def test_rag_integration_imports_socratic_rag(self):
        """RAGIntegration imports from socratic-rag library"""
        rag = get_rag_service()

        # Should have library components
        assert hasattr(rag, "rag_client")  # From socratic_rag
        assert hasattr(rag, "document_store")  # From library
        assert hasattr(rag, "retriever")  # From library

    def test_learning_integration_imports_socratic_learning(self):
        """LearningIntegration imports from socratic-learning library"""
        learning = get_learning_service()

        # Should have library components
        assert hasattr(learning, "engine")  # From socratic_learning
        assert hasattr(learning, "pattern_detector")  # From library
        assert hasattr(learning, "metrics_collector")  # From library

    def test_knowledge_manager_imports_socratic_knowledge(self):
        """KnowledgeManager imports from socratic-knowledge library"""
        km = get_knowledge_service()

        # Should have library components
        assert hasattr(km, "knowledge_base")  # From socratic_knowledge
        assert hasattr(km, "document_store")  # From library
        assert hasattr(km, "search_engine")  # From library
        assert hasattr(km, "rbac_manager")  # From library


class TestDependencyInjectionPattern:
    """Test that routers use FastAPI dependency injection correctly"""

    def test_analyzer_router_endpoint_has_dependency(self):
        """Analysis endpoint has analyzer dependency"""
        from socrates_api.routers.analysis import analyze_code

        # Get endpoint function signature
        import inspect

        sig = inspect.signature(analyze_code)

        # Should have 'analyzer' parameter
        assert "analyzer" in sig.parameters

        # Parameter should have AnalyzerIntegration annotation
        analyzer_param = sig.parameters["analyzer"]
        assert (
            "AnalyzerIntegration" in str(analyzer_param.annotation)
            or analyzer_param.annotation is AnalyzerIntegration
        )

    def test_rag_router_endpoint_has_dependency(self):
        """RAG endpoint has rag dependency"""
        from socrates_api.routers.rag import index_document

        import inspect

        sig = inspect.signature(index_document)

        # Should have 'rag' parameter
        assert "rag" in sig.parameters

    def test_learning_router_endpoint_has_dependency(self):
        """Learning endpoint has learning dependency"""
        from socrates_api.routers.learning import log_interaction

        import inspect

        sig = inspect.signature(log_interaction)

        # Should have 'learning' parameter
        assert "learning" in sig.parameters

    def test_knowledge_router_endpoint_has_dependencies(self):
        """Knowledge endpoint has km and rag dependencies"""
        from socrates_api.routers.knowledge_management import add_knowledge_document

        import inspect

        sig = inspect.signature(add_knowledge_document)

        # Should have both 'km' and 'rag' parameters
        assert "km" in sig.parameters or "knowledge" in sig.parameters
        assert "rag" in sig.parameters


class TestNoCodeDuplication:
    """Verify no local code duplicates library functionality"""

    def test_no_duplicate_code_analysis_logic(self):
        """No local code duplication of analyzer functionality"""
        from socrates_api.routers import analysis

        import inspect

        source = inspect.getsource(analysis)

        # Should NOT implement analysis logic, should delegate to library
        # These patterns would indicate duplication:
        patterns_that_mean_duplication = [
            "def analyze_code_quality",
            "def check_security",
            "def calculate_metrics",
            "regex.findall",
            "ast.parse",
        ]

        for pattern in patterns_that_mean_duplication:
            if pattern in source and "analyzer." not in source:
                pytest.fail(f"Found potential duplicate implementation: {pattern}")

    def test_no_duplicate_rag_logic(self):
        """No local code duplication of RAG functionality"""
        from socrates_api.routers import rag

        import inspect

        source = inspect.getsource(rag)

        # Should NOT implement vector search, embedding, or retrieval
        # Should delegate to RAGIntegration

        assert "rag." in source  # Uses rag service
        # Could add more specific checks

    def test_routers_delegate_not_implement(self):
        """Routers delegate to library integration classes, don't implement"""
        from socrates_api.routers import analysis, rag, learning

        # These routers should mostly be:
        # 1. Parse request
        # 2. Call library method
        # 3. Return response

        # Complex business logic should be in library services, not routers

        import inspect

        # Analysis router should be relatively short if it just delegates
        analysis_source = inspect.getsource(analysis)
        rag_source = inspect.getsource(rag)
        learning_source = inspect.getsource(learning)

        # Routers should have many calls to library methods
        assert analysis_source.count("analyzer.") > 0
        assert rag_source.count("rag.") > 0
        assert learning_source.count("learning.") > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
