from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas import ChatRequest, ChatResponse
from app.database import get_db
from app.agents.agent_graph import agent_graph # Import the compiled graph
from app.schemas import AgentState # Import AgentState TypedDict

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Initial state for the LangGraph agent
        state: AgentState = {
            "messages": [{"role": "user", "content": req.message}],
            "sql_query": None,
            "data": [],
            "response": "",
            "has_data": False,
            "download_id": None,
            "is_greeting": False,
            "db": db # Pass the DB session to the agent state
        }
        result = agent_graph.invoke(state) # Use the imported agent_graph

        return ChatResponse(
            response=result["response"],
            data=result["data"],
            has_data=result["has_data"],
            download_id=result["download_id"],
            is_greeting=result["is_greeting"]
        )
    except Exception as e:
        print(f"Chat endpoint error: {e}") # Log the error for debugging
        return ChatResponse(
            response=f"Sorry, an error occurred: {str(e)}",
            data=[],
            has_data=False,
            download_id=None,
            is_greeting=False
        )