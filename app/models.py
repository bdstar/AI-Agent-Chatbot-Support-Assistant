from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class Reference(BaseModel):
    """A reference to a source document chunk."""
    source: str
    content: str
    page: Optional[int] = None


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """Response body from the AI agent."""
    session_id: str
    response: str
    references: list[Reference] = []


class ChatHistoryItem(BaseModel):
    """A single chat history entry."""
    id: int
    session_id: str
    user_message: str
    ai_response: str
    references: list[Reference] = []
    created_at: datetime


class SessionItem(BaseModel):
    """Summary of a chat session for the sidebar."""
    session_id: str
    first_message: str
    message_count: int
    created_at: datetime


class IngestResponse(BaseModel):
    """Response after document ingestion."""
    status: str
    documents_processed: int
    chunks_created: int
    message: str
