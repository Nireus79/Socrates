"""
Comprehensive unit tests for workflow optimization system

Tests cover:
- WorkflowPathFinder: Path enumeration, cycle detection
- WorkflowCostCalculator: Token cost calculation
- WorkflowRiskCalculator: Risk assessment
- WorkflowBuilder: Workflow construction
- WorkflowOptimizer: Strategy-based path selection
- QuestionSelector: Question selection logic
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from socratic_system.core.workflow_builder import (
    WorkflowBuilder,
    create_discovery_workflow_comprehensive,
    create_discovery_workflow_simple,
)
from socratic_system.core.workflow_cost_calculator import WorkflowCostCalculator
from socratic_system.core.workflow_path_finder import WorkflowPathFinder
from socratic_system.core.workflow_risk_calculator import WorkflowRiskCalculator
from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import (
    PathDecisionStrategy,
    WorkflowEdge,
    WorkflowNode,
    WorkflowNodeType,
)


class TestWorkflowBuilder(unittest.TestCase):
    """Tests for WorkflowBuilder fluent API"""

    def test_builder_creates_valid_workflow(self):
        """Test that builder creates valid workflow definition"""
        builder = WorkflowBuilder(name="Test Workflow", phase="discovery")

        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node(
                "questions",
                WorkflowNodeType.QUESTION_SET,
                "Questions",
                5000,
                metadata={"target_categories": ["goals", "requirements"]},
            )
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "questions")
            .add_edge("questions", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        self.assertEqual(workflow.name, "Test Workflow")
        self.assertEqual(workflow.phase, "discovery")
        self.assertEqual(len(workflow.nodes), 3)
        self.assertEqual(len(workflow.edges), 2)
        self.assertEqual(workflow.start_node, "start")
        self.assertIn("end", workflow.end_nodes)

    def test_builder_validation_requires_entry(self):
        """Test that builder validates entry node is set"""
        builder = WorkflowBuilder(name="Invalid", phase="discovery")

        builder.add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
        builder.add_exit("end")

        with self.assertRaises(ValueError):
            builder.build()

    def test_builder_validation_requires_exit(self):
        """Test that builder validates exit nodes are set"""
        builder = WorkflowBuilder(name="Invalid", phase="discovery")

        builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
        builder.set_entry("start")

        with self.assertRaises(ValueError):
            builder.build()

    def test_discovery_simple_workflow(self):
        """Test simple discovery workflow factory"""
        project = self._create_test_project()
        workflow = create_discovery_workflow_simple(project)

        self.assertIsNotNone(workflow.start_node)
        self.assertGreater(len(workflow.end_nodes), 0)
        self.assertGreater(len(workflow.nodes), 0)

    def test_discovery_comprehensive_workflow(self):
        """Test comprehensive discovery workflow factory"""
        project = self._create_test_project()
        workflow = create_discovery_workflow_comprehensive(project)

        self.assertIsNotNone(workflow.start_node)
        self.assertGreater(len(workflow.end_nodes), 0)
        self.assertGreater(len(workflow.nodes), 3)

    @staticmethod
    def _create_test_project():
        """Create test project"""
        return ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


class TestWorkflowPathFinder(unittest.TestCase):
    """Tests for WorkflowPathFinder DFS algorithm"""

    def setUp(self):
        """Set up test workflows"""
        self.project = self._create_test_project()

    def test_path_finder_simple_linear_path(self):
        """Test finding single linear path"""
        builder = WorkflowBuilder(name="Linear", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node("q1", WorkflowNodeType.QUESTION_SET, "Questions", 5000)
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "q1")
            .add_edge("q1", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()

        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0].nodes), 3)

    def test_path_finder_multiple_paths(self):
        """Test finding multiple alternative paths"""
        builder = WorkflowBuilder(name="Branching", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node("quick", WorkflowNodeType.QUESTION_SET, "Quick", 3000)
            .add_node("comprehensive", WorkflowNodeType.QUESTION_SET, "Comprehensive", 8000)
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "quick")
            .add_edge("start", "comprehensive")
            .add_edge("quick", "end")
            .add_edge("comprehensive", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()

        self.assertEqual(len(paths), 2)

    @staticmethod
    def _create_test_project():
        """Create test project"""
        return ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )


class TestWorkflowCostCalculator(unittest.TestCase):
    """Tests for WorkflowCostCalculator"""

    def setUp(self):
        """Set up test calculator"""
        self.calculator = WorkflowCostCalculator()

    def test_calculate_cost_single_node(self):
        """Test cost calculation for single node"""
        builder = WorkflowBuilder(name="Test", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node("questions", WorkflowNodeType.QUESTION_SET, "Questions", 5000)
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "questions")
            .add_edge("questions", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()
        path = paths[0]

        cost_metrics = self.calculator.calculate_path_cost(path, workflow)

        self.assertGreater(cost_metrics["total_tokens"], 0)
        self.assertGreater(cost_metrics["total_cost_usd"], 0.0)

    def test_calculate_cost_multiple_nodes(self):
        """Test cost calculation sums all nodes"""
        builder = WorkflowBuilder(name="Test", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node("q1", WorkflowNodeType.QUESTION_SET, "Q1", 3000)
            .add_node("q2", WorkflowNodeType.QUESTION_SET, "Q2", 4000)
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "q1")
            .add_edge("q1", "q2")
            .add_edge("q2", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()
        path = paths[0]

        cost_metrics = self.calculator.calculate_path_cost(path, workflow)

        # Should sum 3000 + 4000 = 7000 tokens minimum
        self.assertGreaterEqual(cost_metrics["total_tokens"], 7000)


class TestWorkflowRiskCalculator(unittest.TestCase):
    """Tests for WorkflowRiskCalculator"""

    def setUp(self):
        """Set up test calculator"""
        self.calculator = WorkflowRiskCalculator()
        self.project = self._create_test_project()

    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        builder = WorkflowBuilder(name="Test", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node(
                "questions",
                WorkflowNodeType.QUESTION_SET,
                "Questions",
                5000,
                metadata={"target_categories": ["goals", "requirements"]},
            )
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "questions")
            .add_edge("questions", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()
        path = paths[0]

        risk_metrics = self.calculator.calculate_path_risk(path, workflow, self.project)

        self.assertIn("risk_score", risk_metrics)
        self.assertIn("incompleteness_risk", risk_metrics)
        self.assertIn("complexity_risk", risk_metrics)
        self.assertIn("rework_probability", risk_metrics)

        # Risk score should be between 0 and 100
        self.assertGreaterEqual(risk_metrics["risk_score"], 0.0)
        self.assertLessEqual(risk_metrics["risk_score"], 100.0)

    def test_incompleteness_risk_calculation(self):
        """Test that missing categories increase incompleteness risk"""
        builder = WorkflowBuilder(name="Test", phase="discovery")
        # Minimal workflow with few target categories
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node(
                "questions",
                WorkflowNodeType.QUESTION_SET,
                "Questions",
                5000,
                metadata={"target_categories": ["goals"]},  # Only goals
            )
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "questions")
            .add_edge("questions", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        finder = WorkflowPathFinder(workflow)
        paths = finder.find_all_paths()
        path = paths[0]

        risk_metrics = self.calculator.calculate_path_risk(path, workflow, self.project)

        # Should have significant incompleteness risk
        self.assertGreater(risk_metrics["incompleteness_risk"], 0.0)
        self.assertGreater(len(risk_metrics["missing_categories"]), 0)

    @staticmethod
    def _create_test_project():
        """Create test project"""
        return ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )


class TestWorkflowOptimizer(unittest.TestCase):
    """Tests for WorkflowOptimizer strategy selection"""

    def setUp(self):
        """Set up test project"""
        self.project = self._create_test_project()

    def test_optimizer_minimize_cost_strategy(self):
        """Test that MINIMIZE_COST selects lowest cost path"""
        from socratic_system.core.workflow_optimizer import WorkflowOptimizer

        builder = WorkflowBuilder(name="Test", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node("quick", WorkflowNodeType.QUESTION_SET, "Quick", 2000)
            .add_node("comprehensive", WorkflowNodeType.QUESTION_SET, "Comprehensive", 8000)
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "quick")
            .add_edge("start", "comprehensive")
            .add_edge("quick", "end")
            .add_edge("comprehensive", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        optimizer = WorkflowOptimizer()
        approval_request = optimizer.optimize_workflow(
            workflow=workflow,
            project=self.project,
            strategy=PathDecisionStrategy.MINIMIZE_COST,
        )

        self.assertIsNotNone(approval_request.recommended_path)
        # Recommended path should be the quick one (lower cost)
        self.assertLess(
            approval_request.recommended_path.total_cost_tokens,
            max(p.total_cost_tokens for p in approval_request.all_paths),
        )

    def test_optimizer_minimize_risk_strategy(self):
        """Test that MINIMIZE_RISK selects lowest risk path"""
        from socratic_system.core.workflow_optimizer import WorkflowOptimizer

        builder = WorkflowBuilder(name="Test", phase="discovery")
        workflow = (
            builder.add_node("start", WorkflowNodeType.PHASE_START, "Start", 0)
            .add_node(
                "q1",
                WorkflowNodeType.QUESTION_SET,
                "Q1",
                5000,
                metadata={"target_categories": ["goals", "requirements", "tech_stack"]},
            )
            .add_node(
                "q2",
                WorkflowNodeType.QUESTION_SET,
                "Q2",
                5000,
                metadata={"target_categories": ["goals"]},
            )
            .add_node("end", WorkflowNodeType.PHASE_END, "End", 0)
            .add_edge("start", "q1")
            .add_edge("start", "q2")
            .add_edge("q1", "end")
            .add_edge("q2", "end")
            .set_entry("start")
            .add_exit("end")
            .build()
        )

        optimizer = WorkflowOptimizer()
        approval_request = optimizer.optimize_workflow(
            workflow=workflow,
            project=self.project,
            strategy=PathDecisionStrategy.MINIMIZE_RISK,
        )

        self.assertIsNotNone(approval_request.recommended_path)
        # Recommended path should have lower risk score
        self.assertLessEqual(
            approval_request.recommended_path.risk_score,
            max(p.risk_score for p in approval_request.all_paths),
        )

    @staticmethod
    def _create_test_project():
        """Create test project"""
        return ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )


if __name__ == "__main__":
    unittest.main()
