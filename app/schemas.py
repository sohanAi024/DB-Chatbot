from typing import List, Dict, Optional, TypedDict, Annotated
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from sqlalchemy.orm import Session # Required for AgentState TypeDict

class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""
    address: Optional[str] = ""
    salary: Optional[int] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[Dict]] = []
    has_data: bool = False
    download_id: Optional[str] = None
    is_greeting: bool = False

class AgentState(TypedDict):
    messages: Annotated[List[Dict], add_messages]
    sql_query: Optional[str]
    data: Optional[List[Dict]]
    response: Optional[str]
    has_data: bool
    download_id: Optional[str]
    is_greeting: bool
    db: Session # This is important to pass the DB session