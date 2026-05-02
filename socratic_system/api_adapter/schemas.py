"""
Request/Response schemas for API adapter layer.

Provides standardized DTOs for service communication.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RequestDTO(BaseModel):
    """Base request DTO"""

    model_config = ConfigDict(extra="allow")


class ResponseDTO(BaseModel):
    """Base response DTO"""

    status: str = Field(..., description="Response status (success/error)")
    service: str = Field(..., description="Service name")
    version: str = Field(default="v1", description="API version")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp"
    )

    @classmethod
    def success(
        cls,
        data: Dict[str, Any],
        service: str,
        message: Optional[str] = None,
    ) -> "ResponseDTO":
        """
        Create success response.

        Args:
            data: Response data
            service: Service name
            message: Optional message

        Returns:
            ResponseDTO instance
        """
        return cls(
            status="success",
            service=service,
            data=data,
            message=message,
        )

    @classmethod
    def error(
        cls,
        error_message: str,
        service: str,
        error_code: Optional[str] = None,
    ) -> "ResponseDTO":
        """
        Create error response.

        Args:
            error_message: Error message
            service: Service name
            error_code: Optional error code

        Returns:
            ResponseDTO instance
        """
        data = {
            "error": error_message,
        }
        if error_code:
            data["error_code"] = error_code

        return cls(
            status="error",
            service=service,
            data=data,
        )


class AsyncJobRequest(BaseModel):
    """Request for async job submission"""

    model_config = ConfigDict(extra="forbid")

    service: str = Field(..., description="Target service name")
    method: str = Field(..., description="Service method to call")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Method parameters"
    )
    timeout: float = Field(
        default=300.0, description="Job timeout in seconds", ge=1.0, le=3600.0
    )
    name: Optional[str] = Field(None, description="Job name for tracking")


class AsyncJobResponse(BaseModel):
    """Response from async job submission"""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="Unique job ID")
    service: str = Field(..., description="Service that will process the job")
    method: str = Field(..., description="Service method")
    status: str = Field(
        default="pending", description="Initial job status (pending)"
    )
    message: str = Field(default="Job submitted", description="Status message")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Job creation timestamp"
    )


class JobStatusResponse(BaseModel):
    """Response containing job status"""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    ready: bool = Field(..., description="Whether result is ready")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: int = Field(..., description="Job execution duration in ms")
    created_at: Optional[datetime] = Field(None, description="Job creation time")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")


class ServiceInfoRequest(BaseModel):
    """Request for service information"""

    model_config = ConfigDict(extra="forbid")

    service_name: Optional[str] = Field(None, description="Specific service name")


class ServiceInfoResponse(BaseModel):
    """Response with service information"""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Service name")
    methods: list[str] = Field(..., description="Available methods")
    version: str = Field(..., description="Service version")
    description: Optional[str] = Field(None, description="Service description")


class BatchJobStatusRequest(BaseModel):
    """Request for batch job status"""

    model_config = ConfigDict(extra="forbid")

    job_ids: list[str] = Field(..., description="List of job IDs to check")


class BatchJobStatusResponse(BaseModel):
    """Response with batch job statuses"""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total jobs queried")
    completed: int = Field(..., description="Completed jobs")
    pending: int = Field(..., description="Pending jobs")
    failed: int = Field(..., description="Failed jobs")
    jobs: Dict[str, JobStatusResponse] = Field(..., description="Job statuses")
