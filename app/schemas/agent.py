from typing import List, Dict, Optional, TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[Dict], add_messages]
    sql_query: Optional[str]
    data: Optional[List[Dict]]
    response: Optional[str]
    has_data: bool
    download_id: Optional[str]
    is_greeting: bool
