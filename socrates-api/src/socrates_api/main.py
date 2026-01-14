"""
Socrates API - FastAPI application for Socrates AI tutoring system

Provides REST endpoints for project management, Socratic questioning, and code generation.
"""

import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Body, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from slowapi.errors import RateLimitExceeded

from socrates_api.middleware.metrics import (
    add_metrics_middleware,
    get_metrics_summary,
    get_metrics_text,
)
from socrates_api.middleware.rate_limit import (
    initialize_limiter,
)
from socrates_api.middleware.security_headers import add_security_headers_middleware
from socratic_system.events import EventType
from socratic_system.exceptions import SocratesError
from socratic_system.orchestration.orchestrator import AgentOrchestrator

from .models import (
    AskQuestionRequest,
    CodeGenerationResponse,
    ErrorResponse,
    GenerateCodeRequest,
    GenerateCodeForProjectRequest,
    InitializeRequest,
    ProcessResponseRequest,
    ProcessResponseResponse,
    QuestionResponse,
    SystemInfoResponse,
)
from .routers import (
    analysis_router,
    analytics_router,
    auth_router,
    chat_sessions_router,
    code_generation_router,
    collab_router,
    collaboration_router,
    events_router,
    finalization_router,
    free_session_router,
    github_router,
    knowledge_management_router,
    knowledge_router,
    llm_router,
    nlu_router,
    notes_router,
    progress_router,
    projects_chat_router,
    projects_router,
    query_router,
    security_router,
    skills_router,
    subscription_router,
    system_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize rate limiter before app creation
_redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
limiter = initialize_limiter(_redis_url)  # Export for use in routers

# Global state
app_state = {
    "orchestrator": None,
    "start_time": time.time(),
    "event_listeners_registered": False,
    "limiter": limiter,
}


def get_orchestrator() -> AgentOrchestrator:
    """Dependency injection for orchestrator"""
    if app_state["orchestrator"] is None:
        raise RuntimeError("Orchestrator not initialized. Call /initialize first.")
    return app_state["orchestrator"]


def get_rate_limiter_for_app():
    """Get rate limiter instance from app state"""
    return app_state.get("limiter")


def conditional_rate_limit(limit_string: str):
    """
    Conditional rate limit decorator that applies limit if limiter is available.
    Falls back to no limit if limiter is not initialized.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter_for_app()
            if limiter:
                # Apply the rate limit
                limited_func = limiter.limit(limit_string)(func)
                return await limited_func(*args, **kwargs)
            else:
                # No rate limiting
                return await func(*args, **kwargs)

        return wrapper

    return decorator


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Socrates API server...")

    # Rate limiter initialized at module load time
    if app_state.get("limiter"):
        logger.info("Rate limiter is active")
    else:
        logger.warning("Rate limiting is disabled")

    # Auto-initialize orchestrator on startup
    # Note: API key can be provided via environment variable OR per-user via database
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            logger.info(f"ANTHROPIC_API_KEY is set ({api_key[:10]}...)")
        else:
            logger.info(
                "ANTHROPIC_API_KEY not set. Users will provide their own API keys via Settings > LLM > Anthropic"
            )

        # Create and initialize orchestrator
        # If no env API key, use a placeholder - actual keys will be fetched per-user from database
        logger.info("Creating AgentOrchestrator...")
        orchestrator = AgentOrchestrator(
            api_key_or_config=api_key or "placeholder-key-will-use-user-specific-keys"
        )
        logger.info("AgentOrchestrator created successfully")

        # Test connection only if we have an env API key
        if api_key:
            try:
                logger.info("Testing API connection with environment API key...")
                orchestrator.claude_client.test_connection()
                logger.info("Orchestrator initialized successfully with valid environment API key")
            except Exception as e:
                logger.warning(
                    f"Environment API key connection test failed: {type(e).__name__}: {str(e)[:100]}"
                )
                logger.info(
                    "Orchestrator initialized but will rely on per-user API keys from database"
                )
        else:
            logger.info(
                "No environment API key set. System will use per-user API keys from database."
            )

        # Setup event listeners
        logger.info("Setting up event listeners...")
        _setup_event_listeners(orchestrator)
        logger.info("Event listeners set up")

        # Store in global state
        logger.info("Storing orchestrator in global state...")
        app_state["orchestrator"] = orchestrator
        app_state["start_time"] = time.time()
        logger.info(f"Orchestrator stored. app_state['orchestrator'] = {app_state['orchestrator']}")

        logger.info("Socrates API orchestrator fully initialized and ready for per-user API keys")

    except Exception as e:
        logger.error(f"Failed to auto-initialize orchestrator on startup: {type(e).__name__}: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

    yield  # App is running

    # Shutdown
    logger.info("Shutting down Socrates API server...")
    # Close database connection
    from socrates_api.database import close_database

    close_database()


# Create FastAPI application with lifespan handler
app = FastAPI(
    title="Socrates API",
    description="REST API for Socrates AI tutoring system powered by Claude",
    version="8.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add security headers middleware
# Auto-detect environment: if ENVIRONMENT is not explicitly set and running on local machine, use development
environment = os.getenv("ENVIRONMENT")
if not environment:
    hostname = socket.gethostname()
    # Development detection: common patterns for local machines
    is_development = (
        hostname in ["localhost", "127.0.0.1"]
        or hostname.startswith("LAPTOP-")
        or hostname.startswith("DESKTOP-")
        or hostname.startswith("computer")
    )
    environment = "development" if is_development else "production"
else:
    environment = environment.lower()

add_security_headers_middleware(app, environment=environment)

# Add metrics middleware
add_metrics_middleware(app)

# Configure CORS based on environment
if environment == "production":
    # Production: Only allow specific origins
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "https://socrates.app"  # Default production origin
    ).split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins]
elif environment == "staging":
    # Staging: Allow staging domains
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "https://staging.socrates.app,https://socrates-staging.vercel.app"
    ).split(",")
    allowed_origins = [origin.strip() for origin in allowed_origins]
else:
    # Development: Allow localhost and common dev URLs
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    # Allow additional dev origins from environment variable
    dev_origins = os.getenv("ALLOWED_ORIGINS", "")
    if dev_origins:
        allowed_origins.extend([o.strip() for o in dev_origins.split(",")])

# Add CORS middleware with hardened configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "X-Testing-Mode"],
    expose_headers=["X-Process-Time", "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

logger.info(f"CORS configured for {environment} environment with origins: {allowed_origins}")


# Include API routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(collaboration_router)
app.include_router(collab_router)
app.include_router(code_generation_router)
app.include_router(knowledge_router)
app.include_router(llm_router)
app.include_router(projects_chat_router)
app.include_router(analysis_router)
app.include_router(security_router)
app.include_router(analytics_router)
app.include_router(github_router)
app.include_router(events_router)
app.include_router(notes_router)
app.include_router(finalization_router)
app.include_router(subscription_router)
app.include_router(query_router)
app.include_router(knowledge_management_router)
app.include_router(skills_router)
app.include_router(progress_router)
app.include_router(system_router)
app.include_router(nlu_router)
app.include_router(free_session_router)
app.include_router(chat_sessions_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Socrates API", "version": "8.0.0"}


@app.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint.

    Returns overall system status and component health.
    """
    orchestrator_ready = app_state.get("orchestrator") is not None
    limiter_ready = app_state.get("limiter") is not None

    overall_status = "healthy" if (orchestrator_ready and limiter_ready) else "degraded"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "components": {
            "orchestrator": "ready" if orchestrator_ready else "not_ready",
            "rate_limiter": "ready" if limiter_ready else "disabled",
            "api": "operational",
        },
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint.

    Returns comprehensive system status including database, cache, and service details.
    """
    from socrates_api.caching import get_cache
    from socratic_system.database.query_profiler import get_profiler

    try:
        cache = get_cache()
        cache_status = (await cache.get_stats()) if cache else {"status": "unavailable"}
    except Exception as e:
        cache_status = {"status": "error", "error": str(e)}

    try:
        profiler = get_profiler()
        profiler_stats = profiler.get_stats()
        slow_queries = profiler.get_slow_queries(min_slow_count=1)
    except Exception:
        profiler_stats = {}
        slow_queries = []

    orchestrator_ready = app_state.get("orchestrator") is not None
    limiter_ready = app_state.get("limiter") is not None

    overall_status = "healthy" if (orchestrator_ready and limiter_ready) else "degraded"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "uptime_seconds": time.time() - app_state.get("start_time", time.time()),
        "components": {
            "orchestrator": {
                "status": "ready" if orchestrator_ready else "not_ready",
                "api_key_configured": orchestrator_ready,
            },
            "rate_limiter": {
                "status": "ready" if limiter_ready else "disabled",
                "backend": "redis" if limiter_ready else "none",
            },
            "cache": cache_status,
            "api": {
                "status": "operational",
                "version": "8.0.0",
            },
        },
        "database_metrics": {
            "total_queries": len(profiler_stats),
            "slow_queries": len(slow_queries),
            "slowest_query_avg_ms": max(
                (q.get("avg_time_ms", 0) for q in profiler_stats.values()), default=0
            ),
        },
        "metrics": {
            "queries_tracked": len(profiler_stats),
            "cache_type": cache_status.get("type", "unknown"),
        },
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns metrics in Prometheus text format for scraping by monitoring systems.

    Example:
        GET /metrics
        http_requests_total{method="GET",endpoint="/health",status="200"} 1234
        http_request_duration_seconds_bucket{method="GET",endpoint="/health",status="200",le="0.01"} 100
    """
    from fastapi.responses import Response

    metrics_text = get_metrics_text()
    return Response(
        content=metrics_text,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.get("/metrics/summary", response_model=dict)
async def metrics_summary():
    """
    Get a summary of key metrics.

    Returns:
        Dictionary with high-level metric summaries
    """
    return get_metrics_summary()


@app.get("/metrics/queries")
async def query_metrics():
    """
    Get database query performance metrics.

    Returns query profiler statistics including:
    - Query execution counts
    - Average/min/max execution times
    - Slow query counts and percentages
    - Error counts per query

    Example:
        GET /metrics/queries
        {
            "get_project": {
                "count": 150,
                "avg_time_ms": 23.5,
                "min_time_ms": 5.2,
                "max_time_ms": 145.3,
                "total_time_ms": 3525.0,
                "slow_count": 3,
                "slow_percentage": 2.0,
                "error_count": 0,
                "last_executed_at": 1735152385.234
            },
            ...
        }
    """
    from socratic_system.database.query_profiler import get_profiler

    profiler = get_profiler()
    return profiler.get_stats()


@app.get("/metrics/queries/slow")
async def slow_query_metrics(min_count: int = 1):
    """
    Get list of queries with slow executions.

    Args:
        min_count: Minimum number of slow executions to include (default: 1)

    Returns:
        List of slow queries sorted by slow execution count
    """
    from socratic_system.database.query_profiler import get_profiler

    profiler = get_profiler()
    return profiler.get_slow_queries(min_slow_count=min_count)


@app.get("/metrics/queries/slowest")
async def slowest_query_metrics(limit: int = 10):
    """
    Get slowest queries by average execution time.

    Args:
        limit: Maximum number of queries to return (default: 10)

    Returns:
        List of slowest queries sorted by average execution time
    """
    from socratic_system.database.query_profiler import get_profiler

    profiler = get_profiler()
    return profiler.get_slowest_queries(limit=limit)


@app.post("/initialize", response_model=SystemInfoResponse)
async def initialize(request: Optional[InitializeRequest] = Body(None)):
    """
    Initialize the Socrates API with configuration

    Parameters:
    - api_key: Claude API key (optional, will use ANTHROPIC_API_KEY env var if not provided)

    Note: API key can be provided here OR users can set it in Settings > LLM > Anthropic
    """
    try:
        # Get API key from request body or environment variable
        api_key = None
        if request and request.api_key:
            api_key = request.api_key
        else:
            # Fall back to environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")

        # If no API key provided, that's okay - users will provide their own via UI
        if api_key:
            logger.info("Initializing with provided API key")

            # Create orchestrator with provided API key
            orchestrator = AgentOrchestrator(api_key_or_config=api_key)

            # Test connection
            try:
                orchestrator.claude_client.test_connection()
                logger.info("API key connection successful")
            except Exception as e:
                logger.warning(f"API key connection test failed: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"API key is invalid: {str(e)}"
                )
        else:
            logger.info("No API key provided in request. Using placeholder for per-user keys from database")

            # Create orchestrator with placeholder - will use per-user keys
            orchestrator = AgentOrchestrator(
                api_key_or_config="placeholder-key-will-use-user-specific-keys"
            )

        # Setup event listeners
        _setup_event_listeners(orchestrator)

        # Store in global state
        app_state["orchestrator"] = orchestrator
        app_state["start_time"] = time.time()

        logger.info("Socrates API initialized successfully")

        return SystemInfoResponse(
            version="8.0.0", library_version="8.0.0", status="operational", uptime=0.0
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info", response_model=SystemInfoResponse)
async def get_info():
    """Get API and system information"""
    # Check if orchestrator is initialized
    if app_state.get("orchestrator") is None:
        raise HTTPException(
            status_code=503, detail="System not initialized. Call /initialize first."
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
            raise HTTPException(status_code=400, detail="Request must include 'code' field")

        code = request.get("code")
        logger.info(f"Improving code: {code[:50]}...")

        # Return mock improvement suggestions
        return {
            "original_code": code,
            "improved_code": code + "\n# Added type hints\n# Added docstring",
            "suggestions": [
                "Add type hints to function parameters",
                "Add docstring explaining the function",
                "Consider using list comprehension if applicable",
            ],
            "status": "success",
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
            detail="System not initialized. Call /initialize first.",
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
            detail="System not initialized. Call /initialize first.",
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
    Generate code for a project (legacy endpoint)

    Parameters:
    - project_id: Project identifier (in body)
    - specification: Code specification or requirements
    - language: Programming language
    """
    try:
        orchestrator = get_orchestrator()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not initialized. Call /initialize first.",
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
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(SocratesError)
async def socrates_error_handler(request: Request, exc: SocratesError):
    """Handle Socrates library errors"""
    logger.warning(f"SocratesError in {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc),
            error_code=getattr(exc, "error_code", None),
            details=getattr(exc, "context", None),
        ).model_dump(),
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded for {request.client.host}: {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "TooManyRequests",
            "message": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
        },
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
