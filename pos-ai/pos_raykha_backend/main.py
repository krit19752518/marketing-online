from jose import jwt, JWTError
import json
import bcrypt
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import Config
from database import get_central_db
from models import CentralUser, Tenant
from tenant_db_manager import tenant_db_manager
from tenant_models import TenantChatSession, TenantChatMessage
from services.ai_service import AIService

app = FastAPI(title="POS-Raykha Backend", version="1.0.0")

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    name: str
    role: str
    tenant_id: str
    tenant_name: str

class ChatMessageRequest(BaseModel):
    session_id: str
    content: str

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"

# JWT Helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token scheme. Prefix token with 'Bearer '."
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired."
        )

# Endpoint: Login (Central Authentication)
@app.post("/api/raykha/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, central_db: Session = Depends(get_central_db)):
    user = central_db.query(CentralUser).filter(CentralUser.username == req.username).first()
    if not user or not bcrypt.checkpw(req.password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )
    
    tenant = central_db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant database settings not configured."
        )

    token_data = {
        "user_id": user.id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role,
        "name": user.name
    }
    token = create_access_token(data=token_data)

    return LoginResponse(
        token=token,
        name=user.name,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_name=tenant.name
    )

# Endpoint: Create new Chat Session in Tenant DB
@app.post("/api/raykha/sessions")
def create_session(
    req: ChatSessionCreate,
    current_user: dict = Depends(get_current_user),
    central_db: Session = Depends(get_central_db)
):
    tenant_id = current_user["tenant_id"]
    tenant_db = tenant_db_manager.get_tenant_session(tenant_id, central_db)
    
    try:
        session = TenantChatSession(title=req.title)
        tenant_db.add(session)
        tenant_db.commit()
        tenant_db.refresh(session)
        return {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at
        }
    finally:
        tenant_db.close()

# Endpoint: List Chat Sessions in Tenant DB (with snippets)
@app.get("/api/raykha/sessions")
def list_sessions(
    current_user: dict = Depends(get_current_user),
    central_db: Session = Depends(get_central_db)
):
    tenant_id = current_user["tenant_id"]
    tenant_db = tenant_db_manager.get_tenant_session(tenant_id, central_db)
    
    try:
        sessions = tenant_db.query(TenantChatSession).order_by(TenantChatSession.created_at.desc()).all()
        result = []
        for s in sessions:
            # Query last message as a snippet
            last_msg = (
                tenant_db.query(TenantChatMessage)
                .filter(TenantChatMessage.session_id == s.id)
                .order_by(TenantChatMessage.created_at.desc())
                .first()
            )
            snippet = last_msg.content[:50] + "..." if last_msg else "No messages yet"
            result.append({
                "id": s.id,
                "title": s.title,
                "snippet": snippet,
                "created_at": s.created_at
            })
        return result
    finally:
        tenant_db.close()

# Endpoint: Send message to RayKha AI Agent (processes prompts and SQL queries)
@app.post("/api/raykha/chat")
async def send_chat(
    req: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    central_db: Session = Depends(get_central_db)
):
    tenant_id = current_user["tenant_id"]
    tenant_db = tenant_db_manager.get_tenant_session(tenant_id, central_db)
    
    try:
        # Verify session exists
        session = tenant_db.query(TenantChatSession).filter(TenantChatSession.id == req.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
            
        # Get chat history (up to last 10 messages for context)
        history_msgs = (
            tenant_db.query(TenantChatMessage)
            .filter(TenantChatMessage.session_id == req.session_id)
            .order_by(TenantChatMessage.created_at.asc())
            .limit(10)
            .all()
        )
        
        # Package history for LLM
        history_payload = []
        for h in history_msgs:
            history_payload.append({
                "role": "user" if h.role == "user" else "assistant",
                "content": h.content
            })
            
        # Call AI Agent (AIService compiles queries and runs them safely)
        ai_response, generated_sql, query_results = await AIService.ask_raykha(
            user_message=req.content,
            history=history_payload,
            tenant_db=tenant_db
        )
        
        # If the session title is still default, update it using user's initial query
        if session.title == "New Conversation" or session.title == "":
            session.title = req.content[:30] + "..." if len(req.content) > 30 else req.content
            tenant_db.add(session)
            
        # Log User message to database
        user_log = TenantChatMessage(
            session_id=req.session_id,
            role="user",
            content=req.content
        )
        tenant_db.add(user_log)
        
        # Log AI response to database
        ai_log = TenantChatMessage(
            session_id=req.session_id,
            role="assistant",
            content=ai_response,
            query_sql=generated_sql if generated_sql else None,
            query_result=query_results if query_results else None
        )
        tenant_db.add(ai_log)
        tenant_db.commit()
        
        return {
            "ai_response": ai_response,
            "query_sql": generated_sql,
            "query_result": query_results
        }
    finally:
        tenant_db.close()

# Endpoint: Retrieve chat history for session
@app.get("/api/raykha/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    central_db: Session = Depends(get_central_db)
):
    tenant_id = current_user["tenant_id"]
    tenant_db = tenant_db_manager.get_tenant_session(tenant_id, central_db)
    
    try:
        messages = (
            tenant_db.query(TenantChatMessage)
            .filter(TenantChatMessage.session_id == session_id)
            .order_by(TenantChatMessage.created_at.asc())
            .all()
        )
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "query_sql": m.query_sql,
                "query_result": m.query_result,
                "created_at": m.created_at
            }
            for m in messages
        ]
    finally:
        tenant_db.close()

# Endpoint: Delete Session
@app.delete("/api/raykha/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    central_db: Session = Depends(get_central_db)
):
    tenant_id = current_user["tenant_id"]
    tenant_db = tenant_db_manager.get_tenant_session(tenant_id, central_db)
    
    try:
        session = tenant_db.query(TenantChatSession).filter(TenantChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found.")
            
        tenant_db.delete(session)
        tenant_db.commit()
        return {"message": "Chat session and history deleted successfully."}
    finally:
        tenant_db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=True)
