import sys
sys.path.insert(0, 'backend/src')
sys.path.insert(0, '.')

from socrates_api.orchestrator import LLMClientAdapter
from socrates_nexus import LLMClient

# Create a mock LLMClient (this will fail without API key, but let's see the adapter structure)
try:
    real_client = LLMClient(provider="anthropic", model="claude-3-sonnet", api_key="test")
    adapter = LLMClientAdapter(real_client)
    
    # Check if adapter has generate_response
    print(f"Adapter has generate_response: {hasattr(adapter, 'generate_response')}")
    print(f"Adapter has chat: {hasattr(adapter, 'chat')}")
    print(f"Adapter has stream: {hasattr(adapter, 'stream')}")
    print(f"Adapter callable methods: {[m for m in dir(adapter) if not m.startswith('_') and callable(getattr(adapter, m))]}")
except Exception as e:
    print(f"Expected error during client creation (no real API key): {type(e).__name__}")
    print(f"This is OK - we're just testing the adapter structure")
    
    # Test the adapter with a mock
    class MockClient:
        def chat(self, messages):
            return {"content": "Test response"}
        def stream(self, messages):
            yield "Test"
    
    mock = MockClient()
    adapter = LLMClientAdapter(mock)
    
    print(f"\nWith mock client:")
    print(f"Adapter has generate_response: {hasattr(adapter, 'generate_response')}")
    print(f"Adapter has chat: {hasattr(adapter, 'chat')}")
    
    # Test generate_response
    try:
        result = adapter.generate_response("Test prompt")
        print(f"generate_response result: {result}")
    except Exception as e:
        print(f"Error calling generate_response: {e}")
