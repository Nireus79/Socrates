import sys
import json
sys.path.insert(0, 'backend/src')
sys.path.insert(0, '.')

from socrates_api.orchestrator import APIOrchestrator
from socratic_core import SocratesConfig

config = SocratesConfig(api_key="test-key")
orchestrator = APIOrchestrator(config)

result = orchestrator.process_request("multi_llm", {
    "action": "list_providers",
    "user_id": "testuser"
})

if result.get('status') == 'success':
    providers = result.get('data', {}).get('providers', [])
    print(f"Number of providers: {len(providers)}\n")
    
    for i, provider in enumerate(providers):
        print(f"Provider {i+1}:")
        print(f"  Keys: {list(provider.keys())}")
        print(f"  display_name: {provider.get('display_name')}")
        print(f"  name: {provider.get('name')}")
        print(f"  provider: {provider.get('provider')}")
        print(f"  requires_api_key: {provider.get('requires_api_key')}")
        print(f"  is_configured: {provider.get('is_configured')}")
        print()
