import sys
sys.path.insert(0, 'backend/src')
sys.path.insert(0, '.')

from socrates_api.orchestrator import APIOrchestrator
from socratic_core import SocratesConfig

print("Creating orchestrator...")
config = SocratesConfig(api_key="test-key")
orchestrator = APIOrchestrator(config)

# Test list_providers
print("Testing list_providers...")
result = orchestrator.process_request("multi_llm", {
    "action": "list_providers",
    "user_id": "testuser"
})

print("Result status:", result.get('status'))
print("Result message:", result.get('message'))
if result.get('status') == 'success':
    providers = result.get('data', {}).get('providers', [])
    print(f"Providers returned: {len(providers)}")
    if providers:
        print(f"First provider: {providers[0].get('display_name')} (name: {providers[0].get('name')})")
else:
    print("Full result:", result)
