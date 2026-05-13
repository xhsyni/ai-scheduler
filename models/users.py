from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

class User(BaseModel):
    user_id: Optional[int] = Field(default=None)
    name: str = Field(default=None)
    email: str = Field(default=None)
    password: str = Field(default=None)
    tags: List[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_json(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "tags": self.tags,
            "created_at": self.created_at
        }
    
    @staticmethod
    def from_json(data: dict) -> "User":
        return User(
            user_id=data.get("user_id"),
            name=data.get("name"),
            email=data.get("email"),
            tags=data.get("tags"),
            created_at=data.get("created_at")
        )