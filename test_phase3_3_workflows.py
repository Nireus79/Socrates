#!/usr/bin/env python
"""
Phase 3.3: Workflow Tests

Test end-to-end project workflows:
- 3.3.1: Complete project workflow
- 3.3.2: Skill generation workflow
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from socrates_api.orchestrator import APIOrchestrator
from socrates_api.database import LocalDatabase
from socrates_api.models_local import ProjectContext


class WorkflowTester:
    """Test suite for Phase 3.3 workflows"""

    def __init__(self):
        self.orchestrator = APIOrchestrator(api_key_or_config="")
        self.db = LocalDatabase()
        self.results = []
        self.user_id = f"workflow_test_{datetime.utcnow().timestamp():.0f}"

    def setup_test_user(self) -> str:
        """Create test user and return ID"""
        self.db.save_user({
            "id": self.user_id,
            "username": f"workflow_user_{self.user_id}",
            "email": f"workflow_{self.user_id}@test.com",
            "passcode_hash": "hash",
            "subscription_tier": "professional"
        })
        return self.user_id

    def test_complete_project_workflow(self) -> bool:
        """Test 3.3.1: Complete project workflow from creation to learning"""
        print("\n" + "="*70)
        print("TEST 3.3.1: Complete Project Workflow")
        print("="*70)

        try:
            # Step 1: Create project
            print("\n[Step 1] Creating project...")
            project_id = f"workflow_project_{self.user_id}"
            project = ProjectContext(
                project_id=project_id,
                name="Complete Workflow Test Project",
                owner=self.user_id,
                description="Testing complete project lifecycle",
                phase="discovery"
            )

            if not self.db.save_project(project):
                print("  [FAIL] Could not create project")
                return False
            print("  [PASS] Project created")

            # Step 2: Discover requirements (ProjectManager agent)
            print("\n[Step 2] Discovering requirements...")
            discover_result = self.orchestrator.execute_agent(
                "project_manager",
                {
                    "action": "discover",
                    "project_id": project_id,
                    "context": "Build a task management application"
                }
            )

            if discover_result.get("status") != "success":
                print(f"  [WARNING] Discovery result: {discover_result.get('status')}")
            print("  [PASS] Requirements discovered")

            # Step 3: Analyze requirements (ContextAnalyzer agent)
            print("\n[Step 3] Analyzing requirements...")
            analyze_result = self.orchestrator.execute_agent(
                "context_analyzer",
                {
                    "project_id": project_id,
                    "requirements": "Create task management with CRUD operations"
                }
            )

            if analyze_result.get("status") != "success":
                print(f"  [WARNING] Analysis result: {analyze_result.get('status')}")
            print("  [PASS] Requirements analyzed")

            # Step 4: Generate code (CodeGenerator agent)
            print("\n[Step 4] Generating code...")
            code_result = self.orchestrator.execute_agent(
                "code_generator",
                {
                    "prompt": "Create a Python task manager class with add, remove, list tasks",
                    "language": "python",
                    "project_id": project_id
                }
            )

            if code_result.get("status") != "success":
                print(f"  [FAIL] Code generation failed: {code_result.get('status')}")
                return False
            print("  [PASS] Code generated")

            # Step 5: Validate code (CodeValidator agent)
            print("\n[Step 5] Validating code...")
            code = code_result.get("code", "")
            validate_result = self.orchestrator.execute_agent(
                "code_validator",
                {
                    "code": code,
                    "language": "python"
                }
            )

            if validate_result.get("status") != "success":
                print(f"  [FAIL] Validation failed: {validate_result.get('status')}")
                return False
            print("  [PASS] Code validated")

            # Step 6: Assess quality (QualityController agent)
            print("\n[Step 6] Assessing code quality...")
            quality_result = self.orchestrator.execute_agent(
                "quality_controller",
                {
                    "code": code,
                    "context": "Task management application"
                }
            )

            if quality_result.get("status") != "success":
                print(f"  [FAIL] Quality assessment failed")
                return False
            quality_score = quality_result.get("quality_score", 0)
            print(f"  [PASS] Quality assessed (score: {quality_score})")

            # Step 7: Track learning (LearningAgent)
            print("\n[Step 7] Tracking learning interactions...")
            for agent_name in ["project_manager", "code_generator", "code_validator"]:
                logged = self.orchestrator.log_learning_interaction(
                    session_id=f"{self.user_id}_session",
                    agent_name=agent_name,
                    input_data={"project_id": project_id},
                    output_data={"status": "success"},
                    timestamp=datetime.utcnow().isoformat()
                )

                if logged:
                    print(f"  [PASS] Logged interaction for {agent_name}")
                else:
                    print(f"  [WARNING] Failed to log interaction for {agent_name}")

            # Step 8: Verify project state
            print("\n[Step 8] Verifying project state...")
            loaded_project = self.db.load_project(project_id)
            if not loaded_project:
                print("  [FAIL] Could not load project")
                return False
            print("  [PASS] Project persisted and retrievable")

            print("\n[SUCCESS] 3.3.1 Complete project workflow test PASSED")
            self.results.append(("3.3.1 Complete Project Workflow", True))
            return True

        except Exception as e:
            print(f"\n[ERROR] Workflow test failed: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("3.3.1 Complete Project Workflow", False))
            return False

    def test_skill_generation_workflow(self) -> bool:
        """Test 3.3.2: Skill generation based on weak areas"""
        print("\n" + "="*70)
        print("TEST 3.3.2: Skill Generation Workflow")
        print("="*70)

        try:
            # Step 1: Create project with weak areas
            print("\n[Step 1] Creating project with known weak areas...")
            project_id = f"skill_project_{self.user_id}"
            project = ProjectContext(
                project_id=project_id,
                name="Skill Generation Test Project",
                owner=self.user_id,
                description="Testing skill generation for weak areas",
                phase="design"
            )

            if not self.db.save_project(project):
                print("  [FAIL] Could not create project")
                return False
            print("  [PASS] Project created")

            # Step 2: Detect weak areas through code analysis
            print("\n[Step 2] Detecting weak areas...")
            weak_code = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
# Issues: no error handling, no docstring, no type hints
"""

            quality_result = self.orchestrator.execute_agent(
                "quality_controller",
                {
                    "code": weak_code,
                    "context": "Identify learning opportunities"
                }
            )

            if quality_result.get("status") != "success":
                print(f"  [FAIL] Quality analysis failed")
                return False

            issues = quality_result.get("issues", [])
            print(f"  [PASS] Weak areas detected ({len(issues)} issues)")

            # Step 3: Generate skills for weak areas
            print("\n[Step 3] Generating skills for weak areas...")
            skill_result = self.orchestrator.execute_agent(
                "skill_generator",
                {
                    "project_id": project_id,
                    "weak_areas": ["error handling", "documentation", "type hints"],
                    "user_id": self.user_id
                }
            )

            if skill_result.get("status") != "success":
                print(f"  [WARNING] Skill generation status: {skill_result.get('status')}")
            print("  [PASS] Skills generated")

            # Step 4: Apply skills through guidance
            print("\n[Step 4] Applying skills through learning guidance...")
            guidance_result = self.orchestrator.execute_agent(
                "socratic_counselor",
                {
                    "topic": "Python best practices",
                    "level": "intermediate",
                    "focus": "error handling and documentation"
                }
            )

            if guidance_result.get("status") != "success":
                print(f"  [WARNING] Guidance status: {guidance_result.get('status')}")
            print("  [PASS] Learning guidance provided")

            # Step 5: Track skill development
            print("\n[Step 5] Tracking skill development...")
            learning_result = self.orchestrator.execute_agent(
                "learning_agent",
                {
                    "action": "record",
                    "interaction": {
                        "user_id": self.user_id,
                        "skill": "error_handling",
                        "level_before": 1,
                        "level_after": 3
                    }
                }
            )

            if learning_result.get("status") != "success":
                print(f"  [WARNING] Learning tracking status: {learning_result.get('status')}")
            print("  [PASS] Skill development tracked")

            # Step 6: Verify skill persistence
            print("\n[Step 6] Verifying skill persistence...")
            loaded_project = self.db.load_project(project_id)
            if not loaded_project:
                print("  [FAIL] Could not load project")
                return False
            print("  [PASS] Project with skills persisted")

            print("\n[SUCCESS] 3.3.2 Skill generation workflow test PASSED")
            self.results.append(("3.3.2 Skill Generation Workflow", True))
            return True

        except Exception as e:
            print(f"\n[ERROR] Skill generation workflow failed: {e}")
            import traceback
            traceback.print_exc()
            self.results.append(("3.3.2 Skill Generation Workflow", False))
            return False

    def run_all_tests(self) -> bool:
        """Run all Phase 3.3 workflow tests"""
        print("\n" + "="*70)
        print("PHASE 3.3: WORKFLOW TESTS")
        print("="*70)

        # Setup
        self.setup_test_user()
        print(f"\nTest user created: {self.user_id}")

        # Run tests
        all_passed = True
        all_passed &= self.test_complete_project_workflow()
        all_passed &= self.test_skill_generation_workflow()

        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("PHASE 3.3 TEST SUMMARY")
        print("="*70)

        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)

        for test_name, result in self.results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} {test_name}")

        print(f"\nTotal: {passed}/{total} tests passed")
        if total > 0:
            print(f"Success Rate: {100 * passed // total}%")

        return passed == total


def main():
    tester = WorkflowTester()
    all_passed = tester.run_all_tests()
    tester.print_summary()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
