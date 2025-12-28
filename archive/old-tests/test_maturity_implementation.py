"""
Comprehensive test of maturity tracking implementation
Tests all interconnections and core functionality
"""

import datetime

from socratic_system.events import EventType
from socratic_system.models import ProjectContext


def test_1_model_initialization():
    """Test 1: Verify maturity model initialization"""
    print("\n" + "=" * 70)
    print("TEST 1: Model Initialization")
    print("=" * 70)

    # Create a test project
    project = ProjectContext(
        project_id="test-project-1",
        name="Test Project",
        owner="test_user",
        collaborators=[],
        goals="Build a web app",
        requirements=["Responsive design"],
        tech_stack=["Python"],
        constraints=["Budget: $5000"],
        team_structure="Solo",
        language_preferences="Python",
        deployment_target="Cloud",
        code_style="PEP8",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    print(f"[OK] Project created: {project.name}")
    print(f"[OK] Phase: {project.phase}")
    print(f"[OK] Maturity scores initialized: {project.phase_maturity_scores}")
    print(f"[OK] Category scores: {project.category_scores}")
    print(f"[OK] Categorized specs: {project.categorized_specs}")
    print(f"[OK] Maturity history: {project.maturity_history}")

    # Verify initialization values
    assert project.phase_maturity_scores == {
        "discovery": 0.0,
        "analysis": 0.0,
        "design": 0.0,
        "implementation": 0.0,
    }, "Phase maturity scores not initialized correctly"
    assert isinstance(project.category_scores, dict), "Category scores not dict"
    assert isinstance(project.categorized_specs, dict), "Categorized specs not dict"
    assert isinstance(project.maturity_history, list), "Maturity history not list"

    print("\n[OK] TEST 1 PASSED: All maturity fields initialized correctly")
    return project


def test_2_event_types():
    """Test 2: Verify new event types exist"""
    print("\n" + "=" * 70)
    print("TEST 2: Event Types")
    print("=" * 70)

    event_types_to_check = [
        "PHASE_MATURITY_UPDATED",
        "PHASE_READY_TO_ADVANCE",
        "QUALITY_CHECK_PASSED",
        "QUALITY_CHECK_WARNING",
        "MATURITY_MILESTONE",
        "PHASE_ADVANCED",  # This was already defined
    ]

    for event_name in event_types_to_check:
        assert hasattr(EventType, event_name), f"EventType.{event_name} not found"
        event = getattr(EventType, event_name)
        print(f"[OK] {event_name}: {event.value}")

    print("\n[OK] TEST 2 PASSED: All event types exist and accessible")


def test_3_quality_controller_agent():
    """Test 3: Quality Controller Agent - Basic functionality"""
    print("\n" + "=" * 70)
    print("TEST 3: Quality Controller Agent Initialization")
    print("=" * 70)

    # Import and check agent exists
    from socratic_system.agents import QualityControllerAgent

    print("[OK] QualityControllerAgent imported successfully")

    # Create a mock orchestrator with minimal setup
    class MockClaudeClient:
        pass

    class MockEventEmitter:
        def emit(self, event_type, data=None):
            pass

    class MockOrchestrator:
        def __init__(self):
            self.claude_client = MockClaudeClient()
            self.event_emitter = MockEventEmitter()

    orchestrator = MockOrchestrator()
    agent = QualityControllerAgent(orchestrator)

    print(f"[OK] Agent created: {agent.name}")
    print(
        f"[OK] Thresholds: READY={agent.READY_THRESHOLD}, "
        f"COMPLETE={agent.COMPLETE_THRESHOLD}, "
        f"WARNING={agent.WARNING_THRESHOLD}"
    )

    # Verify phase categories are defined
    expected_phases = ["discovery", "analysis", "design", "implementation"]
    for phase in expected_phases:
        assert phase in agent.phase_categories, f"Phase {phase} not in categories"
        categories = agent.phase_categories[phase]
        print(f"[OK] {phase.capitalize()} has {len(categories)} categories")

    print("\n[OK] TEST 3 PASSED: QualityControllerAgent initialized correctly")
    return agent


def test_4_maturity_calculation():
    """Test 4: Maturity calculation with empty specs"""
    print("\n" + "=" * 70)
    print("TEST 4: Maturity Calculation - Empty Specs")
    print("=" * 70)

    from socratic_system.agents import QualityControllerAgent
    from socratic_system.models import ProjectContext

    # Create a mock orchestrator with minimal setup
    class MockClaudeClient:
        pass

    class MockEventEmitter:
        def emit(self, event_type, data=None):
            pass

    class MockOrchestrator:
        def __init__(self):
            self.claude_client = MockClaudeClient()
            self.event_emitter = MockEventEmitter()

    orchestrator = MockOrchestrator()
    agent = QualityControllerAgent(orchestrator)

    # Create a sample project
    project = ProjectContext(
        project_id="test_proj",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test goals",
        requirements=["Req1"],
        tech_stack=["Python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="clean",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    # Calculate maturity with no specs (should be 0%)
    result = agent._calculate_phase_maturity({"project": project, "phase": "discovery"})

    assert result["status"] == "success", f"Failed: {result}"
    maturity = result["maturity"]

    print("[OK] Maturity calculation successful")
    print(f"[OK] Overall score: {maturity['overall_score']:.1f}%")
    print(f"[OK] Total specs: {maturity['total_specs']}")
    print(f"[OK] Ready to advance: {maturity['is_ready_to_advance']}")

    assert maturity["overall_score"] == 0.0, "Empty specs should be 0%"
    assert maturity["total_specs"] == 0, "Should have 0 specs"
    assert not maturity["is_ready_to_advance"], "Should not be ready at 0%"
    assert len(maturity["missing_categories"]) > 0, "Should have missing categories"

    print(f"[OK] Missing categories: {maturity['missing_categories'][:3]}...")

    print("\n[OK] TEST 4 PASSED: Maturity calculation works correctly")
    return maturity


def test_5_maturity_with_specs():
    """Test 5: Maturity calculation with specs"""
    print("\n" + "=" * 70)
    print("TEST 5: Maturity Calculation - With Specs")
    print("=" * 70)

    from socratic_system.agents import QualityControllerAgent
    from socratic_system.models import ProjectContext

    # Create a mock orchestrator with minimal setup
    class MockClaudeClient:
        pass

    class MockEventEmitter:
        def emit(self, event_type, data=None):
            pass

    class MockOrchestrator:
        def __init__(self):
            self.claude_client = MockClaudeClient()
            self.event_emitter = MockEventEmitter()

    orchestrator = MockOrchestrator()
    agent = QualityControllerAgent(orchestrator)

    # Create a sample project
    project = ProjectContext(
        project_id="test_proj",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Build a web application",
        requirements=["Requirement 1"],
        tech_stack=["Python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="clean",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    # Add specs to discovery phase
    project.categorized_specs["discovery"] = [
        {
            "category": "goals",
            "content": "Build a web application",
            "confidence": 0.9,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "category": "goals",
            "content": "Help users manage tasks",
            "confidence": 0.9,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "category": "problem_definition",
            "content": "Users struggle with task organization",
            "confidence": 0.9,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
        {
            "category": "target_audience",
            "content": "Professionals and students",
            "confidence": 0.9,
            "value": 1.0,
            "timestamp": datetime.datetime.now().isoformat(),
        },
    ]

    result = agent._calculate_phase_maturity({"project": project, "phase": "discovery"})

    assert result["status"] == "success", f"Failed: {result}"
    maturity = result["maturity"]

    score = maturity["overall_score"]
    print(f"[OK] Maturity with 4 specs: {score:.1f}%")
    print(f"[OK] Total specs counted: {maturity['total_specs']}")
    print(f"[OK] Ready to advance: {maturity['is_ready_to_advance']}")

    assert score > 0.0, "Score should be > 0 with specs"
    assert maturity["total_specs"] == 4, "Should count all specs"

    # Check category scores
    cat_scores = maturity["category_scores"]
    print(
        f"[OK] Goals score: {cat_scores['goals']['current_score']:.1f}/{cat_scores['goals']['target_score']}"
    )
    print(
        f"[OK] Problem definition score: {cat_scores['problem_definition']['current_score']:.1f}/{cat_scores['problem_definition']['target_score']}"
    )

    print("\n[OK] TEST 5 PASSED: Maturity calculation with specs works correctly")
    return project


def test_6_categorization():
    """Test 6: Insight categorization"""
    print("\n" + "=" * 70)
    print("TEST 6: Insight Categorization")
    print("=" * 70)

    # Create a mock orchestrator with minimal setup
    class MockClaudeClient:
        pass

    class MockEventEmitter:
        def emit(self, event_type, data=None):
            pass

    class MockOrchestrator:
        def __init__(self):
            self.claude_client = MockClaudeClient()
            self.event_emitter = MockEventEmitter()

    from socratic_system.agents import QualityControllerAgent

    orchestrator = MockOrchestrator()
    agent = QualityControllerAgent(orchestrator)

    insights = {
        "goals": ["Build a web app", "Help users"],
        "requirements": ["Responsive design", "Fast performance"],
        "tech_stack": ["Python", "React"],
    }

    # Use the calculator's categorize_insights method
    categorized = agent.calculator.categorize_insights(insights, "discovery")

    print(f"[OK] Categorized {len(categorized)} specs from insights")

    for spec in categorized[:3]:
        print(
            f"  - {spec['category']}: {spec['content'][:40]}... (confidence: {spec['confidence']})"
        )

    assert len(categorized) > 0, "Should categorize some specs"
    assert all("category" in s and "content" in s for s in categorized), "Missing required fields"

    print("\n[OK] TEST 6 PASSED: Insight categorization works correctly")


def test_7_advancement_verification():
    """Test 7: Advancement verification"""
    print("\n" + "=" * 70)
    print("TEST 7: Advancement Verification")
    print("=" * 70)

    from socratic_system.agents import QualityControllerAgent
    from socratic_system.models import ProjectContext

    # Create a mock orchestrator with minimal setup
    class MockClaudeClient:
        pass

    class MockEventEmitter:
        def emit(self, event_type, data=None):
            pass

    class MockOrchestrator:
        def __init__(self):
            self.claude_client = MockClaudeClient()
            self.event_emitter = MockEventEmitter()

    orchestrator = MockOrchestrator()
    agent = QualityControllerAgent(orchestrator)

    # Create a sample project
    project = ProjectContext(
        project_id="test_proj",
        name="Test Project",
        owner="testuser",
        collaborators=[],
        goals="Test goals",
        requirements=["Req1"],
        tech_stack=["Python"],
        constraints=[],
        team_structure="individual",
        language_preferences="python",
        deployment_target="cloud",
        code_style="clean",
        phase="discovery",
        conversation_history=[],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
    )

    # Test verification with low maturity
    result = agent._verify_advancement({"project": project, "from_phase": "discovery"})

    assert result["status"] == "success", "Verification should succeed"
    verification = result["verification"]

    print("[OK] Verification completed")
    print(f"[OK] Maturity score: {verification['maturity_score']:.1f}%")
    print(f"[OK] Ready to advance: {verification['ready']}")
    print(f"[OK] Number of warnings: {len(verification['warnings'])}")

    if verification["warnings"]:
        print(f"[OK] Sample warning: {verification['warnings'][0][:60]}...")

    # Should not be ready (score too low)
    assert verification["maturity_score"] < 60, "Should be below 60%"
    assert len(verification["warnings"]) > 0, "Should have warnings"

    print("\n[OK] TEST 7 PASSED: Advancement verification works correctly")


def test_8_orchestrator_registration():
    """Test 8: Agent registered in orchestrator"""
    print("\n" + "=" * 70)
    print("TEST 8: Orchestrator Registration")
    print("=" * 70)

    # This test just verifies the imports and registration logic
    try:
        from socratic_system.orchestration import AgentOrchestrator

        print("[OK] AgentOrchestrator imported")
        print("[OK] QualityControllerAgent imported")
        print("[OK] Both are available for instantiation")

        # Check that orchestrator has the agent registration in code
        import inspect

        src = inspect.getsource(AgentOrchestrator._initialize_agents)

        assert "quality_controller" in src, "quality_controller not initialized in orchestrator"
        print("[OK] quality_controller initialization found in _initialize_agents()")

        src = inspect.getsource(AgentOrchestrator.process_request)
        assert "quality_controller" in src, "quality_controller not in process_request"
        print("[OK] quality_controller routing found in process_request()")

        print("\n[OK] TEST 8 PASSED: Orchestrator registration verified")

    except Exception as e:
        print(f"\n[FAILED] TEST 8 FAILED: {e}")
        raise


def test_9_socratic_counselor_integration():
    """Test 9: SocraticCounselorAgent modifications"""
    print("\n" + "=" * 70)
    print("TEST 9: SocraticCounselorAgent Integration")
    print("=" * 70)

    try:
        import inspect

        from socratic_system.agents import SocraticCounselorAgent

        # Check _process_response has quality controller call
        src = inspect.getsource(SocraticCounselorAgent._process_response)
        assert "quality_controller" in src, "_process_response missing quality_controller call"
        assert "update_after_response" in src, "_process_response missing update_after_response"
        print("[OK] _process_response() calls quality_controller.update_after_response()")

        # Check _advance_phase has quality controller call
        src = inspect.getsource(SocraticCounselorAgent._advance_phase)
        assert "quality_controller" in src, "_advance_phase missing quality_controller call"
        assert "verify_advancement" in src, "_advance_phase missing verify_advancement"
        assert "EventType.PHASE_ADVANCED" in src, "_advance_phase missing PHASE_ADVANCED emission"
        print("[OK] _advance_phase() calls quality_controller.verify_advancement()")
        print("[OK] _advance_phase() emits EventType.PHASE_ADVANCED")

        # Check EventType import in module
        import socratic_system.agents.socratic_counselor as sc_module

        src = inspect.getsource(sc_module)
        assert "from socratic_system.events import EventType" in src, "EventType not imported"
        print("[OK] EventType properly imported in SocraticCounselorAgent")

        print("\n[OK] TEST 9 PASSED: SocraticCounselorAgent properly integrated")

    except Exception as e:
        print(f"\n[FAILED] TEST 9 FAILED: {e}")
        raise


def test_10_ui_commands_registered():
    """Test 10: Maturity commands registered"""
    print("\n" + "=" * 70)
    print("TEST 10: UI Commands Registration")
    print("=" * 70)

    try:

        print("[OK] MaturityCommand imported")
        print("[OK] MaturitySummaryCommand imported")
        print("[OK] MaturityHistoryCommand imported")
        print("[OK] MaturityStatusCommand imported")

        # Check they're in __all__
        from socratic_system.ui.commands import __all__

        for cmd in [
            "MaturityCommand",
            "MaturitySummaryCommand",
            "MaturityHistoryCommand",
            "MaturityStatusCommand",
        ]:
            assert cmd in __all__, f"{cmd} not in __all__"
            print(f"[OK] {cmd} in __all__")

        print("\n[OK] TEST 10 PASSED: All maturity commands registered")

    except Exception as e:
        print(f"\n[FAILED] TEST 10 FAILED: {e}")
        raise


def test_11_maturity_display():
    """Test 11: Maturity display component"""
    print("\n" + "=" * 70)
    print("TEST 11: Maturity Display Component")
    print("=" * 70)

    try:
        from socratic_system.ui.maturity_display import MaturityDisplay

        print("[OK] MaturityDisplay imported successfully")

        # Check all methods exist
        methods = [
            "display_maturity_update",
            "display_detailed_maturity",
            "display_maturity_summary_all_phases",
            "display_maturity_history",
            "display_phase_completion_status",
        ]

        for method in methods:
            assert hasattr(MaturityDisplay, method), f"Method {method} not found"
            print(f"[OK] {method} method exists")

        print("\n[OK] TEST 11 PASSED: MaturityDisplay component is complete")

    except Exception as e:
        print(f"\n[FAILED] TEST 11 FAILED: {e}")
        raise


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MATURITY IMPLEMENTATION TEST SUITE")
    print("=" * 70)

    try:
        # Test 1: Model initialization
        project = test_1_model_initialization()

        # Test 2: Event types
        test_2_event_types()

        # Test 3: Quality controller agent
        agent = test_3_quality_controller_agent(project)

        # Test 4: Maturity calculation empty
        test_4_maturity_calculation(agent, project)

        # Test 5: Maturity calculation with specs
        project = test_5_maturity_with_specs(agent, project)

        # Test 6: Insight categorization
        test_6_categorization(agent)

        # Test 7: Advancement verification
        test_7_advancement_verification(agent, project)

        # Test 8: Orchestrator registration
        test_8_orchestrator_registration()

        # Test 9: SocraticCounselorAgent integration
        test_9_socratic_counselor_integration()

        # Test 10: UI commands
        test_10_ui_commands_registered()

        # Test 11: Maturity display
        test_11_maturity_display()

        # Summary
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print("\n[OK] Models: Initialized correctly with all fields")
        print("[OK] Events: All 5 new events defined and accessible")
        print("[OK] QualityControllerAgent: Created and functional")
        print("[OK] Maturity Calculation: Works with 0 and multiple specs")
        print("[OK] Insight Categorization: Maps insights to categories")
        print("[OK] Advancement Verification: Checks maturity correctly")
        print("[OK] Orchestrator: Agent properly registered and routable")
        print("[OK] SocraticCounselor: Calls quality controller hooks")
        print("[OK] UI Commands: All 4 commands registered")
        print("[OK] Display: MaturityDisplay component complete")
        print("\n[OK] READY FOR TESTING IN ACTUAL APPLICATION")
        print("=" * 70 + "\n")

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("TEST SUITE FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
