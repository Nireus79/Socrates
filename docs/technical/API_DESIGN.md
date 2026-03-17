# API Route Design - All Service Endpoints
## Complete REST API Specification for Modular Socrates AI Platform

---

## API STRUCTURE OVERVIEW

```
Base URL: /api/v1

Routes by Service:
├── /agents          - Agent execution and management
├── /learning        - Learning tracking and skill generation
├── /knowledge       - Knowledge base management
├── /workflow        - Workflow orchestration
├── /analytics       - Metrics and insights
├── /system          - System health and info
└── /health          - Health check endpoints
```

---

## 1. AGENTS SERVICE ROUTES

### Base Path: `/api/v1/agents`

#### 1.1 Execute Agent

```http
POST /api/v1/agents/{agent_name}/execute
Content-Type: application/json

Request Body:
{
  "input_data": {
    "query": "Generate a Python function for...",
    "context": "user_id: 123"
  },
  "apply_skills": true,
  "timeout_seconds": 300
}

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "execution_id": "exec_abc123",
  "status": "success",
  "result": {
    "generated_code": "def func()...",
    "explanation": "This function...",
    "confidence": 0.95
  },
  "duration_ms": 2345,
  "skills_applied": ["error_handling", "documentation"],
  "timestamp": "2024-03-16T14:30:00Z"
}

Error Responses:
400: Invalid input
404: Agent not found
504: Timeout
```

#### 1.2 List Available Agents

```http
GET /api/v1/agents

Query Parameters:
- category: string (optional) - Filter by category (e.g., "generation", "validation")
- enabled_only: boolean (default: true)

Response (200 OK):
{
  "total_agents": 17,
  "agents": [
    {
      "name": "CodeGeneratorAgent",
      "description": "Generates code based on requirements",
      "category": "generation",
      "enabled": true,
      "version": "1.0",
      "current_skills": ["error_handling", "testing", "documentation"]
    },
    {
      "name": "SocraticCounselorAgent",
      "description": "Guides with Socratic questions",
      "category": "guidance",
      "enabled": true,
      "version": "1.0",
      "current_skills": ["questioning", "clarification"]
    }
    // ... 15 more agents
  ]
}
```

#### 1.3 Get Agent Details

```http
GET /api/v1/agents/{agent_name}

Response (200 OK):
{
  "name": "CodeGeneratorAgent",
  "description": "Generates code based on requirements",
  "category": "generation",
  "enabled": true,
  "version": "1.0",
  "dependencies": ["llm", "knowledge"],
  "current_skills": {
    "error_handling": {
      "confidence": 0.92,
      "effectiveness": 0.87,
      "last_used": "2024-03-16T10:15:00Z"
    },
    "documentation": {
      "confidence": 0.85,
      "effectiveness": 0.78,
      "last_used": "2024-03-16T11:45:00Z"
    }
  },
  "stats": {
    "total_executions": 234,
    "success_rate": 0.94,
    "avg_duration_ms": 3200,
    "last_execution": "2024-03-16T14:30:00Z"
  }
}
```

#### 1.4 Get Agent Skills

```http
GET /api/v1/agents/{agent_name}/skills

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "skills": [
    {
      "skill_id": "skill_001",
      "name": "error_handling",
      "type": "enhancement",
      "confidence": 0.92,
      "effectiveness": 0.87,
      "last_applied": "2024-03-16T14:30:00Z",
      "created_at": "2024-03-10T08:00:00Z"
    }
  ],
  "total_skills": 3,
  "skills_generated_at": "2024-03-15T12:00:00Z"
}
```

#### 1.5 Apply Skills Manually

```http
POST /api/v1/agents/{agent_name}/apply-skills

Request Body:
{
  "skill_ids": ["skill_001", "skill_002"]
}

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "applied_skills": 2,
  "message": "Skills applied successfully",
  "next_execution_will_use": ["error_handling", "documentation"]
}
```

#### 1.6 Agent Execution History

```http
GET /api/v1/agents/{agent_name}/history

Query Parameters:
- limit: integer (default: 50, max: 1000)
- offset: integer (default: 0)
- status: string (optional) - Filter by status (success, failure, timeout)
- from_date: ISO8601 (optional)
- to_date: ISO8601 (optional)

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "total_executions": 234,
  "page": 1,
  "per_page": 50,
  "executions": [
    {
      "execution_id": "exec_abc123",
      "timestamp": "2024-03-16T14:30:00Z",
      "status": "success",
      "duration_ms": 2345,
      "input_size": 234,
      "output_size": 1245,
      "skills_used": ["error_handling"],
      "confidence": 0.95
    }
  ]
}
```

---

## 2. LEARNING SERVICE ROUTES

### Base Path: `/api/v1/learning`

#### 2.1 Track Interaction

```http
POST /api/v1/learning/track

Request Body:
{
  "agent_name": "CodeGeneratorAgent",
  "session_id": "sess_abc123",
  "user_id": "user_123",
  "input_data": {
    "query": "Generate a Python function"
  },
  "output_data": {
    "code": "def func()..."
  },
  "status": "success",
  "duration_ms": 2345,
  "metadata": {
    "model_used": "claude-3-5-sonnet",
    "tokens_used": 450
  }
}

Response (201 Created):
{
  "interaction_id": "inter_abc123",
  "tracked": true,
  "timestamp": "2024-03-16T14:30:00Z"
}
```

#### 2.2 Generate Skills

```http
POST /api/v1/learning/{agent_name}/generate-skills

Query Parameters:
- force: boolean (default: false) - Force regeneration even if recent

Request Body:
{
  "context": {
    "recent_failures": 3,
    "performance_threshold": 0.8
  }
}

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "skills_generated": 2,
  "skills": [
    {
      "skill_id": "skill_new_001",
      "name": "error_recovery",
      "type": "enhancement",
      "confidence": 0.88,
      "description": "Handles errors and recovers gracefully",
      "recommended_application": "next_execution"
    },
    {
      "skill_id": "skill_new_002",
      "name": "performance_optimization",
      "type": "optimization",
      "confidence": 0.82,
      "description": "Optimizes code performance",
      "recommended_application": "next_execution"
    }
  ],
  "generation_reason": "Performance degradation detected",
  "next_regeneration_in_hours": 24
}
```

#### 2.3 Get Skill Recommendations

```http
GET /api/v1/learning/{agent_name}/recommendations

Query Parameters:
- priority: string (optional) - Filter by priority (high, medium, low)
- limit: integer (default: 10)

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "recommendations": [
    {
      "recommendation_id": "rec_001",
      "title": "Improve error handling",
      "priority": "high",
      "suggested_action": "Apply skill: error_recovery",
      "expected_impact": "Reduce failure rate by 5-10%",
      "confidence": 0.85
    },
    {
      "recommendation_id": "rec_002",
      "title": "Optimize for large inputs",
      "priority": "medium",
      "suggested_action": "Apply skill: performance_optimization",
      "expected_impact": "Reduce latency by 20-30%",
      "confidence": 0.78
    }
  ],
  "generated_at": "2024-03-16T10:00:00Z"
}
```

#### 2.4 Get Agent Metrics

```http
GET /api/v1/learning/{agent_name}/metrics

Query Parameters:
- period: string (default: "7days") - Options: "1day", "7days", "30days", "all"

Response (200 OK):
{
  "agent_name": "CodeGeneratorAgent",
  "period": "7days",
  "metrics": {
    "total_executions": 234,
    "success_rate": 0.94,
    "avg_duration_ms": 3200,
    "success_count": 220,
    "failure_count": 14,
    "skill_effectiveness": {
      "error_handling": 0.87,
      "documentation": 0.78,
      "overall": 0.82
    }
  },
  "trend": {
    "execution_count_trend": "up",
    "success_rate_trend": "stable",
    "performance_trend": "improving"
  },
  "generated_at": "2024-03-16T14:30:00Z"
}
```

#### 2.5 Get User Learning Profile

```http
GET /api/v1/learning/user/{user_id}/profile

Response (200 OK):
{
  "user_id": "user_123",
  "total_interactions": 1234,
  "learning_style": {
    "preferred_agents": ["SocraticCounselor", "CodeGenerator"],
    "learning_speed": "medium",
    "preference": "hands_on"
  },
  "patterns": [
    {
      "pattern_id": "pat_001",
      "name": "Early morning queries",
      "frequency": "every_weekday",
      "avg_sessions_per_day": 3
    }
  ],
  "weak_areas": [
    {
      "area": "Database design",
      "confidence": 0.45,
      "improvement_trend": "improving"
    }
  ],
  "strengths": [
    {
      "area": "Python development",
      "confidence": 0.92,
      "consistency": "very_high"
    }
  ]
}
```

#### 2.6 Get System Learning Status

```http
GET /api/v1/learning/system/status

Response (200 OK):
{
  "total_tracked_interactions": 45230,
  "agents_with_skills": 15,
  "total_skills_generated": 78,
  "last_skill_generation": "2024-03-16T10:00:00Z",
  "next_scheduled_generation": "2024-03-17T10:00:00Z",
  "learning_engine_status": "healthy",
  "skill_generator_status": "ready"
}
```

---

## 3. KNOWLEDGE SERVICE ROUTES

### Base Path: `/api/v1/knowledge`

#### 3.1 Search Knowledge

```http
POST /api/v1/knowledge/search

Request Body:
{
  "query": "Python async patterns",
  "top_k": 5,
  "filters": {
    "category": "programming",
    "language": "python"
  }
}

Response (200 OK):
{
  "query": "Python async patterns",
  "results": [
    {
      "item_id": "kb_001",
      "title": "Understanding asyncio in Python",
      "content_preview": "Asyncio is a library to write concurrent code...",
      "relevance_score": 0.98,
      "category": "programming",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-03-10T14:30:00Z"
    },
    {
      "item_id": "kb_002",
      "title": "Async/await best practices",
      "content_preview": "When using async/await, consider...",
      "relevance_score": 0.95,
      "category": "programming",
      "created_at": "2024-02-20T10:00:00Z",
      "updated_at": "2024-03-12T09:15:00Z"
    }
  ],
  "total_results": 23,
  "search_time_ms": 125
}
```

#### 3.2 Add Knowledge Items

```http
POST /api/v1/knowledge/items

Request Body:
{
  "items": [
    {
      "title": "Understanding asyncio in Python",
      "content": "Asyncio is a library to write concurrent code...",
      "category": "programming",
      "tags": ["python", "async", "concurrency"],
      "source": "internal",
      "metadata": {
        "author": "John Doe",
        "reviewed": true
      }
    }
  ]
}

Response (201 Created):
{
  "items_added": 1,
  "items": [
    {
      "item_id": "kb_001",
      "status": "created"
    }
  ]
}
```

#### 3.3 Get Knowledge Item Details

```http
GET /api/v1/knowledge/items/{item_id}

Response (200 OK):
{
  "item_id": "kb_001",
  "title": "Understanding asyncio in Python",
  "content": "Full content here...",
  "category": "programming",
  "tags": ["python", "async"],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-03-10T14:30:00Z",
  "version": 3,
  "embedding_updated": "2024-03-10T14:30:00Z",
  "access_stats": {
    "view_count": 234,
    "last_viewed": "2024-03-16T14:00:00Z"
  }
}
```

#### 3.4 Update Knowledge Item

```http
PUT /api/v1/knowledge/items/{item_id}

Request Body:
{
  "title": "Updated title",
  "content": "Updated content",
  "category": "programming",
  "tags": ["python", "async", "new-tag"]
}

Response (200 OK):
{
  "item_id": "kb_001",
  "status": "updated",
  "version": 4,
  "previous_version": 3
}
```

#### 3.5 Delete Knowledge Item

```http
DELETE /api/v1/knowledge/items/{item_id}

Response (204 No Content)
```

#### 3.6 Knowledge Statistics

```http
GET /api/v1/knowledge/stats

Response (200 OK):
{
  "total_items": 2345,
  "categories": {
    "programming": 890,
    "architecture": 456,
    "operations": 234
  },
  "total_embeddings": 2345,
  "embedding_model": "all-MiniLM-L6-v2",
  "last_reindexed": "2024-03-16T02:00:00Z",
  "search_index_size_mb": 234,
  "avg_retrieval_time_ms": 45
}
```

---

## 4. WORKFLOW SERVICE ROUTES

### Base Path: `/api/v1/workflow`

#### 4.1 Create Workflow

```http
POST /api/v1/workflow/create

Request Body:
{
  "name": "Code Review Pipeline",
  "description": "Review code and suggest improvements",
  "tasks": [
    {
      "task_id": "task_1",
      "agent_name": "CodeGeneratorAgent",
      "input": {"code_to_review": "..."},
      "depends_on": []
    },
    {
      "task_id": "task_2",
      "agent_name": "CodeValidatorAgent",
      "input": {"code": "from_task_1"},
      "depends_on": ["task_1"]
    },
    {
      "task_id": "task_3",
      "agent_name": "SocraticCounselorAgent",
      "input": {"issues": "from_task_2"},
      "depends_on": ["task_2"]
    }
  ],
  "optimization": {
    "enable": true,
    "priority": "cost"  // or "speed"
  }
}

Response (201 Created):
{
  "workflow_id": "wf_abc123",
  "name": "Code Review Pipeline",
  "status": "created",
  "task_count": 3,
  "optimization": {
    "estimated_cost": "$0.45",
    "estimated_duration_seconds": 180,
    "parallelizable_tasks": 0
  }
}
```

#### 4.2 Execute Workflow

```http
POST /api/v1/workflow/{workflow_id}/execute

Request Body:
{
  "input_data": {
    "code_to_review": "def my_func(): pass"
  }
}

Response (200 OK):
{
  "execution_id": "exec_wf_abc123",
  "workflow_id": "wf_abc123",
  "status": "running",
  "tasks_completed": 0,
  "tasks_total": 3,
  "estimated_completion_seconds": 180
}

// Poll with:
GET /api/v1/workflow/execution/{execution_id}
```

#### 4.3 Get Workflow Execution Status

```http
GET /api/v1/workflow/execution/{execution_id}

Response (200 OK):
{
  "execution_id": "exec_wf_abc123",
  "workflow_id": "wf_abc123",
  "status": "completed",  // or "running", "failed"
  "started_at": "2024-03-16T14:30:00Z",
  "completed_at": "2024-03-16T14:33:45Z",
  "duration_ms": 225000,
  "actual_cost": "$0.42",
  "tasks": [
    {
      "task_id": "task_1",
      "status": "completed",
      "duration_ms": 45000,
      "cost": "$0.15",
      "output": {...}
    },
    {
      "task_id": "task_2",
      "status": "completed",
      "duration_ms": 90000,
      "cost": "$0.20",
      "output": {...}
    },
    {
      "task_id": "task_3",
      "status": "completed",
      "duration_ms": 90000,
      "cost": "$0.07",
      "output": {...}
    }
  ]
}
```

#### 4.4 List Workflows

```http
GET /api/v1/workflow

Query Parameters:
- user_id: string (optional)
- limit: integer (default: 50)
- offset: integer (default: 0)

Response (200 OK):
{
  "total_workflows": 234,
  "page": 1,
  "per_page": 50,
  "workflows": [
    {
      "workflow_id": "wf_abc123",
      "name": "Code Review Pipeline",
      "created_at": "2024-03-10T10:00:00Z",
      "last_executed": "2024-03-16T14:30:00Z",
      "execution_count": 45,
      "tasks": 3
    }
  ]
}
```

#### 4.5 Get Workflow Details

```http
GET /api/v1/workflow/{workflow_id}

Response (200 OK):
{
  "workflow_id": "wf_abc123",
  "name": "Code Review Pipeline",
  "description": "Review code and suggest improvements",
  "created_at": "2024-03-10T10:00:00Z",
  "updated_at": "2024-03-15T14:00:00Z",
  "tasks": [
    {
      "task_id": "task_1",
      "agent_name": "CodeGeneratorAgent",
      "depends_on": []
    },
    {
      "task_id": "task_2",
      "agent_name": "CodeValidatorAgent",
      "depends_on": ["task_1"]
    },
    {
      "task_id": "task_3",
      "agent_name": "SocraticCounselorAgent",
      "depends_on": ["task_2"]
    }
  ],
  "executions": {
    "total": 45,
    "successful": 44,
    "failed": 1,
    "avg_duration_ms": 215000,
    "avg_cost": "$0.41"
  }
}
```

#### 4.6 Optimize Workflow

```http
POST /api/v1/workflow/{workflow_id}/optimize

Request Body:
{
  "priority": "cost"  // or "speed"
}

Response (200 OK):
{
  "workflow_id": "wf_abc123",
  "optimization": {
    "original": {
      "estimated_cost": "$0.50",
      "estimated_duration_seconds": 200
    },
    "optimized": {
      "estimated_cost": "$0.42",
      "estimated_duration_seconds": 180,
      "parallel_tasks": 1
    },
    "savings": {
      "cost_percent": 16,
      "time_percent": 10
    }
  }
}
```

---

## 5. ANALYTICS SERVICE ROUTES

### Base Path: `/api/v1/analytics`

#### 5.1 Get System Metrics

```http
GET /api/v1/analytics/system/metrics

Query Parameters:
- period: string (default: "7days")

Response (200 OK):
{
  "period": "7days",
  "timestamp": "2024-03-16T14:30:00Z",
  "metrics": {
    "total_interactions": 45230,
    "total_workflows_executed": 234,
    "overall_success_rate": 0.94,
    "avg_response_time_ms": 3200,
    "total_cost": "$234.50",
    "unique_users": 123,
    "unique_agents_used": 15
  }
}
```

#### 5.2 Get Agent Metrics

```http
GET /api/v1/analytics/agents/metrics

Query Parameters:
- period: string (default: "7days")
- agent_name: string (optional)

Response (200 OK):
{
  "period": "7days",
  "agents": [
    {
      "agent_name": "CodeGeneratorAgent",
      "executions": 234,
      "success_rate": 0.96,
      "avg_duration_ms": 3400,
      "total_cost": "$45.23",
      "skill_effectiveness": 0.87
    },
    {
      "agent_name": "SocraticCounselorAgent",
      "executions": 156,
      "success_rate": 0.91,
      "avg_duration_ms": 2800,
      "total_cost": "$28.45",
      "skill_effectiveness": 0.82
    }
  ]
}
```

#### 5.3 Get Insights

```http
GET /api/v1/analytics/insights

Query Parameters:
- focus_area: string (optional) - "agents", "workflows", "users", "performance", "costs"

Response (200 OK):
{
  "insights": [
    {
      "insight_id": "ins_001",
      "title": "CodeGeneratorAgent performance improved",
      "description": "Success rate increased from 0.93 to 0.96 due to new skills",
      "severity": "positive",
      "confidence": 0.92,
      "recommendation": "Continue monitoring skill effectiveness",
      "generated_at": "2024-03-16T10:00:00Z"
    },
    {
      "insight_id": "ins_002",
      "title": "Cost optimization opportunity",
      "description": "Workflow optimization could reduce costs by 15%",
      "severity": "info",
      "confidence": 0.85,
      "recommendation": "Review workflow_abc123 for optimization",
      "generated_at": "2024-03-16T10:00:00Z"
    }
  ]
}
```

#### 5.4 Get Dashboard Data

```http
GET /api/v1/analytics/dashboard

Response (200 OK):
{
  "summary": {
    "total_interactions_today": 1234,
    "avg_success_rate": 0.94,
    "cost_today": "$45.23"
  },
  "charts": {
    "interactions_by_hour": [...],
    "success_rate_trend": [...],
    "top_agents": [...],
    "cost_breakdown": [...]
  }
}
```

---

## 6. SYSTEM ROUTES

### Base Path: `/api/v1/system`

#### 6.1 Health Check

```http
GET /api/v1/system/health

Response (200 OK):
{
  "status": "healthy",
  "timestamp": "2024-03-16T14:30:00Z",
  "services": {
    "agents": {"status": "healthy", "response_time_ms": 45},
    "learning": {"status": "healthy", "response_time_ms": 32},
    "knowledge": {"status": "healthy", "response_time_ms": 78},
    "workflow": {"status": "healthy", "response_time_ms": 56},
    "analytics": {"status": "healthy", "response_time_ms": 89},
    "database": {"status": "healthy"},
    "llm": {"status": "healthy"}
  }
}
```

#### 6.2 System Information

```http
GET /api/v1/system/info

Response (200 OK):
{
  "platform_version": "2.0.0",
  "deployment_mode": "microservices",  // or "single_process"
  "uptime_seconds": 864000,
  "services_running": 8,
  "database": {
    "type": "sqlite",
    "path": "/data/socrates.db"
  },
  "cache": {
    "type": "redis",
    "status": "connected"
  }
}
```

#### 6.3 Configuration Status

```http
GET /api/v1/system/config

Response (200 OK):
{
  "environment": "production",
  "debug_mode": false,
  "log_level": "info",
  "services": {
    "agents": {"enabled": true, "replicas": 3},
    "learning": {"enabled": true, "replicas": 2},
    "knowledge": {"enabled": true, "replicas": 2},
    "workflow": {"enabled": true, "replicas": 2},
    "analytics": {"enabled": true, "replicas": 1}
  }
}
```

---

## 7. AUTHENTICATION & HEADERS

All requests should include:

```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Request-ID: {unique_request_id}  // For tracing
```

---

## 8. ERROR RESPONSES

### Standard Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The agent 'NonexistentAgent' was not found",
    "details": {
      "agent_name": "NonexistentAgent",
      "available_agents": 15
    },
    "request_id": "req_abc123",
    "timestamp": "2024-03-16T14:30:00Z"
  }
}
```

### Common Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| INVALID_REQUEST | 400 | Invalid request parameters |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| CONFLICT | 409 | Resource already exists |
| TIMEOUT | 504 | Request timeout |
| SERVICE_ERROR | 500 | Internal service error |

---

## 9. RATE LIMITING

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1234567890
```

- 1000 requests per hour per user
- 10000 requests per hour per API key

---

## 10. PAGINATION

All list endpoints support:

```
Query Parameters:
- limit: integer (default: 50, max: 1000)
- offset: integer (default: 0)

Response includes:
- total: integer (total count)
- limit: integer (requested limit)
- offset: integer (requested offset)
- items: array
```

---

**Version**: 1.0
**Status**: Complete
**Total Endpoints**: 40+
