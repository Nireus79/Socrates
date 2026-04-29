"""
Tests for Phase 1 Service Layer Implementation.

Tests validate:
- Service instantiation without orchestrator
- Repository pattern functionality
- Dependency injection
- Service isolation
"""

import unittest
from unittest.mock import MagicMock, patch

from socratic_system.config import SocratesConfig
from socratic_system.services import (
    CodeService,
    InsightService,
    KnowledgeService,
    ProjectService,
    QualityService,
    ServiceContainer,
    initialize_container,
    reset_container,
)
from socratic_system.services.repositories import (
    KnowledgeRepository,
    MaturityRepository,
    ProjectRepository,
)


class TestBaseService(unittest.TestCase):
    """Test base Service functionality"""

    def test_service_has_config(self):
        """Test that Service has configuration"""
        from socratic_system.services.base import Service

        config = MagicMock(spec=SocratesConfig)
        service = Service(config)

        self.assertEqual(service.config, config)
        self.assertIsNotNone(service.logger)

    def test_service_logging(self):
        """Test service logging methods"""
        from socratic_system.services.base import Service

        config = MagicMock(spec=SocratesConfig)
        service = Service(config)

        # Should not raise
        service.log_info("test")
        service.log_debug("test")
        service.log_warning("test")
        service.log_error("test")


class TestProjectRepository(unittest.TestCase):
    """Test ProjectRepository"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.repository = ProjectRepository(self.mock_db)

    def test_save_project(self):
        """Test saving a project"""
        project = MagicMock()
        project.project_id = "proj_1"

        result = self.repository.save(project)

        self.mock_db.save_project.assert_called_once_with(project)
        self.assertEqual(result, project)

    def test_find_by_id(self):
        """Test finding project by ID"""
        expected_project = MagicMock()
        self.mock_db.load_project.return_value = expected_project

        result = self.repository.find_by_id("proj_1")

        self.mock_db.load_project.assert_called_once_with("proj_1")
        self.assertEqual(result, expected_project)

    def test_exists(self):
        """Test project existence check"""
        self.mock_db.load_project.return_value = MagicMock()

        exists = self.repository.exists("proj_1")

        self.assertTrue(exists)

    def test_find_by_user(self):
        """Test finding projects by user"""
        projects = [MagicMock(), MagicMock()]
        self.mock_db.get_user_projects.return_value = projects

        result = self.repository.find_by_user("user_1")

        self.mock_db.get_user_projects.assert_called_once_with("user_1")
        self.assertEqual(result, projects)


class TestProjectService(unittest.TestCase):
    """Test ProjectService"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.repo = MagicMock(spec=ProjectRepository)
        self.claude = MagicMock()
        self.events = MagicMock()

        self.service = ProjectService(
            self.config,
            self.repo,
            self.claude,
            self.events,
        )

    def test_create_project_validation(self):
        """Test project creation validates input"""
        with self.assertRaises(ValueError):
            self.service.create_project("", "description", "user_1")

        with self.assertRaises(ValueError):
            self.service.create_project("Test", "description", "")

    def test_create_project_success(self):
        """Test successful project creation"""
        mock_project = MagicMock()
        mock_project.project_id = "proj_1"
        mock_project.name = "Test Project"
        self.repo.save.return_value = mock_project

        result = self.service.create_project(
            name="Test Project",
            description="A test project",
            user_id="user_1",
        )

        self.repo.save.assert_called_once()
        self.events.emit.assert_called_once()
        self.assertEqual(result, mock_project)

    def test_get_project(self):
        """Test retrieving project"""
        expected = MagicMock()
        self.repo.find_by_id.return_value = expected

        result = self.service.get_project("proj_1")

        self.repo.find_by_id.assert_called_once_with("proj_1")
        self.assertEqual(result, expected)

    def test_update_project(self):
        """Test updating project"""
        project = MagicMock()
        project.description = "old"
        self.repo.find_by_id.return_value = project
        self.repo.save.return_value = project

        result = self.service.update_project("proj_1", description="new")

        self.repo.save.assert_called_once()
        self.events.emit.assert_called_once()

    def test_delete_project(self):
        """Test deleting project"""
        self.repo.find_by_id.return_value = MagicMock()
        self.repo.delete.return_value = True

        result = self.service.delete_project("proj_1")

        self.assertTrue(result)
        self.repo.delete.assert_called_once_with("proj_1")
        self.events.emit.assert_called_once()


class TestQualityService(unittest.TestCase):
    """Test QualityService"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.repo = MagicMock(spec=MaturityRepository)

        self.service = QualityService(self.config, self.repo)

    def test_calculate_maturity(self):
        """Test maturity calculation"""
        project = MagicMock()
        project.project_id = "proj_1"
        project.phase = "discovery"
        project.description = "Test project"
        project.goals = ["Goal 1"]
        project.tech_stack = ["Python"]

        result = self.service.calculate_maturity(project)

        self.assertIn("overall_score", result)
        self.assertIn("maturity_level", result)
        self.assertIn("category_scores", result)
        self.repo.save.assert_called_once()

    def test_maturity_level_determination(self):
        """Test maturity level classification"""
        levels = [
            (15, "initial"),
            (35, "developing"),
            (55, "intermediate"),
            (75, "advanced"),
            (95, "mature"),
        ]

        for score, expected_level in levels:
            level = self.service._determine_maturity_level(score)
            self.assertEqual(level, expected_level)

    def test_can_advance_phase(self):
        """Test phase advancement check"""
        project = MagicMock()
        project.project_id = "proj_1"

        # Should advance if score >= 60
        self.repo.find_by_id.return_value = {"overall_score": 70.0}
        self.assertTrue(self.service.can_advance_phase(project))

        # Should not advance if score < 60
        self.repo.find_by_id.return_value = {"overall_score": 50.0}
        self.assertFalse(self.service.can_advance_phase(project))


class TestKnowledgeRepository(unittest.TestCase):
    """Test KnowledgeRepository"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_vector_db = MagicMock()
        self.repository = KnowledgeRepository(self.mock_db, self.mock_vector_db)

    def test_save_knowledge(self):
        """Test saving knowledge entry"""
        knowledge = MagicMock()
        knowledge.content = "Some knowledge"
        knowledge.project_id = "proj_1"

        result = self.repository.save(knowledge)

        self.mock_db.save_knowledge_document.assert_called_once()
        self.mock_vector_db.add_knowledge.assert_called_once()

    def test_search_knowledge(self):
        """Test semantic knowledge search"""
        expected_results = [
            (MagicMock(), 0.95),
            (MagicMock(), 0.87),
        ]
        self.mock_vector_db.search_similar.return_value = expected_results

        result = self.repository.search("query", "proj_1", top_k=2)

        self.mock_vector_db.search_similar.assert_called_once_with("query", 2, "proj_1")
        self.assertEqual(result, expected_results)


class TestKnowledgeService(unittest.TestCase):
    """Test KnowledgeService"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.repo = MagicMock(spec=KnowledgeRepository)

        self.service = KnowledgeService(self.config, self.repo)

    def test_add_knowledge_validation(self):
        """Test knowledge creation validates input"""
        with self.assertRaises(ValueError):
            self.service.add_knowledge("", "proj_1")

        with self.assertRaises(ValueError):
            self.service.add_knowledge("content", "")

    def test_add_knowledge_success(self):
        """Test successful knowledge addition"""
        mock_knowledge = MagicMock()
        self.repo.save.return_value = mock_knowledge

        result = self.service.add_knowledge(
            "API uses REST",
            "proj_1",
            metadata={"type": "architecture"},
        )

        self.repo.save.assert_called_once()

    def test_search_knowledge(self):
        """Test knowledge search"""
        expected = [(MagicMock(), 0.95)]
        self.repo.search.return_value = expected

        result = self.service.search_knowledge("auth", "proj_1", top_k=5)

        self.repo.search.assert_called_once_with("auth", "proj_1", 5)


class TestInsightService(unittest.TestCase):
    """Test InsightService"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.claude = MagicMock()

        self.service = InsightService(self.config, self.claude)

    def test_extract_insights_validation(self):
        """Test insight extraction validates input"""
        with self.assertRaises(ValueError):
            self.service.extract_insights("")

    def test_extract_insights_success(self):
        """Test successful insight extraction"""
        expected_insights = {"requirement": "Build API", "tech": "REST"}
        self.claude.extract_insights.return_value = expected_insights

        result = self.service.extract_insights(
            "Build a REST API",
            user_id="user_1",
        )

        self.claude.extract_insights.assert_called_once()

    def test_categorize_insights(self):
        """Test insight categorization"""
        insights = {
            "tech_stack": "Python",
            "business_goal": "Revenue",
            "user_ui": "Web",
        }

        result = self.service.categorize_insights(insights)

        self.assertIn("technical", result)
        self.assertIn("business", result)
        self.assertIn("user_experience", result)


class TestCodeService(unittest.TestCase):
    """Test CodeService"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.claude = MagicMock()

        self.service = CodeService(self.config, self.claude)

    def test_generate_code(self):
        """Test code generation"""
        project = MagicMock()
        self.claude.generate_artifact.return_value = {"code": "print('hello')"}

        result = self.service.generate_code(project, language="python")

        self.claude.generate_artifact.assert_called_once()
        self.assertEqual(result, "print('hello')")

    def test_validate_python_code(self):
        """Test Python code validation"""
        valid_code = "print('hello')"
        errors = self.service._validate_python(valid_code)
        self.assertEqual(errors, [])

        invalid_code = "print('hello'"
        errors = self.service._validate_python(invalid_code)
        self.assertTrue(len(errors) > 0)

    def test_validate_javascript_code(self):
        """Test JavaScript code validation"""
        valid_code = "console.log('hello');"
        errors = self.service._validate_javascript(valid_code)
        self.assertEqual(errors, [])

        invalid_code = "{ console.log('hello')"
        errors = self.service._validate_javascript(invalid_code)
        self.assertTrue(len(errors) > 0)


class TestServiceContainer(unittest.TestCase):
    """Test ServiceContainer"""

    def setUp(self):
        self.config = MagicMock(spec=SocratesConfig)
        self.db = MagicMock()
        self.vector_db = MagicMock()
        self.claude = MagicMock()
        self.events = MagicMock()

        self.container = ServiceContainer(
            self.config,
            self.db,
            self.vector_db,
            self.claude,
            self.events,
        )

    def test_get_project_service(self):
        """Test getting ProjectService"""
        service = self.container.get_project_service()

        self.assertIsInstance(service, ProjectService)
        # Should be cached
        service2 = self.container.get_project_service()
        self.assertIs(service, service2)

    def test_get_quality_service(self):
        """Test getting QualityService"""
        service = self.container.get_quality_service()

        self.assertIsInstance(service, QualityService)

    def test_get_knowledge_service(self):
        """Test getting KnowledgeService"""
        service = self.container.get_knowledge_service()

        self.assertIsInstance(service, KnowledgeService)

    def test_get_insight_service(self):
        """Test getting InsightService"""
        service = self.container.get_insight_service()

        self.assertIsInstance(service, InsightService)

    def test_get_code_service(self):
        """Test getting CodeService"""
        service = self.container.get_code_service()

        self.assertIsInstance(service, CodeService)

    def test_get_service_by_name(self):
        """Test getting service by name"""
        service = self.container.get_service("project")

        self.assertIsInstance(service, ProjectService)

    def test_register_custom_service(self):
        """Test registering custom service"""
        custom_service = MagicMock()
        self.container.register_service("custom", custom_service)

        self.assertIn("custom", self.container._services)

    def test_service_stats(self):
        """Test getting service statistics"""
        self.container.get_project_service()
        self.container.get_quality_service()

        stats = self.container.get_service_stats()

        self.assertGreaterEqual(stats["cached_services"], 2)
        self.assertIn("project_service", stats["services"])


class TestDependencyInjection(unittest.TestCase):
    """Test dependency injection functions"""

    def tearDown(self):
        reset_container()

    def test_initialize_container(self):
        """Test initializing global container"""
        config = MagicMock(spec=SocratesConfig)
        db = MagicMock()
        vector_db = MagicMock()
        claude = MagicMock()
        events = MagicMock()

        container = initialize_container(config, db, vector_db, claude, events)

        self.assertIsNotNone(container)
        self.assertIsInstance(container, ServiceContainer)

    def test_get_global_container(self):
        """Test getting global container"""
        from socratic_system.services import get_service_container

        config = MagicMock(spec=SocratesConfig)
        db = MagicMock()
        vector_db = MagicMock()
        claude = MagicMock()
        events = MagicMock()

        initialize_container(config, db, vector_db, claude, events)
        container = get_service_container()

        self.assertIsNotNone(container)

    def test_reset_container(self):
        """Test resetting global container"""
        from socratic_system.services import get_service_container

        config = MagicMock(spec=SocratesConfig)
        db = MagicMock()
        vector_db = MagicMock()
        claude = MagicMock()
        events = MagicMock()

        initialize_container(config, db, vector_db, claude, events)
        reset_container()

        # Container should be None or empty after reset
        container = get_service_container()
        self.assertIsNone(container)


if __name__ == "__main__":
    unittest.main()
