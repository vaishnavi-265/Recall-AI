from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant", "tool"]
MemoryKind = Literal["decision", "requirement", "task", "fact", "note"]


class Message(BaseModel):
    role: Role
    content: str = Field(min_length=1)


class ConversationIngestRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    project: str = Field(default="general", min_length=1)
    messages: list[Message] = Field(min_length=1)


class Memory(BaseModel):
    id: int | None = None
    kind: MemoryKind
    content: str
    project: str
    provider: str
    source_conversation_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IngestResponse(BaseModel):
    conversation_id: str
    memories_created: int
    memories: list[Memory]


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[Memory]


class TimelineResponse(BaseModel):
    project: str
    count: int
    events: list[Memory]
