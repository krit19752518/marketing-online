import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    db_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class CentralUser(Base):
    __tablename__ = "central_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # hashed password
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="STAFF")  # OWNER, MANAGER, CASHIER, STAFF
    created_at = Column(DateTime, server_default=func.now())
