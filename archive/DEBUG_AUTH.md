# Authentication Debug Guide

## Quick Browser Console Check

Run these commands in your browser console (F12) to check if tokens are stored:

```javascript
// Check if tokens exist in localStorage
console.log("Access Token:", localStorage.getItem('access_token'));
console.log("Refresh Token:", localStorage.getItem('refresh_token'));

// Try to decode and inspect the access token
const token = localStorage.getItem('access_token');
if (token) {
  const parts = token.split('.');
  if (parts.length === 3) {
    const decoded = JSON.parse(atob(parts[1]));
    console.log("Token payload:", decoded);
    console.log("Token expires at:", new Date(decoded.exp * 1000));
    console.log("Token expired?", Date.now() / 1000 > decoded.exp);
  }
}

// Check API client state
console.log("API Client authenticated?", apiClient.isAuthenticated());
```

## Expected Results

✅ **Success**: You should see:
- Access token stored in localStorage
- Refresh token stored in localStorage
- Token payload with `sub` field containing username
- Current time before `exp` field

❌ **Problem**: If you see:
- Both tokens are `null` → Login didn't save tokens
- Token is expired → Need to refresh token
- API Client returns `false` → Tokens not loaded by client

## Common Issues

### Issue 1: Tokens Missing After Login
- Login may not have completed successfully
- Check Network tab → look for `/auth/login` response
- Response should contain `access_token` and `refresh_token`

### Issue 2: Tokens Expired
- Access tokens expire after 15 minutes
- Frontend should auto-refresh, but may have failed
- Try logging out and logging back in

### Issue 3: Token Not Being Sent
- The APIClient should auto-inject tokens in Authorization header
- Check Network tab → look at any API request → Headers tab
- Should see: `Authorization: Bearer <token>`

## Manual Test (Using Browser Console)

```javascript
// Try making a projects request manually
fetch('http://localhost:8000/projects', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
})
.then(r => r.json())
.then(data => console.log('Response:', data));
```

This should return your projects or a clear error message.
