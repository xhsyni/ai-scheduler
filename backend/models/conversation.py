from pydantic import BaseModel, Field
from typing import Optional,List
from models.users import User
from models.tasks import Task
from datetime import datetime, timezone

class Conversation(BaseModel):
    conversation_id: Optional[int] = Field(default=None)
    user_id: Optional[List[User]] = Field(default=None)
    task_id: Optional[Task] = Field(default=None)
    title: str = Field(default=None)
    types: str = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self):
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id.to_json() if self.user_id else None,
            "task_id": self.task_id.to_json() if self.task_id else None,
            "title": self.title,
            "types": self.types,
            "created_at": self.created_at
        }
    
    @staticmethod
    def from_json(data: dict) -> "Conversation":
        return Conversation(
            conversation_id=data.get("conversation_id"),
            user_id=User.from_json(data.get("user_id")) if data.get("user_id") else None,
            task_id=Task.from_json(data.get("task_id")) if data.get("task_id") else None,
            title=data.get("title"),
            types=data.get("types"),
            created_at=data.get("created_at")
        )

class Message(BaseModel):
    message_id: Optional[int] = Field(default=None)
    conversation_id: Optional[Conversation] = Field(default=None)
    role: str = Field(default=None)
    content: str = Field(default=None)
    normalize_content: Optional[str] = Field(default=None) #english
    language: Optional[str] = Field(default=None)
    useful: Optional[bool] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self):
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id.to_json() if self.conversation_id else None,
            "role": self.role,
            "content": self.content,
            "normalize_content": self.normalize_content,
            "language": self.language,
            "useful": self.useful,
            "created_at": self.created_at
        }
    
    @staticmethod
    def from_json(data: dict) -> "Message":
        return Message(
            message_id=data.get("message_id"),
            conversation_id=Conversation.from_json(data.get("conversation_id")) if data.get("conversation_id") else None,
            role=data.get("role"),
            content=data.get("content"),
            normalize_content=data.get("normalize_content"),
            language=data.get("language"),
            useful=data.get("useful"),
            created_at=data.get("created_at")
        )