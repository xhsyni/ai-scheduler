from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from utils.timezone import now_myt, to_myt

class Conversation(BaseModel):
    conversation_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    task_id: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now_myt)

    def to_json(self):
        data = {
            "user_id": self.user_id,
            "task_id": self.task_id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if self.conversation_id:
            data["conversation_id"] = self.conversation_id
        return data
    
    @staticmethod
    def from_json(data: dict) -> "Conversation":
        if not data:
            return None
        return Conversation(
            conversation_id=str(data["_id"]) if data.get("_id") else data.get("conversation_id"),
            user_id=data.get("user_id"),
            task_id=data.get("task_id"),
            title=data.get("title"),
            created_at=to_myt(data.get("created_at"))
        )

class Message(BaseModel):
    message_id: Optional[str] = Field(default=None)
    conversation_id: Optional[str] = Field(default=None)
    role: Optional[str] = Field(default=None)
    content: Optional[str] = Field(default=None)
    normalize_content: Optional[str] = Field(default=None) # english
    message_input: Optional[str] = Field(default=None) # text, voice 
    language: Optional[str] = Field(default=None)
    useful: Optional[bool] = Field(default=None)
    created_at: datetime = Field(default_factory=now_myt)

    def to_json(self):
        data = {
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "normalize_content": self.normalize_content,
            "message_input": self.message_input,
            "language": self.language,
            "useful": self.useful,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if self.message_id:
            data["message_id"] = self.message_id
        return data
    
    @staticmethod
    def from_json(data: dict) -> "Message":
        if not data:
            return None
        return Message(
            message_id=str(data["_id"]) if data.get("_id") else data.get("message_id"),
            conversation_id=data.get("conversation_id"),
            role=data.get("role"),
            content=data.get("content"),
            normalize_content=data.get("normalize_content"),
            message_input=data.get("message_input"),
            language=data.get("language"),
            useful=data.get("useful"),
            created_at=to_myt(data.get("created_at"))
        )



class SendMessageRequest(BaseModel):
    """
    What the user actually needs to send — just their message.
    The AI agent figures out all scheduling details from natural language.
    """
    content: str = Field(..., description="The user's natural-language message.")
    message_input: Optional[str] = Field(default="text", description="'text' or 'voice'")
    language: Optional[str] = Field(default=None, description="BCP-47 language tag, e.g. 'en', 'ms'")

