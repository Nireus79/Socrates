"""
Pydantic models for API request/response bodies
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    knowledge_base_content: Optional[str] = Field(
        None, description="Initial knowledge base content"
    )


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

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    phase: Optional[str] = Field(None, description="Project phase")


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

    username: str = Field(
        ..., min_length=3, max_length=100, description="Username (3-100 characters)"
    )
    email: Optional[str] = Field(None, description="User email address (optional)")
    password: str = Field(
        ..., min_length=8, max_length=200, description="Password (min 8 characters)"
    )


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

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


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
            }
        }
    )

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="Short-lived access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")


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
