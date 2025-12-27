"""
Pydantic models for API request/response bodies
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project"""

    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    knowledge_base_content: Optional[str] = Field(
        None, description="Initial knowledge base content"
    )

    class Config:
        extra = "forbid"  # Reject any extra fields (like 'owner')
        json_schema_extra = {
            "example": {
                "name": "Python API Development",
                "description": "Building a REST API with FastAPI",
                "knowledge_base_content": "FastAPI is a modern web framework...",
            }
        }


class UpdateProjectRequest(BaseModel):
    """Request body for updating a project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    phase: Optional[str] = Field(None, description="Project phase")

    class Config:
        extra = "forbid"  # Reject any extra fields
        json_schema_extra = {
            "example": {
                "name": "Updated Project Name",
                "phase": "implementation",
            }
        }


class ProjectResponse(BaseModel):
    """Response model for project data"""

    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    owner: str = Field(..., description="Project owner username")
    description: Optional[str] = Field(None, description="Project description")
    phase: str = Field(..., description="Current project phase")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")
    is_archived: bool = Field(default=False, description="Whether project is archived")

    class Config:
        json_schema_extra = {
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


class ListProjectsResponse(BaseModel):
    """Response model for listing projects"""

    projects: List[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")

    class Config:
        json_schema_extra = {
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


class AskQuestionRequest(BaseModel):
    """Request body for asking a Socratic question"""

    topic: Optional[str] = Field(None, description="Topic to ask about")
    difficulty_level: str = Field(default="intermediate", description="Question difficulty level")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "topic": "API design patterns",
                "difficulty_level": "intermediate",
            }
        }


class QuestionResponse(BaseModel):
    """Response model for a Socratic question"""

    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="The Socratic question")
    context: Optional[str] = Field(None, description="Context for the question")
    hints: List[str] = Field(default_factory=list, description="Available hints")

    class Config:
        json_schema_extra = {
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


class ProcessResponseRequest(BaseModel):
    """Request body for processing a user's response to a question"""

    question_id: str = Field(..., description="Question identifier")
    user_response: str = Field(..., min_length=1, description="User's response to the question")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "question_id": "q_xyz789",
                "user_response": "REST APIs should follow resource-oriented design...",
                "project_id": "proj_abc123",
            }
        }


class ProcessResponseResponse(BaseModel):
    """Response model for processing a user response"""

    feedback: str = Field(..., description="Feedback on the user's response")
    is_correct: bool = Field(..., description="Whether the response is correct")
    next_question: Optional[QuestionResponse] = Field(
        None, description="Next question if available"
    )
    insights: Optional[List[str]] = Field(None, description="Key insights extracted")

    class Config:
        json_schema_extra = {
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


class GenerateCodeRequest(BaseModel):
    """Request body for code generation"""

    project_id: str = Field(..., description="Project identifier")
    specification: Optional[str] = Field(None, description="Code specification or requirements")
    language: str = Field(default="python", description="Programming language")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "specification": "Create a FastAPI endpoint for user registration",
                "language": "python",
            }
        }


class CodeGenerationResponse(BaseModel):
    """Response model for code generation"""

    code: str = Field(..., description="Generated code")
    explanation: Optional[str] = Field(None, description="Explanation of the generated code")
    language: str = Field(..., description="Programming language")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token usage statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "@app.post('/api/users/register')\nasync def register_user(user: User):\n    # Implementation here",
                "explanation": "This endpoint handles user registration using FastAPI...",
                "language": "python",
                "token_usage": {"input_tokens": 150, "output_tokens": 200, "total_tokens": 350},
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ProjectNotFoundError",
                "message": "Project 'proj_abc123' not found",
                "error_code": "PROJECT_NOT_FOUND",
                "details": {"project_id": "proj_abc123"},
            }
        }


class SystemInfoResponse(BaseModel):
    """Response model for system information"""

    version: str = Field(..., description="API version")
    library_version: str = Field(..., description="Socrates library version")
    status: str = Field(..., description="API status")
    uptime: float = Field(..., description="API uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "version": "8.0.0",
                "library_version": "8.0.0",
                "status": "operational",
                "uptime": 3600.5,
            }
        }


# ============================================================================
# Authentication Models
# ============================================================================


class RegisterRequest(BaseModel):
    """Request body for user registration"""

    username: str = Field(
        ..., min_length=3, max_length=100, description="Username (3-100 characters)"
    )
    email: Optional[str] = Field(None, description="User email address (optional)")
    password: str = Field(
        ..., min_length=8, max_length=200, description="Password (min 8 characters)"
    )

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "username": "alice_smith",
                "email": "alice@example.com",
                "password": "SecurePassword123!",
            }
        }


class LoginRequest(BaseModel):
    """Request body for user login"""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "username": "alice_smith",
                "password": "SecurePassword123!",
            }
        }


class UserResponse(BaseModel):
    """Response model for user information"""

    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email address")
    subscription_tier: str = Field(..., description="Subscription tier (free/pro/enterprise)")
    subscription_status: str = Field(..., description="Subscription status")
    testing_mode: bool = Field(..., description="Whether testing mode is enabled")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "alice_smith",
                "email": "alice@example.com",
                "subscription_tier": "pro",
                "subscription_status": "active",
                "testing_mode": False,
                "created_at": "2025-12-01T12:00:00Z",
            }
        }


class TokenResponse(BaseModel):
    """Response model for authentication tokens"""

    access_token: str = Field(..., description="Short-lived access token (15 min)")
    refresh_token: str = Field(..., description="Long-lived refresh token (7 days)")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
            }
        }


class AuthResponse(BaseModel):
    """Combined response for auth operations with user info and tokens"""

    user: UserResponse = Field(..., description="User information")
    access_token: str = Field(..., description="Short-lived access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=900, description="Access token expiry in seconds")

    class Config:
        json_schema_extra = {
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


class RefreshTokenRequest(BaseModel):
    """Request body for refreshing access token"""

    refresh_token: str = Field(..., description="The refresh token")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class ChangePasswordRequest(BaseModel):
    """Request body for changing password"""

    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "old_password": "current_password",
                "new_password": "new_secure_password",
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = Field(default=True, description="Whether operation succeeded")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Logout successful",
            }
        }


class GitHubImportRequest(BaseModel):
    """Request body for GitHub import"""

    url: str = Field(..., description="GitHub repository URL")
    project_name: Optional[str] = Field(None, description="Custom project name")
    branch: Optional[str] = Field(None, description="Branch to import")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "url": "https://github.com/user/repo",
                "project_name": "My Project",
                "branch": "main",
            }
        }


class SetDefaultProviderRequest(BaseModel):
    """Request body for setting default LLM provider"""

    provider: str = Field(..., description="Provider name (claude, openai, gemini, local)")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {"provider": "anthropic"}
        }


class SetLLMModelRequest(BaseModel):
    """Request body for setting LLM model"""

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model identifier")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "provider": "anthropic",
                "model": "claude-3-sonnet"
            }
        }


class AddAPIKeyRequest(BaseModel):
    """Request body for adding API key"""

    provider: str = Field(..., description="Provider name")
    api_key: str = Field(..., description="API key for the provider")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "provider": "anthropic",
                "api_key": "sk-ant-..."
            }
        }


class CollaborationInviteRequest(BaseModel):
    """Request body for inviting collaborator"""

    email: str = Field(..., description="Email of the collaborator")
    role: str = Field(default="viewer", description="Role (editor, viewer, admin)")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "editor"
            }
        }


class DeleteDocumentRequest(BaseModel):
    """Request body for deleting knowledge document"""

    document_id: str = Field(..., description="Document ID to delete")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {"document_id": "doc_123"}
        }


class InitializeRequest(BaseModel):
    """Request body for API initialization"""

    api_key: Optional[str] = Field(None, description="Claude API key")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {"api_key": "sk-ant-..."}
        }


# ============================================================================
# Chat Session and Message Models
# ============================================================================


class CreateChatSessionRequest(BaseModel):
    """Request body for creating a chat session"""

    title: Optional[str] = Field(None, max_length=255, description="Session title")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "title": "Initial Design Discussion"
            }
        }


class ChatSessionResponse(BaseModel):
    """Response model for a chat session"""

    session_id: str = Field(..., description="Unique session identifier")
    project_id: str = Field(..., description="Project ID this session belongs to")
    user_id: str = Field(..., description="User who created the session")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Session last update timestamp")
    archived: bool = Field(default=False, description="Whether session is archived")
    message_count: int = Field(default=0, description="Number of messages in session")

    class Config:
        json_schema_extra = {
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


class ListChatSessionsResponse(BaseModel):
    """Response model for listing chat sessions"""

    sessions: List[ChatSessionResponse] = Field(..., description="List of chat sessions")
    total: int = Field(..., description="Total number of sessions")

    class Config:
        json_schema_extra = {
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


class ChatMessageRequest(BaseModel):
    """Request body for sending a chat message"""

    message: str = Field(..., min_length=1, description="Message content")
    role: str = Field(default="user", description="Message role (user or assistant)")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "message": "What should I focus on next?",
                "role": "user"
            }
        }


class ChatMessage(BaseModel):
    """Model for a chat message"""

    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session ID this message belongs to")
    user_id: str = Field(..., description="User who sent the message")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user or assistant)")
    created_at: datetime = Field(..., description="Message creation timestamp")
    updated_at: datetime = Field(..., description="Message last update timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

    class Config:
        json_schema_extra = {
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


class GetChatMessagesResponse(BaseModel):
    """Response model for listing chat messages"""

    messages: List[ChatMessage] = Field(..., description="List of messages in session")
    total: int = Field(..., description="Total number of messages")
    session_id: str = Field(..., description="Session ID")

    class Config:
        json_schema_extra = {
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


class UpdateMessageRequest(BaseModel):
    """Request body for updating a chat message"""

    content: str = Field(..., min_length=1, description="Updated message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the message")

    class Config:
        extra = "forbid"
        json_schema_extra = {
            "example": {
                "content": "Updated message content",
                "metadata": None
            }
        }
