import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.agent.llm import llm
from app.services.agent.prompts import SQL_PROMPT_TEMPLATE, get_table_info
from app.utils.greetings import is_greeting


def text_to_sql(user_input: str, db: Session) -> str:
    if is_greeting(user_input):
        return ""

    table_info = get_table_info(db)

    prompt = SQL_PROMPT_TEMPLATE.format(
        table_info=table_info,
        user_input=user_input
    )

    try:
        response = llm.invoke(prompt)
        sql_query = response.content.strip()

        # Remove markdown if model adds it
        sql_query = re.sub(r"```sql", "", sql_query)
        sql_query = re.sub(r"```", "", sql_query).strip()

        # Remove trailing semicolon if present to avoid syntax error with LIMIT
        sql_query = sql_query.rstrip(";")

        sql_lower = sql_query.lower()

        # 🔒 SECURITY VALIDATION
        if not sql_lower.startswith("select"):
            return ""

        blocked_keywords = [
            "drop", "delete", "insert",
            "update", "alter", "truncate"
        ]

        if any(word in sql_lower for word in blocked_keywords):
            return ""

        # Ensure LIMIT exists
        if "limit" not in sql_lower:
            sql_query += " LIMIT 100"

        return sql_query.strip()

    except Exception as e:
        print(f"LLM SQL Generation Error: {e}")
        return ""


def execute_query(sql_query: str, db: Session) -> Optional[List[Dict]]:
    if not sql_query:
        return None

    try:
        result = db.execute(text(sql_query))
        colnames = result.keys()
        rows = result.fetchall()

        data = [dict(zip(colnames, row)) for row in rows]

        # Convert non-JSON serializable values (datetime etc.)
        for row in data:
            for key, val in row.items():
                if not isinstance(val, (int, float, str, bool)) and val is not None:
                    row[key] = str(val)

        return data

    except Exception as e:
        print(f"Database error: {e}")
        return None
