from utils.timezone import now_myt, to_myt
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional,List, Literal
from models.users import User

class GroupTask(BaseModel):
    user_id: str = Field(default=None)
    name: Optional[str] = Field(default=None)
    role: Optional[Literal["viewer","editor","admin","owner"]] = Field(default=None)
    updated_by: Optional[str] = Field(default=None)
    updated_at: Optional[datetime] = Field(default_factory=now_myt)

    def to_json(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "role": self.role,
            "updated_by": self.updated_by,
            "updated_at": self.updated_at.isoformat()
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
    description: str = Field(default=None)
    priority: Literal["low", "mid", "high"] = Field(default="low")
    location: Optional[str] = Field(default=None)
    link: Optional[List[str]] = Field(default=None)
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    reminder: Optional[bool] = Field(default=False)
    status: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=now_myt)
    updated_at: datetime = Field(default_factory=now_myt)

    def to_json(self):
        data = {
            "users": [user.to_json() for user in self.users] if self.users else [],
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "location": self.location,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration if self.duration else int((to_myt(self.end_time) - to_myt(self.start_time)).total_seconds() / 60) if self.start_time and self.end_time else None,
            "reminder": self.reminder,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        print(data)
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
            location=data.get("location"),
            start_time=to_myt(data.get("start_time")),
            end_time=to_myt(data.get("end_time")),
            duration=data.get("duration"),
            reminder=data.get("reminder"),
            status=data.get("status"),
            created_at=to_myt(data.get("created_at")),
            updated_at=to_myt(data.get("updated_at"))
        )