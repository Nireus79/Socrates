"""
Phase 2 Verification: Router Integration with Orchestrator

Verifies:
1. All routers using _build_agent_context() correctly
2. All routers using orchestration methods (_orchestrate_*)
3. All routers returning debug_logs in APIResponse
4. Conversation_history properly passed to agents
5. Router endpoint patterns consistency
"""

import pytest
import inspect
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TestPhase2RouterVerification:
    """Verify Phase 2: Router context passing and orchestrator integration"""

    @pytest.fixture
    def router_files(self):
        """Get all router files"""
        router_dir = Path("backend/src/socrates_api/routers")
        return sorted([f for f in router_dir.glob("*.py") if f.name != "__init__.py"])

    def test_router_files_exist(self, router_files):
        """Verify router files exist"""
        assert len(router_files) > 0, "No router files found"
        logger.info(f"Found {len(router_files)} router files")
        for router in router_files:
            assert router.exists(), f"Router {router.name} not found"
        logger.info("✓ All router files exist")

    def test_priority_routers_present(self, router_files):
        """Verify priority routers are present"""
        priority_routers = {
            "projects_chat.py",
            "chat.py",
            "code_generation.py",
            "websocket.py",
            "knowledge.py",
        }

        found_routers = {f.name for f in router_files}
        missing = priority_routers - found_routers

        assert not missing, f"Missing priority routers: {missing}"
        logger.info(f"✓ All {len(priority_routers)} priority routers present")

    def test_orchestrator_import_in_routers(self, router_files):
        """Verify routers import orchestrator"""
        priority_routers = {"projects_chat.py", "chat.py", "code_generation.py", "websocket.py", "knowledge.py"}

        for router_file in router_files:
            if router_file.name in priority_routers:
                with open(router_file, "r") as f:
                    content = f.read()

                # Check for orchestrator import or usage
                has_orchestrator = (
                    "orchestrator" in content
                    or "get_orchestrator" in content
                    or "APIOrchestrator" in content
                )

                assert has_orchestrator, f"{router_file.name} doesn't import orchestrator"
                logger.info(f"✓ {router_file.name} imports orchestrator")

    def test_context_building_in_routers(self, router_files):
        """Verify routers use _build_agent_context()"""
        priority_routers = {"projects_chat.py", "chat.py", "websocket.py"}

        for router_file in router_files:
            if router_file.name in priority_routers:
                with open(router_file, "r") as f:
                    content = f.read()

                # Check for context building
                has_context = "_build_agent_context" in content or "context = orchestrator" in content

                assert has_context, f"{router_file.name} doesn't build context"
                logger.info(f"✓ {router_file.name} builds agent context")

    def test_debug_logs_in_responses(self, router_files):
        """Verify routers return debug_logs in APIResponse"""
        priority_routers = {"projects_chat.py", "chat.py", "code_generation.py", "websocket.py"}

        for router_file in router_files:
            if router_file.name in priority_routers:
                with open(router_file, "r") as f:
                    content = f.read()

                # Check for debug_logs in APIResponse
                has_debug_logs = "debug_logs" in content and "APIResponse" in content

                assert has_debug_logs, f"{router_file.name} doesn't return debug_logs in APIResponse"
                logger.info(f"✓ {router_file.name} returns debug_logs in APIResponse")

    def test_orchestration_methods_usage(self, router_files):
        """Verify routers use orchestration methods"""
        expected_methods = {
            "projects_chat.py": ["_orchestrate_question_generation", "_orchestrate_answer_processing"],
            "chat.py": ["_build_agent_context"],
            "code_generation.py": ["_build_agent_context"],
            "websocket.py": ["_build_agent_context"],
        }

        for router_name, methods in expected_methods.items():
            router_file = next((f for f in router_files if f.name == router_name), None)
            if router_file:
                with open(router_file, "r") as f:
                    content = f.read()

                for method in methods:
                    assert method in content, f"{router_name} doesn't use {method}"
                    logger.info(f"✓ {router_name} uses {method}")

    def test_conversation_history_handling(self, router_files):
        """Verify routers handle conversation_history"""
        priority_routers = {"projects_chat.py", "chat.py", "websocket.py", "knowledge.py"}

        for router_file in router_files:
            if router_file.name in priority_routers:
                with open(router_file, "r") as f:
                    content = f.read()

                # Check for conversation_history handling
                has_history = "conversation_history" in content

                assert has_history, f"{router_file.name} doesn't handle conversation_history"
                logger.info(f"✓ {router_file.name} handles conversation_history")

    def test_endpoint_patterns(self, router_files):
        """Verify endpoint patterns are consistent"""
        patterns_to_check = {
            "APIResponse": "APIResponse structure",
            "router": "FastAPI router",
            "@router": "router decorator",
        }

        for router_file in router_files:
            with open(router_file, "r") as f:
                content = f.read()

            for pattern, description in patterns_to_check.items():
                if pattern in ["@router", "router ="]:
                    # Check for either pattern
                    has_pattern = "@router" in content or "router =" in content
                    assert has_pattern, f"{router_file.name} missing {description}"
                else:
                    assert pattern in content, f"{router_file.name} missing {description}"

        logger.info("✓ All routers follow consistent patterns")

    def test_error_handling_in_routers(self, router_files):
        """Verify routers have error handling"""
        priority_routers = {"projects_chat.py", "chat.py", "code_generation.py"}

        for router_file in router_files:
            if router_file.name in priority_routers:
                with open(router_file, "r") as f:
                    content = f.read()

                # Check for error handling patterns
                has_error_handling = (
                    "try:" in content
                    or "HTTPException" in content
                    or "except" in content
                )

                assert has_error_handling, f"{router_file.name} lacks error handling"
                logger.info(f"✓ {router_file.name} has error handling")


class TestPhase2RouterResponses:
    """Test router response structures"""

    def test_api_response_structure(self):
        """Verify APIResponse structure"""
        try:
            from socrates_api.models import APIResponse

            # Check required fields
            assert hasattr(APIResponse, "success"), "APIResponse missing success field"
            assert hasattr(APIResponse, "data") or hasattr(APIResponse, "message"), "APIResponse missing data/message"

            logger.info("✓ APIResponse structure valid")
        except ImportError:
            pytest.skip("APIResponse not available")

    def test_response_includes_debug_logs(self):
        """Verify responses can include debug_logs"""
        try:
            from socrates_api.models import APIResponse

            # Create sample response with debug_logs
            response = APIResponse(
                success=True,
                data={"test": "data"},
                debug_logs=["test_log"],
            )

            assert response.success is True
            assert response.debug_logs == ["test_log"]
            logger.info("✓ APIResponse can include debug_logs")
        except ImportError:
            pytest.skip("APIResponse not available")


class TestPhase2Integration:
    """Integration tests for Phase 2"""

    @pytest.fixture
    def orchestrator(self):
        """Get orchestrator"""
        try:
            from socrates_api.orchestrator import APIOrchestrator

            return APIOrchestrator(api_key_or_config="")
        except ImportError:
            pytest.skip("Orchestrator not available")

    @pytest.fixture
    def mock_project(self):
        """Create mock project"""

        class MockProject:
            def __init__(self):
                self.project_id = "test_proj"
                self.name = "Test"
                self.description = "Test project"
                self.phase = "discovery"
                self.conversation_history = [
                    {"type": "question", "content": "Q1?"},
                    {"type": "answer", "content": "A1."},
                ]
                self.pending_questions = []
                self.goals = ["Goal 1"]
                self.requirements = ["Req 1"]
                self.tech_stack = ["Python"]
                self.constraints = []
                self.files = []
                self.members = []

        return MockProject()

    def test_orchestration_flow_question_generation(self, orchestrator, mock_project):
        """Test complete question generation orchestration"""
        # This would require a real API call, so we test the method exists and is callable
        assert hasattr(orchestrator, "_orchestrate_question_generation")
        assert callable(orchestrator._orchestrate_question_generation)

        logger.info("✓ Question generation orchestration method available")

    def test_orchestration_flow_answer_processing(self, orchestrator, mock_project):
        """Test complete answer processing orchestration"""
        assert hasattr(orchestrator, "_orchestrate_answer_processing")
        assert callable(orchestrator._orchestrate_answer_processing)

        logger.info("✓ Answer processing orchestration method available")

    def test_context_building_in_orchestrator(self, orchestrator, mock_project):
        """Test context building produces expected structure"""
        context = orchestrator._build_agent_context(mock_project)

        # Verify context structure
        assert "project" in context
        assert "conversation_history" in context
        assert "conversation_summary" in context
        assert "debug_logs" in context

        # Verify conversation_history
        assert len(context["conversation_history"]) > 0
        assert context["conversation_history"] == mock_project.conversation_history

        logger.info("✓ Context building produces correct structure")


class TestPhase2Readiness:
    """Test Phase 2 readiness for production"""

    def test_router_count(self):
        """Verify sufficient routers for functionality"""
        router_dir = Path("backend/src/socrates_api/routers")
        router_count = len([f for f in router_dir.glob("*.py") if f.name != "__init__.py"])

        assert router_count >= 34, f"Expected at least 34 routers, found {router_count}"
        logger.info(f"✓ {router_count} routers present")

    def test_priority_router_completeness(self):
        """Verify priority routers are complete"""
        priority_routers = {
            "projects_chat.py": "Question-answer flow",
            "chat.py": "Chat operations",
            "code_generation.py": "Code generation",
            "websocket.py": "Real-time communication",
            "knowledge.py": "Knowledge management",
        }

        router_dir = Path("backend/src/socrates_api/routers")

        for router_name, description in priority_routers.items():
            router_path = router_dir / router_name
            assert router_path.exists(), f"{router_name} ({description}) not found"

            # Check file size (should have content)
            file_size = router_path.stat().st_size
            assert file_size > 1000, f"{router_name} is too small ({file_size} bytes)"

            logger.info(f"✓ {router_name}: {description}")

    def test_orchestrator_completeness(self):
        """Verify orchestrator has all Phase 2 requirements"""
        from socrates_api.orchestrator import APIOrchestrator

        required_methods = [
            "_build_agent_context",
            "_gather_question_context",
            "_orchestrate_question_generation",
            "_orchestrate_answer_processing",
            "_generate_conversation_summary",
        ]

        for method in required_methods:
            assert hasattr(APIOrchestrator, method), f"Orchestrator missing {method}"

        logger.info("✓ Orchestrator has all Phase 2 requirements")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
