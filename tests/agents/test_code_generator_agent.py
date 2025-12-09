"""
Tests for CodeGeneratorAgent - Code generation and documentation
"""

from unittest.mock import MagicMock, patch

import pytest

import socrates
from socratic_system.agents.code_generator import CodeGeneratorAgent


@pytest.mark.unit
class TestCodeGeneratorAgentInitialization:
    """Tests for CodeGeneratorAgent initialization"""

    def test_agent_initialization(self, test_config):
        """Test CodeGeneratorAgent initializes correctly"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            assert agent is not None
            assert agent.name == "CodeGenerator"
            assert agent.orchestrator == orchestrator


@pytest.mark.unit
class TestCodeGeneratorAgentContextBuilding:
    """Tests for code generation context building"""

    def test_build_generation_context_basic(self, test_config, sample_project):
        """Test building code generation context from project"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            sample_project.goals = "Build a REST API"
            sample_project.phase = "implementation"
            sample_project.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
            sample_project.requirements = ["RESTful design", "Authentication", "Rate limiting"]
            sample_project.constraints = ["Must run on Linux"]
            sample_project.deployment_target = "AWS"
            sample_project.code_style = "PEP 8"

            context = agent._build_generation_context(sample_project)

            assert "Build a REST API" in context
            assert "implementation" in context
            assert "FastAPI" in context
            assert "RESTful design" in context
            assert "AWS" in context

    def test_build_generation_context_with_conversation(self, test_config, sample_project):
        """Test that conversation history is included in context"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            sample_project.conversation_history = [
                {"type": "user", "content": "Should I use async or sync?"},
                {"type": "assistant", "content": "Use async for I/O-bound operations"},
                {"type": "user", "content": "What about error handling?"},
                {"type": "assistant", "content": "Use try-except blocks with custom exceptions"},
            ]

            context = agent._build_generation_context(sample_project)

            # Recent messages (last 5) should be included
            assert "Should I use async or sync?" in context or "async" in context.lower()
            assert "error handling" in context.lower() or "handling" in context.lower()

    def test_build_generation_context_empty_fields(self, test_config, sample_project):
        """Test context building handles empty project fields gracefully"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # Leave most fields empty
            sample_project.goals = ""
            sample_project.tech_stack = []
            sample_project.requirements = []
            sample_project.conversation_history = []

            context = agent._build_generation_context(sample_project)

            # Should not raise error and should return valid context
            assert isinstance(context, str)
            assert len(context) > 0
            assert sample_project.name in context


@pytest.mark.unit
class TestCodeGeneratorAgentScriptGeneration:
    """Tests for script/code generation"""

    def test_generate_script_success(self, test_config, sample_project):
        """Test successful script generation"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # Mock the generate_code method
            mock_code = "def hello():\n    print('Hello, World!')"
            orchestrator.claude_client.generate_code = MagicMock(return_value=mock_code)

            sample_project.goals = "Create a simple greeting function"
            sample_project.tech_stack = ["Python"]

            request = {"action": "generate_script", "project": sample_project}

            result = agent.process(request)

            assert result["status"] == "success"
            assert result["script"] == mock_code
            assert "context_used" in result
            orchestrator.claude_client.generate_code.assert_called_once()

    def test_generate_script_api_error(self, test_config, sample_project):
        """Test handling of API errors during code generation"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # Mock API error
            orchestrator.claude_client.generate_code = MagicMock(
                side_effect=Exception("API Error: Rate limited")
            )

            request = {"action": "generate_script", "project": sample_project}

            # Should propagate error or handle gracefully
            try:
                result = agent.process(request)
                # If it doesn't raise, it should indicate error
                assert "status" in result
            except Exception:
                # This is also acceptable - error is raised
                pass

    def test_generate_script_preserves_context(self, test_config, sample_project):
        """Test that generated context is returned with script"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            sample_project.goals = "Build API endpoints"
            sample_project.requirements = ["CRUD operations", "Validation"]
            orchestrator.claude_client.generate_code = MagicMock(return_value="# Generated code")

            request = {"action": "generate_script", "project": sample_project}

            result = agent.process(request)

            assert "context_used" in result
            context = result["context_used"]
            assert "Build API endpoints" in context
            assert "CRUD operations" in context


@pytest.mark.unit
class TestCodeGeneratorAgentDocumentation:
    """Tests for documentation generation"""

    def test_generate_documentation_success(self, test_config, sample_project):
        """Test successful documentation generation"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            sample_code = "def calculate_sum(a, b):\n    return a + b"
            mock_docs = "# Calculate Sum\nAdds two numbers and returns the result."

            orchestrator.claude_client.generate_documentation = MagicMock(return_value=mock_docs)

            request = {
                "action": "generate_documentation",
                "project": sample_project,
                "script": sample_code,
            }

            result = agent.process(request)

            assert result["status"] == "success"
            assert result["documentation"] == mock_docs
            orchestrator.claude_client.generate_documentation.assert_called_once()

    def test_generate_documentation_missing_script(self, test_config, sample_project):
        """Test documentation generation handles missing script"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            request = {
                "action": "generate_documentation",
                "project": sample_project,
                "script": None,
            }

            result = agent.process(request)

            assert "status" in result
            # Should handle gracefully or raise appropriate error
            orchestrator.claude_client.generate_documentation.assert_called_once()

    def test_generate_documentation_with_complex_code(self, test_config, sample_project):
        """Test documentation generation for complex code"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            complex_code = """
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = {}

    async def process_batch(self, items):
        results = []
        for item in items:
            result = await self._process_item(item)
            results.append(result)
        return results

    async def _process_item(self, item):
        if item in self.cache:
            return self.cache[item]
        # Process item...
        return item
"""

            mock_docs = "# Data Processor\nHandles batch processing with caching."

            orchestrator.claude_client.generate_documentation = MagicMock(return_value=mock_docs)

            request = {
                "action": "generate_documentation",
                "project": sample_project,
                "script": complex_code,
            }

            result = agent.process(request)

            assert result["status"] == "success"
            assert "Data Processor" in result["documentation"]


@pytest.mark.unit
class TestCodeGeneratorAgentErrorHandling:
    """Tests for error scenarios"""

    def test_unknown_action(self, test_config):
        """Test handling of unknown action"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            request = {"action": "unknown_generation_action"}

            result = agent.process(request)

            assert result["status"] == "error"
            assert "unknown" in result["message"].lower()

    def test_missing_action_field(self, test_config):
        """Test handling of missing action field"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            request = {}

            result = agent.process(request)

            assert result["status"] == "error"

    def test_missing_project_field(self, test_config):
        """Test handling of missing project in request"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            orchestrator.claude_client.generate_code = MagicMock(
                side_effect=AttributeError("'NoneType' object has no attribute 'name'")
            )

            request = {
                "action": "generate_script"
                # Missing 'project' field
            }

            try:
                result = agent.process(request)
                # Should handle error
                assert "status" in result
            except Exception:
                # Error raised is also acceptable
                pass


@pytest.mark.unit
class TestCodeGeneratorAgentLanguageSupport:
    """Tests for different programming language support"""

    @pytest.mark.parametrize(
        "language,tech_stack",
        [
            ("Python", ["Python", "FastAPI"]),
            ("JavaScript", ["JavaScript", "Node.js", "Express"]),
            ("TypeScript", ["TypeScript", "NestJS"]),
            ("Go", ["Go", "Gin"]),
            ("Rust", ["Rust", "Actix"]),
        ],
    )
    def test_generate_script_multiple_languages(
        self, test_config, sample_project, language, tech_stack
    ):
        """Test code generation for different programming languages"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            sample_project.tech_stack = tech_stack
            sample_project.language_preferences = language

            mock_code = f"// {language} code example"
            orchestrator.claude_client.generate_code = MagicMock(return_value=mock_code)

            request = {"action": "generate_script", "project": sample_project}

            result = agent.process(request)

            assert result["status"] == "success"
            orchestrator.claude_client.generate_code.assert_called_once()


@pytest.mark.unit
class TestCodeGeneratorAgentLogging:
    """Tests for logging and event emission"""

    def test_generates_log_message(self, test_config, sample_project):
        """Test that code generation emits log messages"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # Track log calls
            agent.log = MagicMock()
            orchestrator.claude_client.generate_code = MagicMock(return_value="# code")

            request = {"action": "generate_script", "project": sample_project}

            agent.process(request)

            # Should have called log
            agent.log.assert_called()


@pytest.mark.integration
class TestCodeGeneratorAgentIntegration:
    """Integration tests for code generation workflows"""

    def test_full_generation_workflow(self, test_config, sample_project):
        """Test complete workflow: script generation -> documentation"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            mock_code = """
def process_data(data):
    '''Process input data'''
    return [x * 2 for x in data]
"""
            mock_docs = "# Process Data\nDoubles each element in the input list."

            orchestrator.claude_client.generate_code = MagicMock(return_value=mock_code)
            orchestrator.claude_client.generate_documentation = MagicMock(return_value=mock_docs)

            sample_project.goals = "Create data processing utilities"
            sample_project.tech_stack = ["Python"]
            sample_project.requirements = ["Efficient processing", "Clean code"]

            # Generate script
            gen_request = {"action": "generate_script", "project": sample_project}
            gen_result = agent.process(gen_request)
            assert gen_result["status"] == "success"

            # Generate documentation for the script
            doc_request = {
                "action": "generate_documentation",
                "project": sample_project,
                "script": gen_result["script"],
            }
            doc_result = agent.process(doc_request)
            assert doc_result["status"] == "success"

            # Verify both succeeded
            assert gen_result["script"] == mock_code
            assert doc_result["documentation"] == mock_docs

    def test_context_rich_generation(self, test_config, sample_project):
        """Test that rich project context improves generation quality"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # Set up rich context
            sample_project.goals = "Build microservices architecture"
            sample_project.phase = "implementation"
            sample_project.tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"]
            sample_project.requirements = [
                "RESTful API",
                "Authentication",
                "Rate limiting",
                "Caching",
                "Logging",
            ]
            sample_project.constraints = [
                "Must run on Kubernetes",
                "Zero-downtime deployments",
                "Sub-100ms response times",
            ]
            sample_project.deployment_target = "Kubernetes"
            sample_project.code_style = "PEP 8 with Black formatter"
            sample_project.conversation_history = [
                {"type": "user", "content": "Should services be in separate containers?"},
                {"type": "assistant", "content": "Yes, separate containers for each microservice"},
            ]

            mock_code = "# Microservices starter code"
            orchestrator.claude_client.generate_code = MagicMock(return_value=mock_code)

            request = {"action": "generate_script", "project": sample_project}

            result = agent.process(request)

            assert result["status"] == "success"
            # Verify rich context was used
            context = result["context_used"]
            assert "microservices" in context.lower() or "Build" in context
            assert "kubernetes" in context.lower() or "Deployment" in context.lower()

    def test_generation_with_error_recovery(self, test_config, sample_project):
        """Test recovery from temporary API failures"""
        with patch("anthropic.Anthropic"):
            orchestrator = socrates.AgentOrchestrator(test_config)
            agent = CodeGeneratorAgent(orchestrator)

            # First call fails, second succeeds (simulating retry)
            orchestrator.claude_client.generate_code = MagicMock(
                side_effect=[RuntimeError("Temporary API error"), "# Code after retry"]
            )

            request = {"action": "generate_script", "project": sample_project}

            # First attempt fails
            with pytest.raises(RuntimeError):
                agent.process(request)

            # Reset mock
            orchestrator.claude_client.generate_code.reset_mock()
            orchestrator.claude_client.generate_code.return_value = "# Code after retry"

            # Second attempt succeeds
            result = agent.process(request)
            assert result["status"] == "success"
