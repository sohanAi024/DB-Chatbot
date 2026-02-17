from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.utils.auth import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.agent import AgentState
from app.database import get_db, get_data_db
from app.services.agent.graph import agent_graph
from app.models.conversation import Conversation

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_data_db), current_user = Depends(get_current_user)):
    try:
        # Initial state for the LangGraph agent
        state: AgentState = {
            "messages": [{"role": "user", "content": req.message}],
            "sql_query": None,
            "data": [],
            "response": "",
            "has_data": False,
            "download_id": None,
            "is_greeting": False
        }
        
        # Determine thread_id (prioritize request, fallback to username or session)
        thread_id = req.thread_id or f"user_{current_user.id}"
        config = {"configurable": {"thread_id": thread_id, "db": db}}
        
        # --- Update Conversation Title if needed ---
        primary_db = next(get_db()) # Get the history DB session
        conv = primary_db.query(Conversation).filter(Conversation.thread_id == thread_id).first()
        if conv and conv.title == "New Chat":
            # Simple title generation: first 30 chars of the message
            new_title = req.message[:30] + ("..." if len(req.message) > 30 else "")
            conv.title = new_title
            primary_db.commit()

        result = agent_graph.invoke(state, config=config) # Use config for memory and DB

        return ChatResponse(
            response=result["response"],
            data=result["data"],
            has_data=result["has_data"],
            download_id=result["download_id"],
            is_greeting=result["is_greeting"],
            thread_id=thread_id
        )
    except Exception as e:
        print(f"Chat endpoint error: {e}") # Log the error for debugging
        return ChatResponse(
            response=f"Sorry, an error occurred: {str(e)}",
            data=[],
            has_data=False,
            download_id=None,
            is_greeting=False,
            thread_id=req.thread_id
        )
