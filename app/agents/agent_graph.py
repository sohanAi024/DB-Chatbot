import tempfile
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing import List, Dict, Optional, TypedDict, Annotated # Import TypedDict and Annotated
from app.schemas import AgentState # Import AgentState
from app.utils.greetings import is_greeting
from app.utils.excel import generate_excel
from app.utils.temp_files import add_temp_file
from app.agents.query_utils import text_to_sql, execute_query

# --- LangGraph Nodes ---
def input_node(state: AgentState) -> AgentState:
    last_message = state["messages"][-1]
    # Support both dict and HumanMessage
    if isinstance(last_message, dict):
        user_input = last_message["content"]
    else:
        user_input = last_message.content

    if is_greeting(user_input):
        state["is_greeting"] = True
        state["response"] = "Hello! I'm your database assistant. How can I help you with user data today?"
        state["has_data"] = False
        state["data"] = []
        state["download_id"] = None
    else:
        state["is_greeting"] = False
        state["sql_query"] = text_to_sql(user_input)
    return state

def query_node(state: AgentState) -> AgentState:
    if state["is_greeting"] or not state["sql_query"]:
        if not state["is_greeting"]:
            state["response"] = "I'm not sure what you're asking. Try queries like 'Show me users with salary above 50000' or 'List all users'."
            state["has_data"] = False
            state["data"] = []
            state["download_id"] = None
        return state

    state["data"] = execute_query(state["sql_query"], state["db"])

    if state["data"] is None:
        state["response"] = "I encountered an issue retrieving data for your request. Could you try asking in a different way?"
        state["has_data"] = False
        state["data"] = []
        state["download_id"] = None
    else:
        download_id = generate_excel(state["data"])
        if download_id:
            add_temp_file(download_id, f"{tempfile.gettempdir()}/db_export_{download_id}.xlsx") # Add to temp_files
            state["download_id"] = download_id
        else:
            state["download_id"] = None # Ensure it's None if generation failed

        state["response"] = f"I found {len(state['data'])} records for your request." if state["data"] else "I couldn't find any matching records."
        state["has_data"] = bool(state["data"])
    return state

def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("input", input_node)
    graph.add_node("query", query_node)
    graph.add_edge("input", "query")
    graph.add_edge("query", END)
    graph.set_entry_point("input")
    return graph.compile()

# Initialize the agent graph
agent_graph = create_graph()