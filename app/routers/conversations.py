import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.conversation import Conversation
from app.schemas.chat import ChatResponse
from app.utils.auth import get_current_user
from app.services.agent.graph import agent_graph

# We need a schema for listing conversations, let's define it or import if we made one.
# In app/main.py it was ConversationResponse and ConversationList.
# I will use inline pydantic models or simple dicts if schemas are not available, 
# but I should ideally have them in app2/schemas.
# I didn't verify app2/schemas/conversation.py, I only made auth, chat, agent.
# I will define response models here or add them to schemas later if needed. 
# For now, I'll rely on what I have or define simple DTOs.
# Actually, I missed creating `app2/schemas/conversation.py` in my previous steps!
# I will define them here for now to avoid breaking flow, or I can add them to schemas/chat.py or a new file.
# I'll add them to this file for simplicity as they are specific to this router.

from pydantic import BaseModel

class ConversationResponse(BaseModel):
    thread_id: str
    title: str
    created_at: datetime
    class Config:
        from_attributes = True

class ConversationList(BaseModel):
    conversations: List[ConversationResponse]

class MessageResponse(BaseModel):
    role: str
    content: str
    data: List[dict] | None = None
    download_id: str | None = None

class MessageList(BaseModel):
    messages: List[MessageResponse]


router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("", response_model=ConversationList)
def get_conversations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).all()
    return {"conversations": conversations}

@router.post("/new", response_model=ConversationResponse)
def create_conversation(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_thread_id = str(uuid.uuid4())
    new_conversation = Conversation(
        user_id=current_user.id,
        thread_id=new_thread_id,
        title="New Chat",
        created_at=datetime.utcnow()
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

@router.get("/{thread_id}/messages", response_model=MessageList)
def get_conversation_messages(thread_id: str, current_user = Depends(get_current_user)):
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_graph.get_state(config)
    
    messages = []
    if state and state.values and "messages" in state.values:
        for m in state.values["messages"]:
            # Format based on LangGraph message types
            role = "user" if m.type == "human" else "ai"
            msg_data = {
                "role": role,
                "content": m.content,
            }
            # Extract data and download_id from metadata if present
            if hasattr(m, "additional_kwargs"):
                msg_data["data"] = m.additional_kwargs.get("data")
                msg_data["download_id"] = m.additional_kwargs.get("download_id")
            
            messages.append(msg_data)
            
    return {"messages": messages}

@router.delete("/{thread_id}")
def delete_conversation(thread_id: str, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1. Verify ownership and delete from metadata table
    conv = db.query(Conversation).filter(Conversation.thread_id == thread_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
    
    db.delete(conv)
    db.commit()
    
    # 2. Cleanup LangGraph checkpoints from the history database
    try:
        # We use raw SQL because these tables are not in our SQLAlchemy models
        db.execute(text("DELETE FROM checkpoints WHERE thread_id = :tid"), {"tid": thread_id})
        db.execute(text("DELETE FROM checkpoint_blobs WHERE thread_id = :tid"), {"tid": thread_id})
        db.execute(text("DELETE FROM checkpoint_writes WHERE thread_id = :tid"), {"tid": thread_id})
        db.commit()
    except Exception as e:
        print(f"Non-critical cleanup error: {e}")
        db.rollback()
        
    return {"message": "Conversation deleted successfully"}
    
@router.patch("/{thread_id}/title")
def update_conversation_title(thread_id: str, title_data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    new_title = title_data.get("title")
    if not new_title:
        raise HTTPException(status_code=400, detail="Title is required")
        
    conv = db.query(Conversation).filter(Conversation.thread_id == thread_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
        
    conv.title = new_title
    db.commit()
    return {"message": "Title updated successfully", "title": new_title}
