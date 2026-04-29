"""
Message types for agent communication.

Defines:
- Request/Response message formats
- Message serialization
- Message validation
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from enum import Enum


class MessageType(Enum):
    """Types of messages in the system"""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    NOTIFICATION = "notification"


class MessageStatus(Enum):
    """Status of a message"""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class AgentMessage:
    """Base message for agent communication"""

    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Create message from dictionary"""
        data = data.copy()
        if isinstance(data.get("message_type"), str):
            data["message_type"] = MessageType(data["message_type"])
        return cls(**data)


@dataclass
class RequestMessage(AgentMessage):
    """Request message sent from one agent to another"""

    target_agent: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    reply_to: Optional[str] = None
    timeout: float = 30.0
    fire_and_forget: bool = False

    def __post_init__(self):
        self.message_type = MessageType.REQUEST

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return data


@dataclass
class ResponseMessage(AgentMessage):
    """Response message from agent"""

    request_id: str = ""
    status: MessageStatus = MessageStatus.SUCCESS
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        self.message_type = MessageType.RESPONSE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        data["status"] = self.status.value
        return data

    @classmethod
    def success(
        cls,
        request_id: str,
        result: Dict[str, Any],
        sender: str = "",
        **kwargs,
    ) -> "ResponseMessage":
        """Create successful response"""
        return cls(
            request_id=request_id,
            status=MessageStatus.SUCCESS,
            result=result,
            sender=sender,
            **kwargs,
        )

    @classmethod
    def error(
        cls,
        request_id: str,
        error: str,
        sender: str = "",
        **kwargs,
    ) -> "ResponseMessage":
        """Create error response"""
        return cls(
            request_id=request_id,
            status=MessageStatus.ERROR,
            error=error,
            sender=sender,
            **kwargs,
        )


@dataclass
class ErrorMessage(AgentMessage):
    """Error message"""

    request_id: str = ""
    error_code: str = ""
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.message_type = MessageType.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return data
