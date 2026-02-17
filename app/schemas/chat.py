from typing import List, Dict, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[List[Dict]] = []
    has_data: bool = False
    download_id: Optional[str] = None
    is_greeting: bool = False
    thread_id: Optional[str] = None
