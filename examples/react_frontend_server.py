"""
React Frontend Server Integration Example for Socrates AI

This example demonstrates how to build a web server for a React frontend
that integrates with the Socrates AI library through a REST API.

Architecture:
```
React Frontend (TypeScript/React)
         ↓ HTTP/WebSocket
FastAPI Server (this file)
         ↓ Python API
Socrates Library
         ↓
Claude API
```

Features:
- REST endpoints for all Socrates functionality
- WebSocket for real-time event streaming
- Server-sent events (SSE) for event notifications
- CORS support for cross-origin requests
- Session management for user projects
- Token usage tracking and cost estimation

Installation:
1. Install dependencies: pip install fastapi uvicorn socrates-ai python-dotenv
2. Set ANTHROPIC_API_KEY environment variable
3. Run: python react_frontend_server.py
4. Access: http://localhost:8000

React Frontend Example:
```typescript
// useQuestion.ts
import { useEffect, useState } from 'react';

export function useQuestion(projectId: string) {
    const [question, setQuestion] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const askQuestion = async () => {
            setLoading(true);
            const response = await fetch('http://localhost:8000/projects/${projectId}/question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic: 'API design', difficulty_level: 'intermediate' })
            });
            const data = await response.json();
            setQuestion(data);
            setLoading(false);
        };

        askQuestion();
    }, [projectId]);

    return { question, loading };
}
```
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

try:
    import socrates
except ImportError:
    print("Install socrates-ai: pip install socrates-ai")
    raise

from pydantic import BaseModel

# ============================================================================
# Request/Response Models
# ============================================================================


class ProjectCreate(BaseModel):
    name: str
    owner: str
    description: Optional[str] = None


class QuestionRequest(BaseModel):
    topic: Optional[str] = None
    difficulty_level: str = "intermediate"


class ResponseSubmit(BaseModel):
    question_id: str
    user_response: str


class CodeGenerateRequest(BaseModel):
    specification: Optional[str] = None
    language: str = "python"


# ============================================================================
# Application State Manager
# ============================================================================


class SocratesAppState:
    """Manages application state and Socrates connection"""

    def __init__(self):
        self.orchestrator: Optional[socrates.AgentOrchestrator] = None
        self.event_history: list = []
        self.max_history = 100
        self.websocket_clients = set()

    async def initialize(self, api_key: str, data_dir: Optional[str] = None):
        """Initialize Socrates orchestrator"""
        config_builder = socrates.ConfigBuilder(api_key)
        if data_dir:
            from pathlib import Path

            config_builder = config_builder.with_data_dir(Path(data_dir))

        config = config_builder.build()
        self.orchestrator = socrates.create_orchestrator(config)

        # Setup event listeners
        self._setup_event_listeners()

        logger.info("Socrates initialized")

    def _setup_event_listeners(self):
        """Setup event listeners to track and broadcast events"""
        if not self.orchestrator:
            return

        def on_event(event_type, data):
            # Add to history
            event_record = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type.value,
                "data": data,
            }
            self.event_history.append(event_record)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)

            # Broadcast to WebSocket clients
            asyncio.create_task(self._broadcast_event(event_record))

        # Register listener for all event types
        emitter = self.orchestrator.event_emitter
        for event_type in [
            socrates.EventType.PROJECT_CREATED,
            socrates.EventType.CODE_GENERATED,
            socrates.EventType.QUESTION_GENERATED,
            socrates.EventType.AGENT_START,
            socrates.EventType.AGENT_COMPLETE,
            socrates.EventType.TOKEN_USAGE,
        ]:
            emitter.on(event_type, on_event)

    async def _broadcast_event(self, event_record: Dict[str, Any]):
        """Broadcast event to all connected WebSocket clients"""
        for ws in self.websocket_clients:
            try:
                await ws.send_text(json.dumps(event_record))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

    def add_websocket_client(self, websocket: WebSocket):
        """Register a WebSocket client"""
        self.websocket_clients.add(websocket)

    def remove_websocket_client(self, websocket: WebSocket):
        """Unregister a WebSocket client"""
        self.websocket_clients.discard(websocket)


# ============================================================================
# FastAPI Application Setup
# ============================================================================

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Socrates React Server",
    description="Backend server for Socrates AI React frontend",
    version="8.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
state = SocratesAppState()


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set")
        return

    await state.initialize(api_key)
    logger.info("Socrates React Server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Socrates React Server shutdown")


# ============================================================================
# Health & Info Endpoints
# ============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "initialized": state.orchestrator is not None}


@app.get("/info")
async def get_info():
    """Get server information"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    return {
        "version": "8.0.0",
        "library_version": socrates.__version__,
        "model": state.orchestrator.config.claude_model,
        "initialized": True,
    }


# ============================================================================
# Project Endpoints
# ============================================================================


@app.post("/api/projects")
async def create_project(request: ProjectCreate):
    """Create a new project"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    result = state.orchestrator.process_request(
        "project_manager",
        {
            "action": "create_project",
            "project_name": request.name,
            "owner": request.owner,
            "description": request.description or "",
        },
    )

    if result.get("status") == "success":
        project = result.get("project")
        return {
            "success": True,
            "project": {
                "project_id": project.project_id,
                "name": project.name,
                "owner": project.owner,
                "description": project.description,
                "phase": project.phase,
                "created_at": project.created_at.isoformat(),
            },
        }
    raise HTTPException(status_code=400, detail=result.get("message"))


@app.get("/api/projects")
async def list_projects(owner: Optional[str] = None):
    """List all projects"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    result = state.orchestrator.process_request(
        "project_manager", {"action": "list_projects", "owner": owner}
    )

    return {
        "success": True,
        "projects": result.get("projects", []),
        "total": len(result.get("projects", [])),
    }


# ============================================================================
# Question Endpoints
# ============================================================================


@app.post("/api/projects/{project_id}/question")
async def ask_question(project_id: str, request: QuestionRequest):
    """Get a Socratic question"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    result = state.orchestrator.process_request(
        "question_generator",
        {
            "action": "generate_question",
            "project_id": project_id,
            "topic": request.topic,
            "difficulty_level": request.difficulty_level,
        },
    )

    if result.get("status") == "success":
        return {
            "success": True,
            "question_id": result.get("question_id"),
            "question": result.get("question"),
            "context": result.get("context"),
            "hints": result.get("hints", []),
        }
    raise HTTPException(status_code=400, detail=result.get("message"))


@app.post("/api/projects/{project_id}/response")
async def submit_response(project_id: str, request: ResponseSubmit):
    """Submit a response and get feedback"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    result = state.orchestrator.process_request(
        "response_evaluator",
        {
            "action": "evaluate_response",
            "project_id": project_id,
            "question_id": request.question_id,
            "user_response": request.user_response,
        },
    )

    if result.get("status") == "success":
        return {
            "success": True,
            "feedback": result.get("feedback"),
            "is_correct": result.get("is_correct", False),
            "insights": result.get("insights", []),
        }
    raise HTTPException(status_code=400, detail=result.get("message"))


# ============================================================================
# Code Generation Endpoints
# ============================================================================


@app.post("/api/projects/{project_id}/code/generate")
async def generate_code(project_id: str, request: CodeGenerateRequest):
    """Generate code for a project"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    # Load project
    project_result = state.orchestrator.process_request(
        "project_manager", {"action": "load_project", "project_id": project_id}
    )

    if project_result.get("status") != "success":
        raise HTTPException(status_code=404, detail="Project not found")

    project = project_result["project"]

    # Generate code
    result = state.orchestrator.process_request(
        "code_generator",
        {
            "action": "generate_code",
            "project": project,
            "specification": request.specification or "",
            "language": request.language,
        },
    )

    if result.get("status") == "success":
        return {
            "success": True,
            "code": result.get("script", ""),
            "explanation": result.get("explanation"),
            "language": request.language,
            "token_usage": result.get("token_usage"),
        }
    raise HTTPException(status_code=400, detail=result.get("message"))


# ============================================================================
# Event Streaming Endpoints
# ============================================================================


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming"""
    await websocket.accept()
    state.add_websocket_client(websocket)

    try:
        # Send event history
        for event in state.event_history:
            await websocket.send_text(json.dumps(event))

        # Keep connection alive
        while True:
            # Receive and ignore client messages (could be heartbeat)
            await websocket.receive_text()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        state.remove_websocket_client(websocket)


@app.get("/api/events/stream")
async def stream_events():
    """Server-sent events (SSE) endpoint for real-time events"""

    async def event_generator():
        # Send event history
        for event in state.event_history:
            yield f"data: {json.dumps(event)}\n\n"

        # Keep connection open for new events
        while True:
            await asyncio.sleep(30)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/events/history")
async def get_event_history(limit: int = 50):
    """Get event history"""
    return {
        "success": True,
        "events": state.event_history[-limit:],
        "total": len(state.event_history),
    }


# ============================================================================
# Utility Endpoints
# ============================================================================


@app.post("/api/test-connection")
async def test_connection():
    """Test Claude API connection"""
    if not state.orchestrator:
        raise HTTPException(status_code=503, detail="Server not initialized")

    try:
        state.orchestrator.claude_client.test_connection()
        return {"success": True, "message": "Connection successful"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the server"""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info(f"Starting Socrates React Server on {host}:{port}")
    logger.info("Access API docs at http://localhost:8000/docs")

    uvicorn.run("react_frontend_server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
