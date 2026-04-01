"""
Conflicts API Router

Provides endpoints for conflict detection and resolution across projects.
Integrates with the socratic-conflict library for multi-agent conflict detection.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Use PyPI library directly
from socratic_conflict import ConflictDetector
from socrates_api.utils import IDGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])


# ============================================================================
# MODELS
# ============================================================================


class ConflictDetectionRequest(BaseModel):
    """Request for conflict detection"""

    project_id: str = Field(..., description="Project ID")
    new_values: Dict[str, Any] = Field(..., description="New values to check for conflicts")
    fields_to_check: Optional[List[str]] = Field(
        None, description="Specific fields to check (all if not provided)"
    )
    include_resolution: bool = Field(False, description="Include suggested resolutions")


class ConflictInfo(BaseModel):
    """Conflict information"""

    conflict_type: str
    field_name: str
    existing_value: Any
    new_value: Any
    severity: str  # "low", "medium", "high", "critical"
    description: str
    suggested_resolution: Optional[str] = None
    conflict_id: Optional[str] = None  # FIX #9: Unique identifier for tracking


class ConflictDetectionResponse(BaseModel):
    """Response from conflict detection"""

    status: str
    conflicts: List[ConflictInfo] = Field(default_factory=list)
    has_conflicts: bool
    total_conflicts: int
    message: Optional[str] = None


class ConflictHistoryEntry(BaseModel):
    """Entry in conflict history"""

    timestamp: str
    project_id: str
    conflict_type: str
    resolution: str
    resolved_by: Optional[str] = None


class ConflictResolutionRequest(BaseModel):
    """Request for conflict resolution"""

    project_id: str
    conflict_type: str
    resolution_strategy: str  # "existing", "new", "merge", "custom"
    resolution_details: Optional[Dict[str, Any]] = None


class ConflictResolutionResponse(BaseModel):
    """Response from conflict resolution"""

    status: str
    result: Optional[Dict[str, Any]] = None
    message: str


# ============================================================================
# STATE
# ============================================================================

_conflict_detector: Optional[ConflictDetector] = None


def get_conflict_detector() -> ConflictDetector:
    """Get or initialize conflict detector"""
    global _conflict_detector
    if _conflict_detector is None:
        _conflict_detector = ConflictDetector()
    return _conflict_detector


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/detect", response_model=ConflictDetectionResponse)
def detect_conflicts(request: ConflictDetectionRequest) -> ConflictDetectionResponse:
    """
    Detect conflicts in project updates.

    Analyzes proposed changes against existing project values to identify:
    - Data conflicts (contradictory values)
    - Decision conflicts (incompatible proposals)
    - Workflow conflicts (incompatible workflow steps)

    Request Body:
    - project_id: Project identifier
    - new_values: Dictionary of new values to check
    - fields_to_check: Optional list of specific fields (checks all if omitted)
    - include_resolution: Whether to include suggested resolutions

    Returns:
    - List of detected conflicts with severity and descriptions
    - Suggested resolutions if requested
    """
    try:
        from socrates_api.database import get_database
        db = get_database()

        # Load project from database
        project = db.load_project(request.project_id)
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{request.project_id}' not found"
            )

        detector = get_conflict_detector()

        if detector.detector is None:
            return ConflictDetectionResponse(
                status="unavailable",
                conflicts=[],
                has_conflicts=False,
                total_conflicts=0,
                message="Conflict detection is not available (socratic-conflict not installed)",
            )

        # Detect conflicts between new values and existing project specs
        detected_conflicts: List[ConflictInfo] = []

        # Define fields to check
        fields_to_check = request.fields_to_check or [
            "goals", "requirements", "tech_stack", "constraints"
        ]

        # Get existing project values
        existing_data = {
            "goals": project.goals or [],
            "requirements": project.requirements or [],
            "tech_stack": project.tech_stack or [],
            "constraints": project.constraints or [],
        }

        # Check each field for conflicts
        for field_name in fields_to_check:
            if field_name not in request.new_values:
                continue

            existing_value = existing_data.get(field_name)
            new_value = request.new_values[field_name]

            # Skip if values are identical
            if existing_value == new_value:
                continue

            # Determine conflict type based on field
            conflict_type = "data_conflict"
            if field_name == "goals":
                conflict_type = "goal_conflict"
            elif field_name == "tech_stack":
                conflict_type = "tech_conflict"
            elif field_name == "requirements":
                conflict_type = "requirement_conflict"
            elif field_name == "constraints":
                conflict_type = "constraint_conflict"

            # Determine severity level
            severity = "high" if field_name in ["goals", "tech_stack"] else "medium"

            # Create conflict info
            conflict = ConflictInfo(
                conflict_type=conflict_type,
                field_name=field_name,
                existing_value=existing_value,
                new_value=new_value,
                severity=severity,
                description=f"{field_name.title()}: {str(existing_value)[:50]} vs {str(new_value)[:50]}",
                suggested_resolution=f"Review both values and choose which better fits your project goals" if request.include_resolution else None
            )

            detected_conflicts.append(conflict)

            # FIX #9: Save conflict to database for history tracking with proper ID
            try:
                conflict_id = IDGenerator.generate_id("conflict")
                db.save_conflict(
                    project_id=request.project_id,
                    conflict_id=conflict_id,
                    conflict_type=conflict_type,
                    title=f"{field_name.title()} Conflict",
                    description=conflict.description,
                    severity=severity,
                    related_agents=[],
                    context={
                        "field": field_name,
                        "existing": str(existing_value),
                        "new": str(new_value),
                    }
                )
                # Store conflict_id on conflict object for client reference
                conflict.conflict_id = conflict_id
            except Exception as e:
                logger.warning(f"Failed to save conflict to database: {e}")

        logger.info(f"Detected {len(detected_conflicts)} conflict(s) for project {request.project_id}")

        return ConflictDetectionResponse(
            status="success",
            conflicts=detected_conflicts,
            has_conflicts=len(detected_conflicts) > 0,
            total_conflicts=len(detected_conflicts),
            message=f"Found {len(detected_conflicts)} conflict(s)" if detected_conflicts else "No conflicts detected",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Conflict detection failed. Please try again.")


@router.post("/resolve", response_model=ConflictResolutionResponse)
def resolve_conflict(request: ConflictResolutionRequest) -> ConflictResolutionResponse:
    """
    Resolve a detected conflict.

    Applies a resolution strategy to an existing conflict:
    - 'existing': Keep existing value
    - 'new': Use new value
    - 'merge': Attempt to merge/combine values
    - 'custom': Apply custom resolution logic

    Request Body:
    - project_id: Project identifier
    - conflict_type: Type of conflict to resolve
    - resolution_strategy: Strategy to apply
    - resolution_details: Additional details for custom strategies

    Returns:
    - Resolution result and status
    """
    try:
        from socrates_api.database import get_database
        from datetime import datetime, timezone

        detector = get_conflict_detector()

        if detector.detector is None:
            raise HTTPException(
                status_code=503,
                detail="Conflict resolution is not available",
            )

        db = get_database()
        logger.info(
            f"Resolving {request.conflict_type} conflict for project {request.project_id} "
            f"using strategy: {request.resolution_strategy}"
        )

        # FIX #9 & #10: Properly save resolution and create decision with versioning
        # FIX #10: Use atomic transaction for resolution to ensure consistency
        resolution_id = IDGenerator.generate_id("resolution")
        decision_id = IDGenerator.generate_id("decision")
        now = datetime.now(timezone.utc).isoformat()

        # Get the most recent conflict of this type for this project
        conflicts = db.get_conflict_history(request.project_id, conflict_type=request.conflict_type, limit=1)
        if not conflicts:
            raise HTTPException(
                status_code=404,
                detail=f"No unresolved conflict found for type {request.conflict_type}"
            )

        conflict_id = conflicts[0]["conflict_id"]

        # FIX #10: Use atomic transaction for all resolution operations
        try:
            with db.transaction():
                # Save resolution strategy
                db.save_resolution(
                    resolution_id=resolution_id,
                    conflict_id=conflict_id,
                    strategy=request.resolution_strategy,
                    confidence=0.8,  # Default confidence
                    rationale=f"Applied {request.resolution_strategy} strategy",
                    metadata=request.resolution_details or {}
                )

                # Save decision (versioning for multiple resolutions of same conflict)
                existing_decisions = db.get_conflict_decisions(conflict_id)
                next_version = len(existing_decisions) + 1

                db.save_decision(
                    decision_id=decision_id,
                    conflict_id=conflict_id,
                    resolution_id=resolution_id,
                    decided_by="system",  # Could be user_id from context
                    rationale=f"Resolved using {request.resolution_strategy}",
                    version=next_version,
                    metadata=request.resolution_details or {}
                )
                logger.debug(f"Conflict {conflict_id} resolution committed atomically")
        except Exception as e:
            logger.error(f"Atomic conflict resolution failed, rolled back: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to save conflict resolution. Please try again."
            )

        result = {
            "strategy_applied": request.resolution_strategy,
            "conflict_type": request.conflict_type,
            "conflict_id": conflict_id,
            "resolution_id": resolution_id,
            "decision_id": decision_id,
            "decision_version": next_version,
            "timestamp": now,
        }

        return ConflictResolutionResponse(
            status="success",
            result=result,
            message=f"Conflict resolved using {request.resolution_strategy} strategy (v{next_version})",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error resolving conflict", exc_info=True)
        return ConflictResolutionResponse(
            status="error",
            message=str(e),
        )


@router.get("/history/{project_id}")
def get_conflict_history(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
    conflict_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get conflict history for a project.

    Retrieves a history of detected and resolved conflicts for a project.

    Path Parameters:
    - project_id: Project identifier

    Query Parameters:
    - limit: Maximum number of entries to return (default: 50, max: 500)
    - conflict_type: Filter by conflict type (optional)

    Returns:
    - List of conflict history entries with resolutions
    """
    try:
        from socrates_api.database import get_database

        db = get_database()
        logger.info(f"Retrieving conflict history for project {project_id}, limit={limit}")

        # Get conflict history from database
        entries = db.get_conflict_history(project_id, conflict_type=conflict_type, limit=limit)

        # Enrich each entry with resolutions and decisions
        enriched_entries = []
        for conflict in entries:
            resolutions = db.get_conflict_resolutions(conflict["conflict_id"])
            decisions = db.get_conflict_decisions(conflict["conflict_id"])

            enriched_entries.append({
                **conflict,
                "resolutions": resolutions,
                "decisions": decisions,
                "is_resolved": len(decisions) > 0,
            })

        return {
            "status": "success",
            "project_id": project_id,
            "total_entries": len(enriched_entries),
            "conflict_type_filter": conflict_type,
            "entries": enriched_entries,
        }

    except Exception as e:
        logger.debug("Error retrieving conflict history", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/analysis/{project_id}")
def analyze_project_conflicts(project_id: str) -> Dict[str, Any]:
    """
    Analyze conflict patterns in a project.

    Provides insights into conflict types, frequency, and resolution patterns.

    Path Parameters:
    - project_id: Project identifier

    Returns:
    - Conflict analysis including statistics and patterns
    """
    try:
        from socrates_api.database import get_database

        db = get_database()
        logger.info(f"Analyzing conflicts for project {project_id}")

        # Get detailed statistics
        stats = db.get_conflict_statistics(project_id)

        # Get recent conflicts for pattern analysis
        recent_conflicts = db.get_conflict_history(project_id, limit=100)

        # Generate recommendations based on patterns
        recommendations = []
        if stats.get("total_conflicts", 0) > 5:
            recommendations.append(
                "High conflict frequency detected. Review project specifications and ensure clarity."
            )

        high_severity = stats.get("severities", {}).get("critical", 0) or stats.get("severities", {}).get("high", 0)
        if high_severity > 0:
            recommendations.append(
                f"Found {high_severity} high/critical conflicts. Prioritize resolution of these issues."
            )

        if stats.get("resolution_rate", 0) < 0.5:
            recommendations.append(
                "Low resolution rate. Implement strategies to address unresolved conflicts."
            )

        # Identify most common conflict type
        most_common_type = None
        max_count = 0
        for conflict_type, count in stats.get("conflict_types", {}).items():
            if count > max_count:
                max_count = count
                most_common_type = conflict_type

        analysis = {
            "project_id": project_id,
            "status": "success",
            "statistics": stats,
            "most_common_conflict_type": most_common_type,
            "most_used_strategy": max(
                stats.get("strategies_used", {}).items(), key=lambda x: x[1]
            )[0] if stats.get("strategies_used") else None,
            "recent_conflicts_count": len(recent_conflicts),
            "recommendations": recommendations,
        }

        return analysis

    except Exception as e:
        logger.debug("Error analyzing conflicts", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/status")
def get_conflict_system_status() -> Dict[str, Any]:
    """
    Get status of the conflict resolution system.

    Returns:
    - System status and capabilities
    """
    try:
        detector = get_conflict_detector()

        return {
            "status": "operational",
            "conflict_detector_available": detector.detector is not None,
            "capabilities": [
                "data_conflict_detection",
                "decision_conflict_detection",
                "workflow_conflict_detection",
                "conflict_resolution",
                "history_tracking",
                "pattern_analysis",
            ],
            "supported_strategies": [
                "existing",
                "new",
                "merge",
                "custom",
            ],
        }

    except Exception as e:
        logger.debug("Error getting conflict system status", exc_info=True)
        return {
            "status": "error",
            "conflict_detector_available": False,
            "message": str(e),
        }


@router.get("/{project_id}/conflicts/{conflict_id}")
def get_conflict_details(project_id: str, conflict_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific conflict.

    Path Parameters:
    - project_id: Project identifier
    - conflict_id: Conflict identifier

    Returns:
    - Complete conflict details with all resolutions and decisions
    """
    try:
        from socrates_api.database import get_database

        db = get_database()
        logger.info(f"Retrieving details for conflict {conflict_id} in project {project_id}")

        # Get the specific conflict
        history = db.get_conflict_history(project_id, limit=1000)
        conflict = next((c for c in history if c["conflict_id"] == conflict_id), None)

        if not conflict:
            raise HTTPException(status_code=404, detail="Conflict not found")

        # Get resolutions and decisions
        resolutions = db.get_conflict_resolutions(conflict_id)
        decisions = db.get_conflict_decisions(conflict_id)

        return {
            "status": "success",
            "conflict": conflict,
            "resolutions": resolutions,
            "decisions": decisions,
            "is_resolved": len(decisions) > 0,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error getting conflict details", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")


@router.get("/{project_id}/conflicts/{conflict_id}/decisions/versions")
def get_conflict_decision_versions(project_id: str, conflict_id: str) -> Dict[str, Any]:
    """
    Get all decision versions for a conflict.

    Shows the complete history of decisions with version tracking.

    Path Parameters:
    - project_id: Project identifier
    - conflict_id: Conflict identifier

    Returns:
    - List of all decision versions in chronological order
    """
    try:
        from socrates_api.database import get_database

        db = get_database()
        logger.info(f"Retrieving decision versions for conflict {conflict_id} in project {project_id}")

        # Get all decisions (which are stored with version numbers)
        decisions = db.get_conflict_decisions(conflict_id)

        if not decisions:
            raise HTTPException(status_code=404, detail="No decisions found for conflict")

        return {
            "status": "success",
            "project_id": project_id,
            "conflict_id": conflict_id,
            "total_versions": len(decisions),
            "versions": decisions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.debug("Error getting decision versions", exc_info=True)
        raise HTTPException(status_code=500, detail="Operation failed. Please try again later.")
