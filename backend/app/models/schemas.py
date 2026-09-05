import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    title: Optional[str] = "New conversation"


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceCitation(BaseModel):
    episode_title: str
    guest_name: str
    timestamp_ref: Optional[str] = None
    similarity: float


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceCitation] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetailOut(SessionOut):
    messages: list[MessageOut] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1, max_length=4000)
    mode: Literal["default", "ship30"] = "default"
    provider: Literal["ollama", "groq"] = "ollama"


class HealthOut(BaseModel):
    api: bool
    postgres: bool
    pgvector: bool
    ollama: bool
    configured_provider: str
