import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

TenantBase = declarative_base()

class TenantChatSession(TenantBase):
    __tablename__ = "raykha_chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="New Conversation")
    created_at = Column(DateTime, server_default=func.now())

class TenantChatMessage(TenantBase):
    __tablename__ = "raykha_chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("raykha_chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    query_sql = Column(Text, nullable=True)  # Store generated SQL if any
    query_result = Column(Text, nullable=True)  # Store database results as JSON string
    created_at = Column(DateTime, server_default=func.now())
