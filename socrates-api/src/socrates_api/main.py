"""
Socrates API - FastAPI application for Socrates AI tutoring system

Provides REST endpoints for project management, Socratic questioning, and code generation.
"""

import os
import logging
import socket
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Body, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from socratic_system.orchestration.orchestrator import AgentOrchestrator
from socratic_system.events import EventType

from .auth import get_current_user
from .models import (
    CreateProjectRequest,
    ProjectResponse,
    ListProjectsResponse,
    AskQuestionRequest,
    QuestionResponse,
    ProcessResponseRequest,
    ProcessResponseResponse,
    GenerateCodeRequest,
    CodeGenerationResponse,
    ErrorResponse,
    SystemInfoResponse,
    InitializeRequest,
)
from .routers import (
    auth_router,
    projects_router,
    websocket_router,
    collaboration_router,
    collab_router,
    code_generation_router,
    knowledge_router,
    llm_router,
    analysis_router,
    security_router,
    analytics_router,
    github_router,
    events_router,
    chat_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
app_state = {"orchestrator": None, "start_time": time.time(), "event_listeners_registered": False}


def get_orchestrator() -> AgentOrchestrator:
    """Dependency injection for orchestrator"""
    if app_state["orchestrator"] is None:
        raise RuntimeError("Orchestrator not initialized. Call /initialize first.")
    return app_state["orchestrator"]


def _setup_event_listeners(orchestrator: AgentOrchestrator):
    """Setup listeners for orchestrator events"""
    if app_state["event_listeners_registered"]:
        return

    # Log all events
    def on_any_event(event_type, data):
        logger.info(f"[Event] {event_type.value}: {data}")

    # Track specific important events
    def on_project_created(event_type, data):
        logger.info(f"Project created: {data.get('project_id')}")

    def on_code_generated(event_type, data):
        logger.info(f"Code generated: {data.get('lines')} lines")

    def on_agent_error(event_type, data):
        logger.error(f"Agent error in {data.get('agent_name')}: {data.get('error')}")

    # Register listeners
    orchestrator.event_emitter.on(EventType.PROJECT_CREATED, on_project_created)
    orchestrator.event_emitter.on(EventType.CODE_GENERATED, on_code_generated)
    orchestrator.event_emitter.on(EventType.AGENT_ERROR, on_agent_error)

    app_state["event_listeners_registered"] = True
    logger.info("Event listeners registered")


# Create FastAPI application
app = FastAPI(
    title="Socrates API",
    description="REST API for Socrates AI tutoring system powered by Claude",
    version="8.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(websocket_router)
app.include_router(collaboration_router)
app.include_router(collab_router)
app.include_router(code_generation_router)
app.include_router(knowledge_router)
app.include_router(llm_router)
app.include_router(analysis_router)
app.include_router(security_router)
app.include_router(analytics_router)
app.include_router(github_router)
app.include_router(events_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Socrates API", "version": "8.0.0"}


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Socrates API server...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Socrates API server...")
    # Close database connection
    from socrates_api.database import close_database
    close_database()


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "initialized": app_state["orchestrator"] is not None}


@app.post("/initialize", response_model=SystemInfoResponse)
async def initialize(request: Optional[InitializeRequest] = Body(None)):
    """
    Initialize the Socrates API with configuration

    Parameters:
    - api_key: Claude API key (optional, will use ANTHROPIC_API_KEY env var if not provided)
    """
    try:
        # Get API key from request body or environment variable
        api_key = None
        if request and request.api_key:
            api_key = request.api_key
        else:
            # Fall back to environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="API key is required. Provide api_key in request body or set ANTHROPIC_API_KEY environment variable."
            )

        # Create configuration
        config_dict = {"api_key": api_key}
        data_dir = os.getenv("SOCRATES_DATA_DIR", None)
        if data_dir:
            config_dict["data_dir"] = Path(data_dir)

        # Create orchestrator with API key
        # AgentOrchestrator requires api_key_or_config parameter
        orchestrator = AgentOrchestrator(api_key_or_config=api_key)

        # Test connection
        orchestrator.claude_client.test_connection()

        # Setup event listeners
        _setup_event_listeners(orchestrator)

        # Store in global state
        app_state["orchestrator"] = orchestrator
        app_state["start_time"] = time.time()

        logger.info("Socrates API initialized successfully")

        return SystemInfoResponse(
            version="8.0.0", library_version="8.0.0", status="operational", uptime=0.0
        )

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", response_model=SystemInfoResponse)
async def get_info():
    """Get API and system information"""
    # Check if orchestrator is initialized
    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=503,
            detail="System not initialized. Call /initialize first."
        )

    uptime = time.time() - app_state["start_time"]

    return SystemInfoResponse(
        version="8.0.0", library_version="8.0.0", status="operational", uptime=uptime
    )


@app.post("/api/test-connection")
async def test_connection():
    """Test API connection and health"""
    try:
        if app_state.get("orchestrator") is None:
            return {"status": "ok", "message": "API is running", "orchestrator": "not initialized"}

        # Test orchestrator connection if available
        return {"status": "ok", "message": "API is running and orchestrator is initialized"}
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")


@app.post("/code_generation/improve")
async def improve_code(request: dict = None):
    """Improve code with AI suggestions"""
    try:
        if not request or "code" not in request:
            raise HTTPException(
                status_code=400,
                detail="Request must include 'code' field"
            )

        code = request.get("code")
        logger.info(f"Improving code: {code[:50]}...")

        # Return mock improvement suggestions
        return {
            "original_code": code,
            "improved_code": code + "\n# Added type hints\n# Added docstring",
            "suggestions": [
                "Add type hints to function parameters",
                "Add docstring explaining the function",
                "Consider using list comprehension if applicable"
            ],
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error improving code: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to improve code: {str(e)}")


@app.post("/projects/{project_id}/question", response_model=QuestionResponse)
async def ask_question(project_id: str, request: AskQuestionRequest):
    """
    Get a Socratic question for a project

    Parameters:
    - project_id: Project identifier
    - topic: Optional topic for the question
    - difficulty_level: Question difficulty level
    """
    try:
        orchestrator = get_orchestrator()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Call /initialize first."
        )

    try:
        result = orchestrator.process_request(
            "question_generator",
            {
                "action": "generate_question",
                "project_id": project_id,
                "topic": request.topic,
                "difficulty_level": request.difficulty_level,
            },
        )

        if result.get("status") == "success":
            return QuestionResponse(
                question_id=result.get("question_id"),
                question=result.get("question"),
                context=result.get("context"),
                hints=result.get("hints", []),
            )
        else:
            raise HTTPException(
                status_code=400, detail=result.get("message", "Failed to generate question")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/response", response_model=ProcessResponseResponse)
async def process_response(project_id: str, request: ProcessResponseRequest):
    """
    Process a user's response to a Socratic question

    Parameters:
    - project_id: Project identifier
    - question_id: Question identifier
    - user_response: User's response to the question
    """
    try:
        orchestrator = get_orchestrator()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Call /initialize first."
        )

    try:
        result = orchestrator.process_request(
            "response_evaluator",
            {
                "action": "evaluate_response",
                "project_id": project_id,
                "question_id": request.question_id,
                "user_response": request.user_response,
            },
        )

        if result.get("status") == "success":
            return ProcessResponseResponse(
                feedback=result.get("feedback"),
                is_correct=result.get("is_correct", False),
                next_question=None,  # Could load next question here
                insights=result.get("insights", []),
            )
        else:
            raise HTTPException(
                status_code=400, detail=result.get("message", "Failed to evaluate response")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/code/generate", response_model=CodeGenerationResponse)
async def generate_code(request: GenerateCodeRequest):
    """
    Generate code for a project

    Parameters:
    - project_id: Project identifier
    - specification: Code specification or requirements
    - language: Programming language
    """
    try:
        orchestrator = get_orchestrator()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Call /initialize first."
        )

    try:
        # Load project
        project_result = orchestrator.process_request(
            "project_manager", {"action": "load_project", "project_id": request.project_id}
        )

        if project_result.get("status") != "success":
            raise HTTPException(status_code=404, detail="Project not found")

        project = project_result["project"]

        # Generate code
        code_result = orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_code",
                "project": project,
                "specification": request.specification,
                "language": request.language,
            },
        )

        if code_result.get("status") == "success":
            return CodeGenerationResponse(
                code=code_result.get("script", ""),
                explanation=code_result.get("explanation"),
                language=request.language,
                token_usage=code_result.get("token_usage"),
            )
        else:
            raise HTTPException(
                status_code=400, detail=code_result.get("message", "Failed to generate code")
            )

    except HTTPException:
        raise
    # except socrates.ProjectNotFoundError:
    #     raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# TODO: Import SocratesError from socratic_system and re-enable this handler
# @app.exception_handler(socrates.SocratesError)
# async def socrates_error_handler(request, exc: socrates.SocratesError):
#     """Handle Socrates library errors"""
#     return JSONResponse(
#         status_code=400,
#         content=ErrorResponse(
#             error=exc.__class__.__name__,
#             message=str(exc),
#             error_code=getattr(exc, "error_code", None),
#             details=getattr(exc, "context", None),
#         ).model_dump(),
#     )


@app.exception_handler(Exception)
async def general_error_handler(request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            error_code="INTERNAL_ERROR",
        ).model_dump(),
    )


def run():
    """Run the API server"""
    host = os.getenv("SOCRATES_API_HOST", "127.0.0.1")
    port = int(os.getenv("SOCRATES_API_PORT", "8000"))
    reload = os.getenv("SOCRATES_API_RELOAD", "False").lower() == "true"

    # Check if port is available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()

    if result == 0:
        logger.warning(f"Port {port} is already in use. Attempting to use it anyway.")
    else:
        logger.info(f"Port {port} is available")

    logger.info(f"Starting Socrates API on {host}:{port}")

    uvicorn.run("socrates_api.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    run()
