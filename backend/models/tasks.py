from datetime import datetime,timezone
from pydantic import BaseModel, Field
from typing import Optional,List
from models.users import User

class Task(BaseModel):
    task_id: Optional[int] = Field(default=None)
    user_id: Optional[List[User]] = Field(default=None)
    title: str = Field(default=None)
    description: str = Field(default=None)
    priority: str = Field(default="low")
    location: Optional[str] = Field(default=None)
    start_time: Optional[str] = Field(default=None)
    end_time: Optional[str] = Field(default=None)
    date: Optional[str] = Field(default=None)
    duration: Optional[int] = Field(default=None)
    reminder: Optional[bool] = Field(default=False)
    status: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self):
        return {
            "task_id": self.task_id,
            "user_id": [user.to_json() for user in self.user_id] if self.user_id else [],
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "location": self.location,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "date": self.date,
            "duration": self.duration,
            "reminder": self.reminder,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @staticmethod
    def from_json(data: dict) -> "Task":
        return Task(
            task_id=data.get("task_id"),
            user_id=[User.from_json(user) for user in data.get("user_id")] if data.get("user_id") else [],
            title=data.get("title"),
            description=data.get("description"),
            priority=data.get("priority"),
            location=data.get("location"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            date=data.get("date"),
            duration=data.get("duration"),
            reminder=data.get("reminder"),
            status=data.get("status"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )