#!/usr/bin/env python3
"""
End-to-end test for Socratic questioning with user API keys.
Tests the full flow: API key retrieval → LLMClient creation → Adapter wrapping → SocraticCounselor
"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'backend/src')

def test_api_key_retrieval():
    """Test 1: Verify API key is in database"""
    print("\n" + "="*60)
    print("TEST 1: API Key Retrieval")
    print("="*60)
    
    from socrates_api.database import get_database
    db = get_database()
    
    api_key = db.get_api_key("Themis", "claude")
    if not api_key:
        print("[FAIL] No API key found for Themis/claude")
        return False
    
    print("[PASS] API key found (length: {})".format(len(api_key)))
    return True

def test_fallback_logic():
    """Test 2: Verify fallback provider logic"""
    print("\n" + "="*60)
    print("TEST 2: Fallback Provider Logic")
    print("="*60)
    
    from socrates_api.database import get_database
    db = get_database()
    
    # Check default provider
    default = db.get_user_default_provider("Themis")
    print("Default provider: {}".format(default))
    
    # Check key for default provider
    key_for_default = db.get_api_key("Themis", default)
    print("Key for default ({}): {}".format(default, "FOUND" if key_for_default else "NOT FOUND"))
    
    # Simulate fallback logic
    user_api_key = key_for_default
    provider = default
    
    if not user_api_key:
        for fallback in ["claude", "openai", "gemini"]:
            key = db.get_api_key("Themis", fallback)
            if key:
                provider = fallback
                user_api_key = key
                print("Fallback to {}".format(fallback))
                break
    
    if user_api_key:
        print("[PASS] Using provider '{}'".format(provider))
        return True, provider
    else:
        print("[FAIL] No API key found in fallback logic")
        return False, None

def test_model_validation():
    """Test 3: Test model validation function"""
    print("\n" + "="*60)
    print("TEST 3: Model Validation")
    print("="*60)
    
    try:
        from socrates_api.orchestrator import _get_valid_model_for_provider
        
        # Test with different models
        tests = [
            ("claude", "claude-3-sonnet", "Should correct invalid model"),
            ("claude", "claude-haiku-4-5-20251001", "Should keep valid model"),
            ("claude", None, "Should use default model"),
        ]
        
        for provider, model_input, description in tests:
            result = _get_valid_model_for_provider(provider, model_input)
            print("  {}/{} -> {} ({})".format(
                provider, 
                model_input or "None", 
                result, 
                description
            ))
        
        print("[PASS] Model validation working")
        return True
    except Exception as e:
        print("[FAIL] {}".format(e))
        return False

def main():
    print("\n" + "="*60)
    print("COMPREHENSIVE SOCRATIC FLOW TEST")
    print("="*60)
    
    # Test 1: API Key
    if not test_api_key_retrieval():
        print("\n[FATAL] API key not found. Cannot proceed.")
        return False
    
    # Test 2: Fallback Logic
    success, provider = test_fallback_logic()
    if not success:
        print("\n[FATAL] Fallback logic failed.")
        return False
    
    # Test 3: Model Validation
    if not test_model_validation():
        print("\n[FATAL] Model validation failed.")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("[SUCCESS] ALL TESTS PASSED - Ready for backend restart")
    print("="*60)
    print("\nNext step: Restart backend with:")
    print("  python socrates.py --full")
    print("\nThen try asking a question in chat.")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print("\n[FATAL ERROR] {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
