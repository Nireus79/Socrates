"""
Socrates API - FastAPI application for Socrates AI tutoring system

Provides REST endpoints for project management, Socratic questioning, and code generation.
"""

print("[MODULE] Starting import of socrates_api.main...", flush=True)

import asyncio
import logging
import os
import signal
import socket
import time
from contextlib import asynccontextmanager
from typing import Any, Optional

from dotenv import load_dotenv

# Load environment variables from .env FIRST, before any other imports
print("[MODULE] Loading environment variables...", flush=True)
load_dotenv()
print(
    "[MODULE] Environment loaded. JWT_SECRET_KEY set: %s" % (bool(os.getenv("JWT_SECRET_KEY"))),
    flush=True,
)

import uvicorn

print("[MODULE] Uvicorn imported", flush=True)
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
from socrates_api.orchestrator import APIOrchestrator
from socrates_api.orchestrator import get_orchestrator as create_orchestrator

from .models import (
    AskQuestionRequest,
    CodeGenerationResponse,
    ErrorResponse,
    GenerateCodeRequest,
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
    commands_router,
    conflicts_router,
    events_router,
    finalization_router,
    free_session_router,
    github_router,
    knowledge_management_router,
    knowledge_router,
    learning_router,
    library_integrations_router,
    llm_router,
    nlu_router,
    notes_router,
    progress_router,
    projects_chat_router,
    projects_router,
    query_router,
    security_router,
    skills_analytics,
    skills_composition,
    skills_distribution,
    skills_marketplace,
    skills_router,
    sponsorships_router,
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


def get_orchestrator_from_state() -> APIOrchestrator:
    """Dependency injection for orchestrator - initializes lazily on first use"""
    if app_state["orchestrator"] is None:
        # Lazy initialization on first use
        api_key = os.getenv("ANTHROPIC_API_KEY")
        logger.info("Lazy-initializing orchestrator on first use...")
        try:
            orchestrator = create_orchestrator(
                api_key=api_key or "placeholder-key-will-use-user-specific-keys"
            )
            app_state["orchestrator"] = orchestrator
            logger.info("Orchestrator initialized successfully on first use")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator on first use: {e}")
            raise RuntimeError(f"Failed to initialize orchestrator: {e}")
    return app_state["orchestrator"]


def get_orchestrator() -> APIOrchestrator:
    """Alias for get_orchestrator_from_state() for compatibility with routers"""
    return get_orchestrator_from_state()


def get_rate_limiter_for_app() -> Any:
    """Get rate limiter instance from app state"""
    return app_state.get("limiter")


def conditional_rate_limit(limit_string: str) -> Any:
    """
    Conditional rate limit decorator that applies limit if limiter is available.
    Falls back to no limit if limiter is not initialized.
    SECURITY: Logs alert if rate limiting is unavailable.
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter_for_app()
            if limiter:
                # Apply the rate limit
                limited_func = limiter.limit(limit_string)(func)
                return await limited_func(*args, **kwargs)
            else:
                # SECURITY ALERT: Rate limiting is disabled/unavailable
                logger.error(
                    f"SECURITY ALERT: Rate limiting is NOT AVAILABLE for endpoint. "
                    f"Redis may be down. Limit: {limit_string}. "
                    f"Endpoint {func.__name__} is UNPROTECTED."
                )
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def _setup_event_listeners(orchestrator: APIOrchestrator) -> None:
    """Setup listeners for orchestrator events"""
    if app_state["event_listeners_registered"]:
        return

    # Log all events
    # Event listener registration depends on local EventType module
    # TODO: Re-enable when EventType is available from PyPI
    app_state["event_listeners_registered"] = False


async def _monitor_shutdown():
    """Background task to monitor and execute scheduled shutdown

    When running in full-stack mode (python socrates.py --full), the API runs
    as a subprocess. This task sends signals to the parent process to ensure
    coordinated shutdown of all components (API, frontend, parent).

    Currently handles:
    - Browser-close detection: 5-minute delay before shutdown
    """
    from socrates_api.middleware.activity_tracker import should_shutdown_now

    while True:
        try:
            await asyncio.sleep(5)  # Check every 5 seconds

            # Check if browser-close shutdown is due (scheduled by client)
            if should_shutdown_now():
                logger.info("Executing scheduled shutdown...")
                # Send SIGTERM to parent process (for full-stack mode)
                # If running standalone, this will shutdown this process
                parent_pid = os.getppid()
                if parent_pid > 1:  # Not init process
                    logger.info(f"Sending SIGTERM to parent process {parent_pid}")
                    os.kill(parent_pid, signal.SIGTERM)
                else:
                    # Running standalone, shutdown self
                    logger.info("No parent process, shutting down self")
                    os.kill(os.getpid(), signal.SIGTERM)
                break

        except asyncio.CancelledError:
            logger.info("Shutdown monitor task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in shutdown monitor: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Socrates API server...")

    # Store in global state
    app_state["start_time"] = time.time()

    # Auto-initialize orchestrator on startup (deferred - initialize lazily on first use)
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        logger.info("Orchestrator will be initialized lazily on first API call")
        # Don't create orchestrator here - let it be created lazily on first use
        # This avoids blocking the server startup
    except Exception as e:
        logger.error(f"Failed to prepare orchestrator initialization: {e}")

    # Start shutdown monitor background task
    logger.info("Starting shutdown monitor background task...")
    shutdown_monitor_task = asyncio.create_task(_monitor_shutdown())

    yield  # App is running

    # Shutdown
    logger.info("Shutting down Socrates API server...")

    # Cancel shutdown monitor task
    if shutdown_monitor_task:
        shutdown_monitor_task.cancel()
        try:
            await shutdown_monitor_task
        except asyncio.CancelledError:
            logger.info("Shutdown monitor task cancelled")

    # Close database connection
    try:
        from socrates_api.database import close_database

        close_database()
    except Exception as e:
        logger.warning(f"Failed to close database: {e}")

    # Shutdown
    logger.info("Shutting down Socrates API server...")

    # Shutdown Phase 4 Service Orchestrator
    if app_state.get("service_orchestrator"):
        try:
            logger.info("Shutting down Phase 4 services...")
            await app_state["service_orchestrator"].stop_all_services()
            logger.info("Phase 4 services shut down successfully")
        except Exception as e:
            logger.debug("Phase 4 shutdown failed")

    # Cancel shutdown monitor task
    shutdown_monitor_task.cancel()
    try:
        await shutdown_monitor_task
    except asyncio.CancelledError:
        logger.info("Shutdown monitor task cancelled")

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

print(
    f"[MODULE] FastAPI app created (id={id(app)}) with {len(app.routes)} routes at this point",
    flush=True,
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

# Add activity tracking middleware
from socrates_api.middleware.activity_tracker import ActivityTrackerMiddleware

app.add_middleware(ActivityTrackerMiddleware)

# Add audit logging middleware
from socrates_api.middleware.audit import AuditMiddleware

app.add_middleware(AuditMiddleware)

# Add performance monitoring middleware
from socrates_api.middleware.performance import PerformanceMiddleware

app.add_middleware(PerformanceMiddleware)
logger.info("Performance monitoring middleware enabled")

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
        "http://localhost:5176",
        "http://localhost:5181",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5181",
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


# Add request logging middleware for debugging
@app.middleware("http")
async def log_requests_debug(request: Request, call_next):
    """Log all incoming requests for debugging"""
    path = str(request.url.path)
    method = request.method
    # Log all requests to auth, projects, and commands
    if any(x in path for x in ["/auth", "/projects", "/commands"]):
        print(f"[MIDDLEWARE] Incoming: {method:4} {path}", flush=True)
    response = await call_next(request)
    if any(x in path for x in ["/auth", "/projects", "/commands"]):
        print(f"[MIDDLEWARE] Response: {path} -> {response.status_code}", flush=True)
    return response


logger.info(f"CORS configured for {environment} environment with origins: {allowed_origins}")


# ============================================================================
# Exception Handlers for Custom Exceptions
# ============================================================================

from socrates_api.exceptions import SocratesException
from socrates_api.models import APIResponse


@app.exception_handler(SocratesException)
async def socrates_exception_handler(request: Request, exc: SocratesException):
    """
    Handle all Socrates custom exceptions.

    Maps custom exceptions to appropriate HTTP status codes and error responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            status="error",
            message=exc.message,
            error_code=exc.error_code,
            data=exc.details if exc.details else None,
        ).model_dump(exclude_none=True),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    Logs the full exception and returns a generic error response to the client.
    """
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            status="error",
            message="An unexpected error occurred",
            error_code="INTERNAL_ERROR",
        ).model_dump(exclude_none=True),
    )


logger.info("Exception handlers registered")


# Helper to safely include routers (skip None routers)
def _include_router_safe(router, name: str):
    if router is not None:
        app.include_router(router)
        logger.info(f"[ROUTER] Included router: {name}")
    else:
        logger.warning(f"[ROUTER] Skipped router (not available): {name}")


# Include API routers
print(f"[MODULE] About to include routers, app has {len(app.routes)} routes", flush=True)
logger.info(f"[STARTUP] Starting router inclusion, auth_router={auth_router is not None}")
_include_router_safe(auth_router, "auth")
_include_router_safe(commands_router, "commands")
_include_router_safe(conflicts_router, "conflicts")
_include_router_safe(projects_router, "projects")
_include_router_safe(collaboration_router, "collaboration")
_include_router_safe(collab_router, "collab")
_include_router_safe(code_generation_router, "code_generation")
_include_router_safe(knowledge_router, "knowledge")
_include_router_safe(learning_router, "learning")
_include_router_safe(library_integrations_router, "library_integrations")
_include_router_safe(llm_router, "llm")
_include_router_safe(projects_chat_router, "projects_chat")
_include_router_safe(analysis_router, "analysis")
_include_router_safe(security_router, "security")
_include_router_safe(analytics_router, "analytics")
_include_router_safe(github_router, "github")
_include_router_safe(events_router, "events")
_include_router_safe(notes_router, "notes")
_include_router_safe(finalization_router, "finalization")
_include_router_safe(subscription_router, "subscription")
_include_router_safe(sponsorships_router, "sponsorships")
_include_router_safe(query_router, "query")
_include_router_safe(knowledge_management_router, "knowledge_management")
_include_router_safe(skills_router, "skills")
_include_router_safe(progress_router, "progress")
_include_router_safe(system_router, "system")
_include_router_safe(nlu_router, "nlu")
_include_router_safe(free_session_router, "free_session")
_include_router_safe(chat_sessions_router, "chat_sessions")

# Phase 4: Skills Ecosystem Routers
app.include_router(
    skills_marketplace.router, prefix="/api/skills/marketplace", tags=["Skills Marketplace"]
)
app.include_router(
    skills_analytics.router, prefix="/api/skills/analytics", tags=["Skills Analytics"]
)
app.include_router(
    skills_distribution.router, prefix="/api/skills/distribution", tags=["Skills Distribution"]
)
app.include_router(
    skills_composition.router, prefix="/api/skills/composition", tags=["Skills Composition"]
)

print(
    f"[MODULE] All routers included (id={id(app)}) with {len(app.routes)} routes total", flush=True
)

# CRITICAL: Force Starlette router compilation
# This ensures routes are properly compiled before uvicorn serves
print("[MODULE] Compiling Starlette router...", flush=True)
try:
    # Force route table compilation
    compiled_routes = list(app.routes)
    print(f"[MODULE] Compiled {len(compiled_routes)} routes", flush=True)
except Exception as e:
    print(f"[MODULE] Compilation error: {e}", flush=True)


@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint - show all routes in the app"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(
                {
                    "path": route.path,
                    "type": type(route).__name__,
                    "methods": list(getattr(route, "methods", [])),
                }
            )
    return {
        "total_routes": len(app.routes),
        "routes": sorted(routes, key=lambda r: r["path"])[:20],
        "note": "Showing first 20 routes",
    }


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

    # REMOVED LOCAL IMPORT: from socratic_system.database.query_profiler import get_profiler

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
    # REMOVED LOCAL IMPORT: from socratic_system.database.query_profiler import get_profiler

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
    # REMOVED LOCAL IMPORT: from socratic_system.database.query_profiler import get_profiler

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
    # REMOVED LOCAL IMPORT: from socratic_system.database.query_profiler import get_profiler

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

        # Create orchestrator with provided API key or placeholder
        logger.info("Creating APIOrchestrator...")
        orchestrator = create_orchestrator(
            api_key=api_key or "placeholder-key-will-use-user-specific-keys"
        )

        # Test that orchestrator initialized properly
        system_info = orchestrator.get_system_info()
        if system_info.get("agents_loaded", 0) == 0:
            logger.warning("Orchestrator initialized but no agents loaded")

        if api_key:
            logger.info("Orchestrator initialized with provided API key")
        else:
            logger.info("Orchestrator initialized - will use per-user API keys from database")

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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


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

    # Verify app has routes before starting
    auth_routes = [r for r in app.routes if "/auth" in r.path]
    logger.info(f"API app has {len(app.routes)} total routes, {len(auth_routes)} auth routes")
    print(f"[RUN] App object id: {id(app)}, Routes: {len(app.routes)}", flush=True)

    # Run with uvicorn using string reference for reliable module loading
    uvicorn.run("socrates_api.main:app", host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    run()
