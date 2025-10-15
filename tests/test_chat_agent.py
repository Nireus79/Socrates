#!/usr/bin/env python3
"""
Test ChatAgent Integration
Tests the ChatAgent and its integration with AgentOrchestrator
"""
import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import initialize_system
from src.agents.orchestrator import AgentOrchestrator
from src.database import init_database, reset_database


@pytest.fixture(scope="function")
def clean_db():
    """Fixture providing clean database for each test"""
    db_path = 'data/socratic.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    reset_database()
    init_database()
    yield
    # Cleanup after test
    if os.path.exists(db_path):
        os.remove(db_path)
    reset_database()


@pytest.fixture(scope="function")
def orchestrator(clean_db):
    """Fixture providing initialized orchestrator"""
    services = initialize_system('config.yaml')
    return AgentOrchestrator(services)


def test_chat_agent_initialization(orchestrator):
    """Test that ChatAgent is properly initialized in orchestrator"""
    # Check that chat_agent is in the agents list
    assert 'chat_agent' in orchestrator.agents, "ChatAgent should be initialized"

    # Get the agent
    chat_agent = orchestrator.agents['chat_agent']

    # Verify it has the expected capabilities
    capabilities = chat_agent.get_capabilities()
    expected_capabilities = [
        'start_chat',
        'continue_chat',
        'end_chat',
        'get_chat_history',
        'extract_insights',
        'switch_topic',
        'get_chat_sessions',
        'export_chat_summary'
    ]

    for cap in expected_capabilities:
        assert cap in capabilities, f"ChatAgent should have capability: {cap}"

    print(f"✓ ChatAgent initialized with {len(capabilities)} capabilities")


def test_chat_agent_in_orchestrator_status(orchestrator):
    """Test that ChatAgent appears in orchestrator status"""
    status = orchestrator.get_agent_status()

    # Check overall status
    assert status.get('total_agents', 0) >= 10, "Should have at least 10 agents"

    # Check chat_agent specifically
    agents = status.get('agents', {})
    assert 'chat_agent' in agents, "ChatAgent should appear in status"

    chat_status = agents['chat_agent']
    assert chat_status['status'] == 'active', "ChatAgent should be active"
    assert chat_status['name'] == 'Chat Agent', "ChatAgent should have correct name"

    print(f"✓ ChatAgent status: {chat_status['status']}")
    print(f"✓ Total agents: {status['total_agents']}")


def test_chat_agent_capability_routing(orchestrator):
    """Test that ChatAgent capabilities are properly mapped"""
    # Check capability map includes chat capabilities
    capabilities = orchestrator.get_capabilities()

    chat_capabilities = [
        'start_chat',
        'continue_chat',
        'end_chat',
        'get_chat_history'
    ]

    for cap in chat_capabilities:
        assert cap in capabilities, f"Capability {cap} should be in capability map"

        # Verify it maps to chat_agent
        agents = orchestrator.get_agents_by_capability(cap)
        assert 'chat_agent' in agents, f"Capability {cap} should map to chat_agent"

    print(f"✓ All chat capabilities properly mapped")


def test_chat_agent_direct_routing(orchestrator):
    """Test routing a request directly to chat_agent"""
    # This will fail without a valid user, but should reach the agent
    result = orchestrator.route_request(
        agent_id='chat_agent',
        action='get_chat_sessions',
        data={'user_id': 'test_user_123'}
    )

    # Should get a response (even if it's an error due to missing user)
    assert isinstance(result, dict), "Should return a dict response"
    assert 'success' in result, "Response should have success field"

    # Check orchestrator metadata was added
    if 'orchestrator_metadata' in result:
        metadata = result['orchestrator_metadata']
        assert metadata['agent_id'] == 'chat_agent'
        assert metadata['action'] == 'get_chat_sessions'

    print(f"✓ Direct routing to ChatAgent works")
    print(f"  Response: {result.get('message', result.get('error', 'No message'))}")


def test_chat_agent_health_check(orchestrator):
    """Test ChatAgent responds to health checks"""
    health = orchestrator.health_check()

    # Check overall health
    assert 'agents' in health, "Health check should include agents"
    assert 'chat_agent' in health['agents'], "ChatAgent should be in health check"

    chat_health = health['agents']['chat_agent']
    assert chat_health['status'] in ['healthy', 'active'], \
        f"ChatAgent should be healthy, got: {chat_health['status']}"

    print(f"✓ ChatAgent health: {chat_health['status']}")
    print(f"✓ Overall orchestrator health: {health['orchestrator']}")


if __name__ == '__main__':
    print("=" * 70)
    print("ChatAgent Integration Tests")
    print("=" * 70)

    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
