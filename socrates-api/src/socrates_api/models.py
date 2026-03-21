"""
Pydantic models for API request/response bodies
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Import input validation utilities if available
try:
    from socratic_security.input_validation import (
        SanitizedStr,
        validate_no_sql_injection,
        validate_no_xss,
    )
    SECURITY_VALIDATION_AVAILABLE = True
except ImportError:
    # Fallback to regular strings if security module unavailable
    SanitizedStr = str
    validate_no_sql_injection = None
    validate_no_xss = None
    SECURITY_VALIDATION_AVAILABLE = False


# ============================================================================
# Standardized API Response Model
# ============================================================================


class APIResponse(BaseModel):
    """
    Standardized wrapper for all API responses.

    This model provides consistent response formatting across all endpoints:
    - success: boolean indicating operation success/failure
    - status: more specific status string (e.g., "success", "error", "pending")
    - data: the actual response data (optional, varies by endpoint)
    - message: optional message to user
    - error_code: machine-readable error code (for errors)
    - timestamp: when the response was generated
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "status": "success",
                "message": "Operation completed successfully",
                "data": {
                    "project_id": "proj_abc123",
                    "name": "My Project"
                },
                "error_code": None,
                "timestamp": "2026-01-08T12:30:45.123456Z"
            }
        }
    )

    success: bool = Field(..., description="Whether the operation succeeded")
    status: Literal["success", "error", "pending", "created", "updated", "deleted"] = Field(
        ..., description="Status of the operation"
    )
    data: Optional[Dict[str, Any]] = Field(
        None, description="Response data (structure varies by endpoint)"
    )
    message: Optional[str] = Field(
        None, description="Human-readable message (useful for errors and status updates)"
    )
    error_code: Optional[str] = Field(
        None, description="Machine-readable error code for programmatic handling"
    )
    timestamp: Optional[str] = Field(
        None, description="ISO 8601 timestamp when response was generated"
    )


# ============================================================================
# Project Models
# ============================================================================


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Python API Development",
                "description": "Building a REST API with FastAPI",
                "knowledge_base_content": "FastAPI is a modern web framework...",
            }
        },
    )

    name: SanitizedStr = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[SanitizedStr] = Field(None, max_length=1000, description="Project description")
    knowledge_base_content: Optional[SanitizedStr] = Field(
        None, description="Initial knowledge base content"
    )

    @field_validator("name", "description")
    @classmethod
    def validate_no_injection(cls, v):
        """Validate input for SQL injection and XSS attacks"""
        if v is None:
            return v
        if validate_no_sql_injection:
            validate_no_sql_injection(v)
        return v


class UpdateProjectRequest(BaseModel):
    """Request body for updating a project"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Updated Project Name",
                "phase": "implementation",
            }
        },
    )

    name: Optional[SanitizedStr] = Field(None, min_length=1, max_length=200, description="Project name")
    phase: Optional[SanitizedStr] = Field(None, description="Project phase")

    @field_validator("name", "phase")
    @classmethod
    def validate_no_injection(cls, v):
        """Validate input for SQL injection and XSS attacks"""
        if v is None:
            return v
        if validate_no_sql_injection:
            validate_no_sql_injection(v)
        return v


class ProjectResponse(BaseModel):
    """Response model for project data"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "proj_abc123",
                "name": "Python API Development",
                "owner": "alice",
                "description": "Building a REST API with FastAPI",
                "phase": "active",
                "created_at": "2025-12-04T10:00:00Z",
                "updated_at": "2025-12-04T10:30:00Z",
                "is_archived": False,
            }
        }
    )

    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    owner: str = Field(..., description="Project owner username")
    description: Optional[str] = Field(None, description="Project description")
    phase: str = Field(..., description="Current project phase")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")
    is_archived: bool = Field(default=False, description="Whether project is archived")
    overall_maturity: float = Field(default=0.0, description="Project maturity percentage (0-100)")
    progress: int = Field(default=0, description="Project progress percentage (0-100)")


class ListProjectsResponse(BaseModel):
    """Response model for listing projects"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "projects": [
                    {
                        "project_id": "proj_abc123",
                        "name": "Python API Development",
                        "owner": "alice",
                        "description": "Building a REST API with FastAPI",
                        "phase": "active",
                        "created_at": "2025-12-04T10:00:00Z",
                        "updated_at": "2025-12-04T10:30:00Z",
                        "is_archived": False,
                    }
                ],
                "total": 1,
            }
        }
    )

    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")


class AskQuestionRequest(BaseModel):
    """Request body for asking a Socratic question"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "project_id": "proj_abc123",
                "topic": "API design patterns",
                "difficulty_level": "intermediate",
            }
        },
    )

    topic: Optional[str] = Field(None, description="Topic to ask about")
    difficulty_level: str = Field(default="intermediate", description="Question difficulty level")


class QuestionResponse(BaseModel):
    """Response model for a Socratic question"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q_xyz789",
                "question": "What are the main principles of RESTful API design?",
                "context": "You are designing an API for a tutoring system",
                "hints": [
                    "Think about resource-oriented design",
                    "Consider HTTP methods and status codes",
                ],
            }
        }
    )

    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The Socratic question")
    context: Optional[str] = Field(None, description="Context for the question")
    hints: List[str] = Field(default_factory=list, description="Available hints")


class ProcessResponseRequest(BaseModel):
    """Request body for processing a user's response to a question"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "question_id": "q_xyz789",
                "user_response": "REST APIs should follow resource-oriented design...",
                "project_id": "proj_abc123",
            }
        },
    )

    question_id: str = Field(..., description="Question identifier")
    user_response: str = Field(..., min_length=1, description="User's response to the question")


class ProcessResponseResponse(BaseModel):
    """Response model for processing a user response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "feedback": "Good understanding of REST principles! Let me ask you about HTTP methods...",
                "is_correct": True,
                "next_question": {
                    "question_id": "q_xyz790",
                    "question": "Which HTTP method should be used for retrieving data?",
                    "context": "In REST API design",
                    "hints": [],
                },
                "insights": [
                    "Student understands resource-oriented design",
                    "Can explain REST principles clearly",
                ],
            }
        }
    )

    feedback: str = Field(..., description="Feedback on the user's response")
    is_correct: bool = Field(..., description="Whether the response is correct")
    next_question: Optional[QuestionResponse] = Field(
        None, description="Next question if available"
    )
    insights: Optional[List[str]] = Field(None, description="Key insights extracted")


class GenerateCodeRequest(BaseModel):
    """Request body for code generation"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "project_id": "proj_abc123",
                "specification": "Create a FastAPI endpoint for user registration",
                "language": "python",
            }
        },
    )

    project_id: str = Field(..., description="Project identifier")
    specification: Optional[str] = Field(None, description="Code specification or requirements")
    language: str = Field(default="python", description="Programming language")


class GenerateCodeForProjectRequest(BaseModel):
    """Request body for code generation (when project_id is in URL path)"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "specification": "Create a FastAPI endpoint for user registration",
                "language": "python",
            }
        },
    )

    specification: Optional[str] = Field(None, description="Code specification or requirements")
    language: Optional[str] = Field(default="python", description="Programming language")


class CodeGenerationResponse(BaseModel):
    """Response model for code generation"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "@app.post('/api/users/register')\nasync def register_user(user: User):\n    # Implementation here",
                "explanation": "This endpoint handles user registration using FastAPI...",
                "language": "python",
                "token_usage": {"input_tokens": 150, "output_tokens": 200, "total_tokens": 350},
            }
        }
    )

    code: str = Field(..., description="Generated code")
    explanation: Optional[str] = Field(None, description="Explanation of the generated code")
    language: str = Field(..., description="Programming language")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")


class ErrorResponse(BaseModel):
    """Standard error response model"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ProjectNotFoundError",
                "message": "Project 'proj_abc123' not found",
                "error_code": "PROJECT_NOT_FOUND",
                "details": {"project_id": "proj_abc123"},
            }
        }
    )

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SystemInfoResponse(BaseModel):
    """Response model for system information"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "8.0.0",
                "library_version": "8.0.0",
                "status": "operational",
                "uptime": 3600.5,
            }
        }
    )

    version: str = Field(..., description="API version")
    library_version: str = Field(..., description="Socrates library version")
    status: str = Field(..., description="API status")
    uptime: float = Field(..., description="API uptime in seconds")


# ============================================================================
# Authentication Models
# ============================================================================


class RegisterRequest(BaseModel):
    """Request body for user registration"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "username": "alice_smith",
                "email": "alice@example.com",
                "password": "SecurePassword123!",
            }
        },
    )

    username: SanitizedStr = Field(
        ..., min_length=3, max_length=100, description="Username (3-100 characters, alphanumeric + underscore)"
    )
    email: Optional[str] = Field(None, description="User email address (optional)")
    password: str = Field(
        ..., min_length=8, max_length=200, description="Password (min 8 characters)"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format and content"""
        if v is None:
            return v
        # Check for valid characters (alphanumeric + underscore)
        if not all(c.isalnum() or c == '_' for c in v):
            raise ValueError("Username must contain only alphanumeric characters and underscores")
        if validate_no_sql_injection:
            validate_no_sql_injection(v)
        return v


class LoginRequest(BaseModel):
    """Request body for user login"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "username": "alice_smith",
                "password": "SecurePassword123!",
            }
        },
    )

    username: SanitizedStr = Field(..., description="Username")
    password: str = Field(..., description="Password")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username for injection attacks"""
        if v is None:
            return v
        if validate_no_sql_injection:
            validate_no_sql_injection(v)
        return v


class UserResponse(BaseModel):
    """Response model for user information"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "alice_smith",
                "email": "alice@example.com",
                "subscription_tier": "pro",
                "subscription_status": "active",
                "testing_mode": False,
                "created_at": "2025-12-01T12:00:00Z",
            }
        }
    )

    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email address")
    subscription_tier: str = Field(..., description="Subscription tier (free/pro/enterprise)")
    subscription_status: str = Field(..., description="Subscription status")
    testing_mode: bool = Field(..., description="Whether testing mode is enabled")
    created_at: datetime = Field(..., description="Account creation timestamp")


class TokenResponse(BaseModel):
    """Response model for authentication tokens"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }
    )

    access_token: str = Field(..., description="Short-lived access token (15 min)")
    refresh_token: str = Field(..., description="Long-lived refresh token (7 days)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")


class AuthResponse(BaseModel):
    """Combined response for auth operations with user info and tokens"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "username": "alice_smith",
                    "email": "alice@example.com",
                    "subscription_tier": "pro",
                    "subscription_status": "active",
                    "testing_mode": False,
                    "created_at": "2025-12-01T12:00:00Z",
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "api_key_configured": False,
                "api_key_message": "No API key configured. Please save your API key in Settings > LLM > Anthropic to use AI features.",
            }
        }
    )

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="Short-lived access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")
    api_key_configured: bool = Field(
        default=True, description="Whether user has configured an API key"
    )
    api_key_message: Optional[str] = Field(
        default=None,
        description="Message to display if no API key is configured. Only shown after login, not on login page.",
    )


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing access token"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        },
    )

    refresh_token: str = Field(..., description="The refresh token")


class ChangePasswordRequest(BaseModel):
    """Request body for changing password"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "old_password": "current_password",
                "new_password": "new_secure_password",
            }
        },
    )

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")


class SuccessResponse(BaseModel):
    """Generic success response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Logout successful",
            }
        }
    )

    success: bool = Field(default=True, description="Whether operation succeeded")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class GitHubImportRequest(BaseModel):
    """Request body for GitHub import"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "url": "https://github.com/user/repo",
                "project_name": "My Project",
                "branch": "main",
            }
        },
    )

    url: str = Field(..., description="GitHub repository URL")
    project_name: Optional[str] = Field(None, description="Custom project name")
    branch: Optional[str] = Field(None, description="Branch to import")


class SetDefaultProviderRequest(BaseModel):
    """Request body for setting default LLM provider"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"provider": "anthropic"}},
    )

    provider: str = Field(..., description="Provider name (claude, openai, gemini, local)")


class SetLLMModelRequest(BaseModel):
    """Request body for setting LLM model"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"provider": "anthropic", "model": "claude-3-sonnet"}},
    )

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model identifier")


class AddAPIKeyRequest(BaseModel):
    """Request body for adding API key"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"provider": "anthropic", "api_key": "sk-ant-..."}},
    )

    provider: str = Field(..., description="Provider name")
    api_key: str = Field(..., description="API key for the provider")


class CollaborationInviteRequest(BaseModel):
    """Request body for inviting collaborator"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"email": "user@example.com", "role": "editor"}},
    )

    email: str = Field(..., description="Email of the collaborator")
    role: str = Field(default="viewer", description="Role (editor, viewer, admin)")


class CollaborationInvitationResponse(BaseModel):
    """Response body for invitation operations"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "inv_123",
                "project_id": "proj_123",
                "inviter_id": "user1",
                "invitee_email": "user2@example.com",
                "role": "editor",
                "token": "eyJ...",
                "status": "pending",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-08T00:00:00Z",
                "accepted_at": None,
            }
        }
    )

    id: str = Field(..., description="Invitation ID")
    project_id: str = Field(..., description="Project ID")
    inviter_id: str = Field(..., description="Username of inviter")
    invitee_email: str = Field(..., description="Email of invitee")
    role: str = Field(..., description="Assigned role")
    token: str = Field(..., description="Unique invitation token")
    status: str = Field(
        ..., description="Invitation status (pending, accepted, expired, cancelled)"
    )
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: str = Field(..., description="Expiration timestamp")
    accepted_at: Optional[str] = Field(None, description="Acceptance timestamp")


class DeleteDocumentRequest(BaseModel):
    """Request body for deleting knowledge document"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"document_id": "doc_123"}},
    )

    document_id: str = Field(..., description="Document ID to delete")


class InitializeRequest(BaseModel):
    """Request body for API initialization"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"api_key": "sk-ant-..."}},
    )

    api_key: Optional[str] = Field(None, description="Claude API key")


# ============================================================================
# Chat Session and Message Models
# ============================================================================


class CreateChatSessionRequest(BaseModel):
    """Request body for creating a chat session"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"title": "Initial Design Discussion"}},
    )

    title: Optional[str] = Field(None, max_length=255, description="Session title")


class ChatSessionResponse(BaseModel):
    """Response model for a chat session"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_abc123",
                "project_id": "proj_xyz789",
                "user_id": "alice",
                "title": "Initial Design Discussion",
                "created_at": "2025-12-04T10:00:00Z",
                "updated_at": "2025-12-04T10:30:00Z",
                "archived": False,
                "message_count": 5,
            }
        }
    )

    session_id: str = Field(..., description="Unique session identifier")
    project_id: str = Field(..., description="Project ID this session belongs to")
    user_id: str = Field(..., description="User who created the session")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    archived: bool = Field(default=False, description="Whether session is archived")
    message_count: int = Field(default=0, description="Number of messages in session")


class ListChatSessionsResponse(BaseModel):
    """Response model for listing chat sessions"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sessions": [
                    {
                        "session_id": "sess_abc123",
                        "project_id": "proj_xyz789",
                        "user_id": "alice",
                        "title": "Initial Design Discussion",
                        "created_at": "2025-12-04T10:00:00Z",
                        "updated_at": "2025-12-04T10:30:00Z",
                        "archived": False,
                        "message_count": 5,
                    }
                ],
                "total": 1,
            }
        }
    )

    sessions: List[ChatSessionResponse] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total number of sessions")


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "message": "What should I focus on next?",
                "role": "user",
                "mode": "socratic",
            }
        },
    )

    message: str = Field(..., min_length=1, max_length=5000, description="Message content (max 5000 characters)")
    role: str = Field(default="user", description="Message role (user or assistant)")
    mode: str = Field(default="socratic", description="Chat mode (socratic or direct)")


class ChatMessage(BaseModel):
    """Model for a chat message"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_def456",
                "session_id": "sess_abc123",
                "user_id": "alice",
                "content": "What should I focus on next?",
                "role": "user",
                "created_at": "2025-12-04T10:10:00Z",
                "updated_at": "2025-12-04T10:10:00Z",
                "metadata": None,
            }
        }
    )

    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session ID this message belongs to")
    user_id: str = Field(..., description="User who sent the message")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user or assistant)")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Message last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")


class GetChatMessagesResponse(BaseModel):
    """Response model for listing chat messages"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {
                        "message_id": "msg_def456",
                        "session_id": "sess_abc123",
                        "user_id": "alice",
                        "content": "What should I focus on next?",
                        "role": "user",
                        "created_at": "2025-12-04T10:10:00Z",
                        "updated_at": "2025-12-04T10:10:00Z",
                        "metadata": None,
                    }
                ],
                "total": 1,
                "session_id": "sess_abc123",
            }
        }
    )

    messages: List[ChatMessage] = Field(..., description="List of messages in session")
    total: int = Field(..., description="Total number of messages")
    session_id: str = Field(..., description="Session ID")


class UpdateMessageRequest(BaseModel):
    """Request body for updating a chat message"""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"content": "Updated message content", "metadata": None}},
    )

    content: str = Field(..., min_length=1, description="Updated message content")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata for the message"
    )


# ============================================================================
# Collaboration Response Models
# ============================================================================


class CollaboratorData(BaseModel):
    """Response data for collaborator information"""

    username: str = Field(..., description="Username of collaborator")
    email: str = Field(..., description="Email of collaborator")
    role: str = Field(..., description="Role in project (owner, editor, viewer)")
    joined_at: Optional[str] = Field(None, description="When collaborator joined")
    status: Optional[str] = Field(default="inactive", description="Current status")


class CollaboratorListData(BaseModel):
    """Response data for list of collaborators"""

    project_id: str = Field(..., description="Project ID")
    total: int = Field(..., description="Total number of collaborators")
    collaborators: List[Dict[str, Any]] = Field(..., description="List of collaborators")


class ActiveCollaboratorData(BaseModel):
    """Response data for active collaborators"""

    project_id: str = Field(..., description="Project ID")
    active_count: int = Field(..., description="Number of active collaborators")
    collaborators: List[Dict[str, Any]] = Field(..., description="List of active collaborators")


class CollaborationTokenData(BaseModel):
    """Response data for collaboration token validation"""

    valid: bool = Field(..., description="Whether token is valid")
    inviter: Optional[str] = Field(None, description="User who sent invitation")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    email: Optional[str] = Field(None, description="Invited email")


class CollaborationSyncData(BaseModel):
    """Response data for collaboration sync"""

    synced_count: int = Field(..., description="Number of items synced")
    last_sync: str = Field(..., description="Timestamp of last sync")
    status: str = Field(..., description="Sync status")


class ActiveSessionsData(BaseModel):
    """Response data for active collaboration sessions"""

    total: int = Field(..., description="Total active sessions")
    sessions: List[Dict[str, Any]] = Field(..., description="List of active sessions")


class PresenceData(BaseModel):
    """Response data for user presence"""

    user_id: str = Field(..., description="User identifier")
    project_id: str = Field(..., description="Project ID")
    status: str = Field(..., description="Presence status (online, away, offline)")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


# ============================================================================
# Project Analytics Response Models
# ============================================================================


class ProjectStatsData(BaseModel):
    """Response data for project statistics"""

    project_id: str = Field(..., description="Project ID")
    total_collaborators: int = Field(..., description="Total collaborators")
    total_messages: int = Field(..., description="Total messages exchanged")
    code_generations: int = Field(..., description="Number of code generations")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class ProjectMaturityData(BaseModel):
    """Response data for project maturity assessment"""

    project_id: str = Field(..., description="Project ID")
    overall_maturity: float = Field(..., description="Overall maturity percentage (0-100)")
    components: Dict[str, float] = Field(..., description="Maturity by component")
    last_assessment: str = Field(..., description="When assessment was done")


class ProjectAnalyticsData(BaseModel):
    """Response data for project analytics"""

    project_id: str = Field(..., description="Project ID")
    period: str = Field(..., description="Analytics period")
    metrics: Dict[str, Any] = Field(..., description="Various metrics")


class ProjectExportData(BaseModel):
    """Response data for project export"""

    export_id: str = Field(..., description="Export identifier")
    format: str = Field(..., description="Export format (json, csv, etc)")
    size: int = Field(..., description="Size in bytes")
    status: str = Field(..., description="Export status")


# ============================================================================
# Knowledge Response Models
# ============================================================================


class KnowledgeSearchData(BaseModel):
    """Response data for knowledge search"""

    query: str = Field(..., description="Search query")
    total_results: int = Field(..., description="Total search results")
    results: List[Dict[str, Any]] = Field(..., description="Search results")


class RelatedDocumentsData(BaseModel):
    """Response data for related documents"""

    document_id: str = Field(..., description="Source document ID")
    total_related: int = Field(..., description="Number of related documents")
    documents: List[Dict[str, Any]] = Field(..., description="Related documents")


class BulkImportData(BaseModel):
    """Response data for bulk import"""

    imported_count: int = Field(..., description="Number of documents imported")
    failed_count: int = Field(default=0, description="Number of failed imports")
    details: List[Dict[str, Any]] = Field(..., description="Import details")


# ============================================================================
# Phase 4: Skills Ecosystem Models
# ============================================================================


# ---- Marketplace Models ----


class RegisterSkillRequest(BaseModel):
    """Request to register a skill in the marketplace"""

    skill_id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Skill name")
    type: str = Field(..., description="Skill type/category")
    effectiveness: float = Field(..., description="Skill effectiveness (0.0-1.0)", ge=0.0, le=1.0)
    agent: str = Field(..., description="Agent that created the skill")
    tags: Optional[List[str]] = Field(default=None, description="Skill tags")
    description: Optional[str] = Field(default=None, description="Skill description")


class DiscoverSkillsRequest(BaseModel):
    """Request to discover skills in the marketplace"""

    skill_type: Optional[str] = Field(default=None, description="Filter by skill type")
    min_effectiveness: float = Field(default=0.0, description="Minimum effectiveness filter")
    min_usage: int = Field(default=0, description="Minimum usage count filter")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    max_results: int = Field(default=10, description="Maximum results to return")


class SearchSkillsRequest(BaseModel):
    """Request to search skills by text"""

    query: str = Field(..., description="Search query")
    max_results: int = Field(default=10, description="Maximum results to return")


class SkillMetadataResponse(BaseModel):
    """Skill metadata response"""

    skill_id: str = Field(..., description="Skill identifier")
    name: str = Field(..., description="Skill name")
    type: str = Field(..., description="Skill type")
    effectiveness: float = Field(..., description="Skill effectiveness")
    agent: str = Field(..., description="Creating agent")
    usage_count: int = Field(default=0, description="Number of times used")
    tags: List[str] = Field(default_factory=list, description="Skill tags")
    adoption_stats: Optional[Dict[str, Any]] = Field(default=None, description="Adoption statistics")


class MarketplaceStatsResponse(BaseModel):
    """Marketplace statistics response"""

    total_skills: int = Field(..., description="Total skills in marketplace")
    total_types: int = Field(..., description="Number of skill types")
    average_effectiveness: float = Field(..., description="Average skill effectiveness")
    most_adopted: Optional[List[str]] = Field(default=None, description="Most adopted skills")


# ---- Distribution Models ----


class DistributeSkillRequest(BaseModel):
    """Request to distribute a skill to an agent"""

    source_skill_id: str = Field(..., description="Source skill ID")
    source_agent: str = Field(..., description="Source agent")
    target_agent: str = Field(..., description="Target agent to receive skill")
    skill_data: Dict[str, Any] = Field(..., description="Skill data")


class BroadcastSkillRequest(BaseModel):
    """Request to broadcast skill to multiple agents"""

    source_skill_id: str = Field(..., description="Source skill ID")
    source_agent: str = Field(..., description="Source agent")
    target_agents: List[str] = Field(..., description="Target agents")
    skill_data: Dict[str, Any] = Field(..., description="Skill data")


class RecordAdoptionRequest(BaseModel):
    """Request to record skill adoption result"""

    source_skill_id: str = Field(..., description="Source skill ID")
    target_agent: str = Field(..., description="Agent adopting skill")
    effectiveness: float = Field(..., description="Adoption effectiveness", ge=0.0, le=1.0)
    success: bool = Field(default=True, description="Whether adoption was successful")


class AdoptionStatusResponse(BaseModel):
    """Adoption status response"""

    skill_id: str = Field(..., description="Skill ID")
    adoption_count: int = Field(..., description="Number of adoptions")
    adoption_rate: float = Field(..., description="Adoption rate (0-1)")
    adoptions: List[Dict[str, Any]] = Field(..., description="Adoption details")


class DistributionMetricsResponse(BaseModel):
    """Distribution metrics response"""

    total_distributions: int = Field(..., description="Total distributions")
    total_adoptions: int = Field(..., description="Total adoptions")
    adoption_rate: float = Field(..., description="Overall adoption rate")


# ---- Composition Models ----


class CreateCompositionRequest(BaseModel):
    """Request to create a skill composition"""

    composition_id: str = Field(..., description="Unique composition ID")
    name: str = Field(..., description="Composition name")
    skills: List[str] = Field(..., description="List of skill IDs in order")
    execution_type: str = Field(default="sequential", description="Execution type: sequential, parallel, or conditional")


class ExecuteCompositionRequest(BaseModel):
    """Request to execute a composition"""

    composition_id: str = Field(..., description="Composition to execute")
    initial_context: Dict[str, Any] = Field(..., description="Initial execution context")


class AddParameterMappingRequest(BaseModel):
    """Request to add parameter mapping"""

    composition_id: str = Field(..., description="Composition ID")
    from_skill_index: int = Field(..., description="Source skill index")
    from_param: str = Field(..., description="Source parameter name")
    to_skill_index: int = Field(..., description="Target skill index")
    to_param: str = Field(..., description="Target parameter name")


class CompositionResponse(BaseModel):
    """Composition response"""

    composition_id: str = Field(..., description="Composition ID")
    name: str = Field(..., description="Composition name")
    skills: List[str] = Field(..., description="Skills in composition")
    execution_type: str = Field(..., description="Execution type")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")


class ExecutionResultResponse(BaseModel):
    """Composition execution result"""

    status: str = Field(..., description="Execution status")
    results: Dict[str, Any] = Field(..., description="Execution results")
    execution_id: Optional[str] = Field(default=None, description="Execution ID")
    duration: Optional[float] = Field(default=None, description="Duration in milliseconds")


# ---- Analytics Models ----


class TrackMetricRequest(BaseModel):
    """Request to track a skill metric"""

    skill_id: str = Field(..., description="Skill ID")
    agent_name: str = Field(..., description="Agent name")
    metric_name: str = Field(..., description="Metric name")
    metric_value: float = Field(..., description="Metric value")


class PerformanceAnalysisResponse(BaseModel):
    """Performance analysis response"""

    skill_id: str = Field(..., description="Skill ID")
    agents_using: int = Field(..., description="Number of agents using skill")
    metric_summaries: Dict[str, Any] = Field(..., description="Metric statistics")
    performance_score: float = Field(..., description="Overall performance score")


class HighPerformerResponse(BaseModel):
    """High performer skill response"""

    skill_id: str = Field(..., description="Skill ID")
    effectiveness: float = Field(..., description="Effectiveness score")
    adoption: int = Field(..., description="Adoption count")


class EcosystemHealthResponse(BaseModel):
    """Ecosystem health response"""

    total_skills: int = Field(..., description="Total skills in ecosystem")
    total_agents: int = Field(..., description="Total agents")
    average_effectiveness: float = Field(..., description="Average effectiveness")
    ecosystem_health: str = Field(..., description="Health status: excellent, good, fair, poor, no_data")


# ============================================================================
# Multi-Factor Authentication (MFA) Models
# ============================================================================


class MFASetupResponse(BaseModel):
    """Response for MFA setup initialization"""

    secret: str = Field(..., description="TOTP secret (base32 encoded)")
    qr_code_uri: str = Field(..., description="QR code URI for authenticator app")
    backup_codes: List[str] = Field(..., description="List of backup recovery codes")
    recovery_codes_display: str = Field(..., description="Formatted backup codes for display")


class MFAVerifyEnableRequest(BaseModel):
    """Request to verify TOTP code and enable MFA"""

    totp_code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA during login"""

    username: str = Field(..., description="Username")
    totp_code: Optional[str] = Field(None, description="6-digit TOTP code")
    recovery_code: Optional[str] = Field(None, description="Recovery code (if TOTP unavailable)")


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""

    password: str = Field(..., description="User password for authentication")


class MFAStatusResponse(BaseModel):
    """Response showing MFA status"""

    mfa_enabled: bool = Field(..., description="Whether MFA is enabled")
    mfa_methods: List[str] = Field(default_factory=lambda: ["totp"], description="Enabled MFA methods")
