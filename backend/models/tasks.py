from utils.timezone import now_myt, to_myt
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional,List, Literal
from models.users import User
from dateutil.parser import isoparse

class GroupTask(BaseModel):
    user_id: str = Field(default=None)
    name: Optional[str] = Field(default=None)
    role: Optional[Literal["viewer","editor","owner"]] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
    updated_at: Optional[datetime] = Field(default_factory=now_myt)

    def to_json(self):
        from datetime import timezone
        updated_at_aware = self.updated_at
        if updated_at_aware and updated_at_aware.tzinfo is None:
            updated_at_aware = updated_at_aware.replace(tzinfo=timezone.utc)
            
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "updated_by": self.updated_by,
            "updated_at": updated_at_aware.isoformat() if updated_at_aware else None
        }
    
    @staticmethod
    def from_json(data: dict) -> "GroupTask":
        return GroupTask(
            user_id=data.get("user_id"),
            name=data.get("name"),
            role=data.get("role"),
            updated_by=data.get("updated_by"),
            updated_at=to_myt(data.get("updated_at"))
        )

class Task(BaseModel):
    id: Optional[str] = Field(default=None)
    users: List[GroupTask] = Field(default=[])
    title: str = Field(default=None)
    description: Optional[str] = Field(default=None)
    priority: Literal["low", "mid", "high"] = Field(default="low")
    category: Optional[str] = Field(default="Work")
    location: Optional[str] = Field(default=None)
    link: Optional[List[str]] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    reminder: Optional[bool] = Field(default=False)
    status: Optional[str] = Field(default=None)
    embeddings: Optional[List[float]] = Field(default=[])
    created_at: datetime = Field(default_factory=now_myt)
    updated_at: datetime = Field(default_factory=now_myt)

    def to_json(self):
        from datetime import timezone
        
        def make_aware(dt):
            if dt is None:
                return None
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        data = {
            "users": [user.to_json() for user in self.users] if self.users else [],
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "location": self.location,
            "link": self.link,
            "start_time": make_aware(self.start_time),
            "end_time": make_aware(self.end_time),
            "duration": self.duration if self.duration else int((to_myt(self.end_time) - to_myt(self.start_time)).total_seconds() / 60) if self.start_time and self.end_time else None,
            "reminder": self.reminder,
            "status": self.status,
            "embeddings":self.embeddings,
            "created_at": make_aware(self.created_at),
            "updated_at": make_aware(self.updated_at),
        }
        if self.id:
            data["task_id"] = self.id
        return data
    
    @staticmethod
    def from_json(data: dict) -> "Task":
        return Task(
            id=str(data["_id"]) if data.get("_id") else None,
            users=[GroupTask.from_json(user) for user in data.get("users")] if data.get("users") else [],
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority"),
            category=data.get("category", "Work"),
            location=data.get("location"),
            link=data.get("link"),
            start_time=(data.get("start_time")),
            end_time=(data.get("end_time")),
            duration=data.get("duration"),
            reminder=data.get("reminder"),
            status=data.get("status"),
            embeddings=data.get("embeddings"),
            created_at=(data.get("created_at")),
            updated_at=(data.get("updated_at"))
        )