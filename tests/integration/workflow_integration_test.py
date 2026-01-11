"""
Integration tests for workflow optimization system

Tests cover:
- Approval request flow: blocking and resumption
- Question selection from approved paths
- Workflow execution and node advancement
- End-to-end discovery phase with optimization
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from socratic_system.agents.quality_controller import QualityControllerAgent
from socratic_system.agents.socratic_counselor import SocraticCounselorAgent
from socratic_system.core.question_selector import QuestionSelector
from socratic_system.core.workflow_builder import create_discovery_workflow_comprehensive
from socratic_system.models.project import ProjectContext
from socratic_system.models.workflow import WorkflowExecutionState


class TestWorkflowApprovalFlow(unittest.TestCase):
    """Tests for workflow approval request and execution flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.project = self._create_test_project()
        self.mock_orchestrator = self._create_mock_orchestrator()

    def test_approval_request_returns_pending_status(self):
        """Test that approval request returns pending_approval status"""
        qc_agent = QualityControllerAgent(self.mock_orchestrator)
        workflow = create_discovery_workflow_comprehensive(self.project)

        result = qc_agent._request_workflow_approval(
            {
                "project": self.project,
                "workflow": workflow,
            }
        )

        self.assertEqual(result["status"], "pending_approval")
        self.assertIn("request_id", result)
        self.assertIn("approval_request", result)

    def test_approval_request_stored_in_pending_approvals(self):
        """Test that approval request is stored for later retrieval"""
        qc_agent = QualityControllerAgent(self.mock_orchestrator)
        workflow = create_discovery_workflow_comprehensive(self.project)

        result = qc_agent._request_workflow_approval(
            {
                "project": self.project,
                "workflow": workflow,
            }
        )

        request_id = result["request_id"]
        self.assertIn(request_id, qc_agent.pending_approvals)

    def test_approve_workflow_removes_from_pending(self):
        """Test that approving workflow removes it from pending list"""
        qc_agent = QualityControllerAgent(self.mock_orchestrator)
        workflow = create_discovery_workflow_comprehensive(self.project)

        # Create approval request
        approval_result = qc_agent._request_workflow_approval(
            {
                "project": self.project,
                "workflow": workflow,
            }
        )

        request_id = approval_result["request_id"]
        approval_request = approval_result["approval_request"]
        path_id = approval_request["recommended_path"]["path_id"]

        # Verify it's in pending
        self.assertIn(request_id, qc_agent.pending_approvals)

        # Approve it
        approve_result = qc_agent._approve_workflow(
            {
                "request_id": request_id,
                "approved_path_id": path_id,
            }
        )

        self.assertEqual(approve_result["status"], "success")
        # Verify it's no longer in pending
        self.assertNotIn(request_id, qc_agent.pending_approvals)

    def test_reject_workflow_removes_from_pending(self):
        """Test that rejecting workflow removes it from pending list"""
        qc_agent = QualityControllerAgent(self.mock_orchestrator)
        workflow = create_discovery_workflow_comprehensive(self.project)

        # Create approval request
        approval_result = qc_agent._request_workflow_approval(
            {
                "project": self.project,
                "workflow": workflow,
            }
        )

        request_id = approval_result["request_id"]

        # Verify it's in pending
        self.assertIn(request_id, qc_agent.pending_approvals)

        # Reject it
        reject_result = qc_agent._reject_workflow(
            {
                "request_id": request_id,
                "reason": "Test rejection",
            }
        )

        self.assertEqual(reject_result["status"], "success")
        # Verify it's no longer in pending
        self.assertNotIn(request_id, qc_agent.pending_approvals)

    def test_get_pending_approvals(self):
        """Test retrieving list of pending approvals"""
        qc_agent = QualityControllerAgent(self.mock_orchestrator)
        workflow = create_discovery_workflow_comprehensive(self.project)

        # Create multiple approval requests
        approval_result1 = qc_agent._request_workflow_approval(
            {"project": self.project, "workflow": workflow}
        )
        approval_result2 = qc_agent._request_workflow_approval(
            {"project": self.project, "workflow": workflow}
        )

        # Get pending approvals
        result = qc_agent._get_pending_approvals(
            {"project_id": self.project.project_id}
        )

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(result["total_count"], 2)

    @staticmethod
    def _create_test_project():
        """Create test project"""
        project = ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )
        project.metadata["use_workflow_optimization"] = True
        return project

    @staticmethod
    def _create_mock_orchestrator():
        """Create mock orchestrator"""
        mock_orchestrator = MagicMock()
        mock_orchestrator.claude_client = MagicMock()
        return mock_orchestrator


class TestQuestionSelection(unittest.TestCase):
    """Tests for question selection from approved workflow paths"""

    def setUp(self):
        """Set up test fixtures"""
        self.project = self._create_test_project()
        self.workflow = create_discovery_workflow_comprehensive(self.project)
        self.selector = QuestionSelector()

    def test_select_questions_for_target_categories(self):
        """Test that selector generates questions for target categories"""
        # Set up execution at first question node
        execution = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="comprehensive_questions",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        questions = self.selector.select_next_questions(
            self.project, self.workflow, execution, max_questions=1
        )

        self.assertGreater(len(questions), 0)
        self.assertIsInstance(questions[0], str)

    def test_select_respects_max_questions(self):
        """Test that selector respects max_questions limit"""
        execution = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="comprehensive_questions",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        questions = self.selector.select_next_questions(
            self.project, self.workflow, execution, max_questions=3
        )

        self.assertLessEqual(len(questions), 3)

    def test_select_next_node(self):
        """Test that selector can find next node in workflow"""
        execution = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="comprehensive_questions",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        next_node = self.selector.get_next_node(self.workflow, execution)

        self.assertIsNotNone(next_node)
        self.assertIn(next_node, self.workflow.nodes)

    def test_is_execution_complete(self):
        """Test checking if execution has reached end node"""
        # Create execution at end node
        execution_complete = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="end",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=0,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        # Create execution at question node
        execution_active = WorkflowExecutionState(
            execution_id="exec_456",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="comprehensive_questions",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        self.assertTrue(self.selector.is_execution_complete(execution_complete, self.workflow))
        self.assertFalse(self.selector.is_execution_complete(execution_active, self.workflow))

    @staticmethod
    def _create_test_project():
        """Create test project"""
        project = ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )
        project.metadata["use_workflow_optimization"] = True
        return project


class TestWorkflowExecution(unittest.TestCase):
    """Tests for workflow execution and advancement"""

    def setUp(self):
        """Set up test fixtures"""
        self.project = self._create_test_project()
        self.workflow = create_discovery_workflow_comprehensive(self.project)

    def test_workflow_execution_state_initialization(self):
        """Test creating workflow execution state"""
        execution = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="start",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        self.assertEqual(execution.execution_id, "exec_123")
        self.assertEqual(execution.current_node_id, "start")
        self.assertEqual(execution.status, "active")
        self.assertEqual(len(execution.completed_nodes), 0)

    def test_workflow_execution_state_transitions(self):
        """Test updating execution state during workflow"""
        execution = WorkflowExecutionState(
            execution_id="exec_123",
            workflow_id=self.workflow.workflow_id,
            approved_path_id="path_123",
            current_node_id="start",
            completed_nodes=[],
            actual_tokens_used=0,
            estimated_tokens_remaining=11000,
            started_at=datetime.now().isoformat(),
            status="active",
        )

        # Simulate node completion
        execution.completed_nodes.append("start")
        execution.current_node_id = "comprehensive_questions"
        execution.actual_tokens_used = 500

        self.assertIn("start", execution.completed_nodes)
        self.assertEqual(execution.current_node_id, "comprehensive_questions")
        self.assertEqual(execution.actual_tokens_used, 500)

    @staticmethod
    def _create_test_project():
        """Create test project"""
        project = ProjectContext(
            project_id="test_123",
            name="Test Project",
            owner="test_user",
            phase="discovery",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            project_type="software",
        )
        project.metadata["use_workflow_optimization"] = True
        return project


if __name__ == "__main__":
    unittest.main()
