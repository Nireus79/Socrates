# Socrates API Reference

Complete reference guide for the Socrates REST API, WebSocket API, and Python client library.

## Quick Links

- **REST API**: Base URL `http://localhost:8000/api/v1`
- **Swagger UI**: `http://localhost:8000/docs` (interactive documentation)
- **ReDoc**: `http://localhost:8000/redoc` (alternative documentation)
- **WebSocket**: `ws://localhost:8000/ws`

## Authentication

All API endpoints require authentication. Use one of these methods:

### Bearer Token Authentication
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/api/v1/projects
```

### Python Client
```python
from socratic_system.api.client import SocratesClient

client = SocratesClient(api_key="your-api-key", base_url="http://localhost:8000")
```

---

## Chat & Specs Endpoints

### POST /projects/{project_id}/chat/message
Send a message in Socratic or Direct mode dialogue.

**Response with Debug Mode (Confirmation Required):**
```json
{
    "success": true,
    "data": {
        "message": {
            "id": "msg_xyz",
            "role": "assistant",
            "content": "Your response has been analyzed.",
            "timestamp": "2026-05-02T12:00:00Z"
        },
        "mode": "socratic",
        "requires_confirmation": true,
        "confirmation_message": "Extracted 3 insight categories - please confirm to save",
        "extracted_specs": {
            "goals": ["Become market leader"],
            "requirements": ["Real-time analytics"],
            "tech_stack": ["Node.js"],
            "constraints": ["Budget $50k"]
        }
    }
}
```

**Behavior:**
- **Debug Mode OFF**: Specs auto-saved silently, no confirmation
- **Debug Mode ON**: Returns specs with `requires_confirmation: true`
- Call `/save-extracted-specs` to confirm and save

### POST /projects/{project_id}/save-extracted-specs
Save extracted specs after user confirmation.

---

## Project Management Endpoints

### GET /projects
List all projects for the authenticated user.

### POST /projects
Create a new project.

### GET /projects/{project_id}
Get detailed project information.

### PUT /projects/{project_id}
Update project details.

### DELETE /projects/{project_id}
Delete or archive a project.

---

## Background Analysis Endpoints

### GET /background/quality
Get cached quality analysis results.

### GET /background/conflicts
Get cached conflict detection results.

### GET /background/insights
Get cached insights analysis results.

---

## WebSocket API

Connect to real-time updates:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/analysis/proj_abc');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'quality.completed') {
        console.log('Quality analysis:', message.data);
    }
};
```

---

## Error Handling

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message"
    }
}
```

### Common Error Codes
- `INVALID_REQUEST` (400) - Invalid parameters
- `AUTHENTICATION_FAILED` (401) - Invalid API key
- `NOT_FOUND` (404) - Resource not found
- `RATE_LIMITED` (429) - Too many requests
- `INTERNAL_ERROR` (500) - Server error

---

## Rate Limiting

- **Default**: 100 requests per minute per user
- **Headers**:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

---

## See Also

- [Architecture Guide](ARCHITECTURE.md)
- [REST Endpoints Detail](../socratic_system/api/REST_ENDPOINTS.md)
- [Client API](../socratic_system/api/CLIENT_API.md)
