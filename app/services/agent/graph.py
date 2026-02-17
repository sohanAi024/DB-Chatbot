import tempfile
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
import os
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
# Import TypedDict and Annotated
from typing import List, Dict, Optional, TypedDict, Annotated
from langchain_core.runnables import RunnableConfig
from app.schemas.agent import AgentState
from app.utils.greetings import is_greeting
from app.utils.excel import generate_excel
from app.utils.temp_files import add_temp_file
from app.services.agent.prompts import EXPLANATION_PROMPT_TEMPLATE
from app.services.agent.llm import llm
from app.services.agent.utils import text_to_sql, execute_query
from app.config import DATABASE_URL
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# --- LangGraph Nodes ---


def input_node(state: AgentState, config: RunnableConfig) -> AgentState:
    db = config.get("configurable", {}).get("db")
    last_message = state["messages"][-1]
    # Support both dict and HumanMessage
    if isinstance(last_message, dict):
        user_input = last_message["content"]
    else:
        user_input = last_message.content

    if is_greeting(user_input):
        greeting = "Hello! I'm your database assistant. How can I help you with your database today?"
        return {
            "is_greeting": True,
            "response": greeting,
            "has_data": False,
            "data": [],
            "sql_query": None,
            "download_id": None,
            "messages": [AIMessage(content=greeting, additional_kwargs={"data": [], "download_id": None})]
        }
    else:
        return {
            "is_greeting": False,
            "sql_query": text_to_sql(user_input, db)
        }


def query_node(state: AgentState, config: RunnableConfig) -> AgentState:
    db = config.get("configurable", {}).get("db")
    if state["is_greeting"] or not state["sql_query"]:
        if not state["is_greeting"]:
            error_msg = "I'm not sure what you're asking. Try queries like 'Show me the total number of orders' or 'List all tables'."
            return {
                "response": error_msg,
                "has_data": False,
                "data": [],
                "download_id": None,
                "messages": [AIMessage(content=error_msg, additional_kwargs={"data": [], "download_id": None})]
            }
        return {}

    data = execute_query(state["sql_query"], db)

    if data is None:
        error_msg = "I encountered an issue retrieving data for your request. Could you try asking in a different way?"
        return {
            "response": error_msg,
            "has_data": False,
            "data": [],
            "download_id": None,
            "messages": [AIMessage(content=error_msg)]
        }

    updates = {
        "data": data,
        "has_data": bool(data)
    }

    # CONDITIONAL EXCEL GENERATION
    last_message = state["messages"][-1]
    user_input = last_message["content"] if isinstance(last_message, dict) else last_message.content
    
    if "excel" in user_input.lower():
        download_info = generate_excel(data)
        if download_info:
            download_id, file_path = download_info
            add_temp_file(download_id, file_path)
            updates["download_id"] = download_id
        else:
            updates["download_id"] = None
    else:
        updates["download_id"] = None

    return updates


def summarize_node(state: AgentState, config: RunnableConfig) -> AgentState:
    if state["is_greeting"]:
        return state
        
    if not state["data"]:
        # If no data but there are messages, we might still want to summarize or just chat
        if len(state["messages"]) > 1:
            pass # Continue to LLM for conversational response
        else:
            return state

    # Convert dict messages to LangChain message objects for history
    formatted_messages = []
    for m in state["messages"][:-1]: # Previous history
        if isinstance(m, dict):
            if m["role"] == "user":
                formatted_messages.append(HumanMessage(content=m["content"]))
            else:
                formatted_messages.append(AIMessage(content=m["content"]))
        else:
            formatted_messages.append(m)

    system_prompt = EXPLANATION_PROMPT_TEMPLATE.format(
        user_input=state["messages"][-1].content if hasattr(state["messages"][-1], "content") else state["messages"][-1]["content"],
        data=state["data"][:50] if state["data"] else "No new data retrieved from database.",
        calculation_logic=state.get("sql_query", "Direct inquiry")
    )
    
    formatted_messages.append(SystemMessage(content=system_prompt))
    formatted_messages.append(HumanMessage(content=state["messages"][-1].content if hasattr(state["messages"][-1], "content") else state["messages"][-1]["content"]))

    try:
        response = llm.invoke(formatted_messages)
        res_text = response.content.strip()
        data = state.get("data")
        download_id = state.get("download_id")
        return {
            "response": res_text,
            "messages": [AIMessage(content=res_text, additional_kwargs={"data": data, "download_id": download_id})]
        }
    except Exception as e:
        print(f"Summarization Error: {e}")
        error_msg = f"I found some records, but I couldn't generate a summary." if state["data"] else "I'm sorry, I couldn't process your request."
        return {
            "response": error_msg,
            "messages": [AIMessage(content=error_msg, additional_kwargs={"data": state.get("data"), "download_id": state.get("download_id")})]
        }


def create_graph():
    graph = StateGraph(AgentState)
    graph.add_node("input", input_node)
    graph.add_node("query", query_node)
    graph.add_node("summarize", summarize_node)
    
    graph.add_edge("input", "query")
    graph.add_edge("query", "summarize")
    graph.add_edge("summarize", END)
    
    graph.set_entry_point("input")
    
    # Persistent Memory checkpointer with PostgreSQL
    # Connection pool for PostgreSQL
    # Using a simple singleton-like pattern for the pool in this demo
    # In production, this should be managed more robustly
    global _pool
    if '_pool' not in globals():
        _pool = ConnectionPool(conninfo=DATABASE_URL, max_size=10, kwargs={"autocommit": True})
    
    checkpointer = PostgresSaver(_pool)
    # Ensure tables are created (idempotent)
    checkpointer.setup()
    
    return graph.compile(checkpointer=checkpointer)


# Initialize the agent graph
agent_graph = create_graph()
