from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo

class User(BaseModel):
    user_id: Optional[int] = Field(default=None)
    name: str = Field(default_factory=str)
    email: str = Field(default_factory=str)
    password: str = Field(default_factory=str)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(ZoneInfo("Asia/Kuala_Lumpur")))

    def to_json(self):
        data = {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }
        return data

    @staticmethod
    def from_json(data: dict) -> "User":
        return User(
            id=str(data["_id"]) if data.get("_id") else None,
            name=data.get("name", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
        )