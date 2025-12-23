# Test-Driven Development Principles - CRITICAL

**Date**: December 23, 2025
**Status**: Mandatory Framework

---

## 🎯 Core Principle

**TESTS ARE THE SPECIFICATION, NOT THE ENEMY**

### Golden Rule
```
❌ WRONG: Modify tests to pass (Test Corruption)
✅ CORRECT: Modify code to pass tests (Root Cause Fix)

When a test fails:
  Don't ask: "How do I make this test pass?"
  Ask instead: "Why is my code wrong?"
```

---

## Why This Matters

### Test Corruption Chain
```
Problem: Test fails
Wrong approach: Modify test to accept bad behavior
Result: Bugs hide in code, users suffer

Example:
❌ test_login_persists_user() fails
❌ "Just modify test to not check localStorage"
❌ User loses session on page refresh
❌ Users complain, system fails
```

### Root Cause Fix Chain
```
Problem: Test fails
Correct approach: Investigate why code doesn't match specification
Result: Code fixed, bugs prevented, users happy

Example:
✅ test_login_persists_user() fails
✅ "Why doesn't authStore save user to localStorage?"
✅ Found: setAuthTokens() doesn't save user
✅ Fixed: Added localStorage.setItem('user', ...)
✅ Test passes, user session persists
✅ No bugs reach production
```

---

## Root Cause Analysis Framework

### When a Test Fails

**Step 1: Read the Test**
```python
def test_user_stays_authenticated_after_refresh(self):
    """User should stay logged in after page refresh"""
    # 1. Login
    login_response = self.client.post('/auth/login', ...)
    token = login_response.data['access_token']

    # 2. Save to localStorage
    localStorage.setItem('access_token', token)
    localStorage.setItem('user', JSON.stringify(user))

    # 3. Simulate page refresh
    restored = restore_auth()

    # 4. Assert: user still authenticated
    self.assertIsNotNone(restored.user)  # ❌ FAILS HERE
```

**Step 2: Understand the Specification**
The test is saying: "The system MUST restore user from localStorage on refresh"

This is not a test problem. This is a specification.

**Step 3: Investigate the Code**
```typescript
// Current code - WRONG
function restoreAuthFromStorage() {
    const token = localStorage.getItem('access_token');
    // ❌ User NOT restored!
    // ❌ Code doesn't match test specification
}
```

**Step 4: Fix the Root Cause**
```typescript
// Fixed code - CORRECT
function restoreAuthFromStorage() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');

    // ✅ User restored from localStorage
    // ✅ Code now matches test specification
    if (userData) {
        const user = JSON.parse(userData);
        setAuthTokens(token, null, user);
    }
}
```

**Step 5: Verify Test Passes**
Test should now pass. If not, code still doesn't match specification.

---

## Examples: Wrong vs Right Approaches

### Example 1: Login Test Fails

**Scenario**: Test expects login to return user object

**❌ WRONG APPROACH**
```typescript
// Test
test_user_returned_in_login() {
    response = login('user', 'pass');
    expect(response.user).toBeDefined();  // ❌ FAILS
}

// "Fix": Modify test (WRONG!)
test_user_returned_in_login() {
    response = login('user', 'pass');
    expect(response.user).toBeUndefined();  // ✅ "Passes" (but code is wrong!)
}

// Result: Login doesn't return user, system breaks
```

**✅ CORRECT APPROACH**
```typescript
// Test (unchanged - it's the specification)
test_user_returned_in_login() {
    response = login('user', 'pass');
    expect(response.user).toBeDefined();  // ❌ FAILS
}

// Investigate: Why doesn't login return user?
// Root cause: Login handler doesn't fetch/return user object

// Fix the code (not the test!)
async function login(username, password) {
    const result = authenticate(username, password);
    const user = await database.getUser(result.userId);  // ✅ Get user
    return {
        access_token: result.token,
        user: user  // ✅ Return user
    };
}

// Result: Test passes, code correct, system works ✅
```

---

## Proper Test-Driven Development Cycle

### Phase 1: Write Tests First
```
1. Understand requirement: "Users should stay logged in after refresh"
2. Write test that verifies this
3. Test fails (code doesn't exist yet)
```

### Phase 2: Write Minimal Code to Pass Test
```
1. Implement feature to pass test
2. Test passes
3. Code now implements specification
```

### Phase 3: Refactor
```
1. Improve code quality
2. Keep tests passing (verify with each change)
3. Code better, behavior unchanged
```

### Phase 4: Add More Tests for Edge Cases
```
1. Test failures edge cases
2. Test error conditions
3. Test concurrency, timing, etc.
4. Write minimal code to pass each test
5. Refactor
6. Repeat
```

---

## For This Project - Implementation Rule

**When running tests:**

1. ✅ Run tests to find bugs
2. ✅ Investigate why test fails
3. ✅ Fix CODE to match test specification
4. ❌ NEVER modify test to hide problem
5. ✅ Document what was fixed and why
6. ✅ Verify test passes

**This is the only way to ensure quality.**

---

**Document Version**: 1.0
**Created**: December 23, 2025
**Requirement**: Mandatory adherence for all testing work
