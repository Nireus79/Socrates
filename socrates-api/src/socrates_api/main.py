"""
Socrates API - FastAPI application for Socrates AI tutoring system

Provides REST endpoints for project management, Socratic questioning, and code generation.
"""

import os
import logging
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import socrates

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
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
app_state = {"orchestrator": None, "start_time": time.time(), "event_listeners_registered": False}


def get_orchestrator() -> socrates.AgentOrchestrator:
    """Dependency injection for orchestrator"""
    if app_state["orchestrator"] is None:
        raise RuntimeError("Orchestrator not initialized. Call /initialize first.")
    return app_state["orchestrator"]


def _setup_event_listeners(orchestrator: socrates.AgentOrchestrator):
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
    orchestrator.event_emitter.on(socrates.EventType.PROJECT_CREATED, on_project_created)
    orchestrator.event_emitter.on(socrates.EventType.CODE_GENERATED, on_code_generated)
    orchestrator.event_emitter.on(socrates.EventType.AGENT_ERROR, on_agent_error)

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


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Socrates API server...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Socrates API server...")


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "initialized": app_state["orchestrator"] is not None}


@app.post("/initialize", response_model=SystemInfoResponse)
async def initialize(api_key: Optional[str] = None):
    """
    Initialize the Socrates API with configuration

    Parameters:
    - api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
    """
    try:
        if api_key is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError("API key required. Set ANTHROPIC_API_KEY or pass api_key parameter.")

        # Create configuration
        data_dir = os.getenv("SOCRATES_DATA_DIR", None)
        config_builder = socrates.ConfigBuilder(api_key)

        if data_dir:
            config_builder = config_builder.with_data_dir(Path(data_dir))

        config = config_builder.build()

        # Create orchestrator
        orchestrator = socrates.create_orchestrator(config)

        # Test connection
        orchestrator.claude_client.test_connection()

        # Setup event listeners
        _setup_event_listeners(orchestrator)

        # Store in global state
        app_state["orchestrator"] = orchestrator
        app_state["start_time"] = time.time()

        logger.info("Socrates API initialized successfully")

        return SystemInfoResponse(
            version="8.0.0", library_version=socrates.__version__, status="operational", uptime=0.0
        )

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", response_model=SystemInfoResponse)
async def get_info():
    """Get API and system information"""
    uptime = time.time() - app_state["start_time"]

    return SystemInfoResponse(
        version="8.0.0", library_version=socrates.__version__, status="operational", uptime=uptime
    )


@app.post("/projects", response_model=ProjectResponse)
async def create_project(request: CreateProjectRequest):
    """
    Create a new project

    Parameters:
    - name: Project name
    - owner: Project owner username
    - description: Optional project description
    """
    orchestrator = get_orchestrator()

    try:
        result = orchestrator.process_request(
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
            return ProjectResponse(
                project_id=project.project_id,
                name=project.name,
                owner=project.owner,
                description=project.description,
                phase=project.phase,
                created_at=project.created_at,
                updated_at=project.updated_at,
                is_archived=project.is_archived,
            )
        else:
            raise HTTPException(
                status_code=400, detail=result.get("message", "Failed to create project")
            )

    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects", response_model=ListProjectsResponse)
async def list_projects(owner: Optional[str] = None):
    """
    List projects

    Parameters:
    - owner: Optional filter by owner
    """
    orchestrator = get_orchestrator()

    try:
        result = orchestrator.process_request(
            "project_manager", {"action": "list_projects", "owner": owner}
        )

        projects = result.get("projects", [])
        project_responses = [
            ProjectResponse(
                project_id=p["project_id"],
                name=p["name"],
                owner=p["owner"],
                description=p.get("description"),
                phase=p["phase"],
                created_at=p["created_at"],
                updated_at=p["updated_at"],
                is_archived=p.get("is_archived", False),
            )
            for p in projects
        ]

        return ListProjectsResponse(projects=project_responses, total=len(project_responses))

    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/question", response_model=QuestionResponse)
async def ask_question(project_id: str, request: AskQuestionRequest):
    """
    Get a Socratic question for a project

    Parameters:
    - project_id: Project identifier
    - topic: Optional topic for the question
    - difficulty_level: Question difficulty level
    """
    orchestrator = get_orchestrator()

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

    except socrates.ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
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
    orchestrator = get_orchestrator()

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

    except socrates.ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
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
    orchestrator = get_orchestrator()

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

    except socrates.ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project not found: {request.project_id}")
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(socrates.SocratesError)
async def socrates_error_handler(request, exc: socrates.SocratesError):
    """Handle Socrates library errors"""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc),
            error_code=getattr(exc, "error_code", None),
            details=getattr(exc, "context", None),
        ).model_dump(),
    )


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

    logger.info(f"Starting Socrates API on {host}:{port}")

    uvicorn.run("socrates_api.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    run()
