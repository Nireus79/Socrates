"""
Pydantic models for API request/response bodies
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CreateProjectRequest(BaseModel):
    """Request body for creating a new project"""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    owner: str = Field(..., min_length=1, max_length=100, description="Project owner username")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    knowledge_base_content: Optional[str] = Field(None, description="Initial knowledge base content")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python API Development",
                "owner": "alice",
                "description": "Building a REST API with FastAPI",
                "knowledge_base_content": "FastAPI is a modern web framework..."
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
                "is_archived": False
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
                        "is_archived": False
                    }
                ],
                "total": 1
            }
        }


class AskQuestionRequest(BaseModel):
    """Request body for asking a Socratic question"""
    project_id: str = Field(..., description="Project identifier")
    topic: Optional[str] = Field(None, description="Topic to ask about")
    difficulty_level: str = Field(default="intermediate", description="Question difficulty level")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "topic": "API design patterns",
                "difficulty_level": "intermediate"
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
                    "Consider HTTP methods and status codes"
                ]
            }
        }


class ProcessResponseRequest(BaseModel):
    """Request body for processing a user's response to a question"""
    question_id: str = Field(..., description="Question identifier")
    user_response: str = Field(..., min_length=1, description="User's response to the question")
    project_id: str = Field(..., description="Project identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_xyz789",
                "user_response": "REST APIs should follow resource-oriented design...",
                "project_id": "proj_abc123"
            }
        }


class ProcessResponseResponse(BaseModel):
    """Response model for processing a user response"""
    feedback: str = Field(..., description="Feedback on the user's response")
    is_correct: bool = Field(..., description="Whether the response is correct")
    next_question: Optional[QuestionResponse] = Field(None, description="Next question if available")
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
                    "hints": []
                },
                "insights": [
                    "Student understands resource-oriented design",
                    "Can explain REST principles clearly"
                ]
            }
        }


class GenerateCodeRequest(BaseModel):
    """Request body for code generation"""
    project_id: str = Field(..., description="Project identifier")
    specification: Optional[str] = Field(None, description="Code specification or requirements")
    language: str = Field(default="python", description="Programming language")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj_abc123",
                "specification": "Create a FastAPI endpoint for user registration",
                "language": "python"
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
                "token_usage": {
                    "input_tokens": 150,
                    "output_tokens": 200,
                    "total_tokens": 350
                }
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
                "details": {"project_id": "proj_abc123"}
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
                "uptime": 3600.5
            }
        }
