import re
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.agents.mistral import llm
from app.agents.prompts import get_table_info, SQL_PROMPT_TEMPLATE
from app.utils.greetings import is_greeting

def text_to_sql(user_input: str) -> str:
    if is_greeting(user_input):
        return ""

    table_info = get_table_info()
    prompt = SQL_PROMPT_TEMPLATE.format(table_info=table_info, user_input=user_input)

    try:
        response = llm.invoke(prompt)
        sql_query = response.content.strip()
        sql_query = re.sub(r'```sql\n?', '', sql_query)
        sql_query = re.sub(r'```\n?', '', sql_query)

        # Safety check for potentially harmful SQL commands
        if any(word in sql_query.lower() for word in ['drop', 'delete', 'insert', 'update', 'alter', 'truncate']):
            return ""

        # Fallback for "all data" or specific user names if no SELECT was generated
        if not sql_query or not sql_query.lower().startswith("select"):
            all_patterns = [
                r"\ball\b.*\bdata\b", r"\ball\b.*\busers\b", r"\bshow\b.*\ball\b", r"\blist\b.*\ball\b",
                r"\bshow\b.*\busers\b", r"\blist\b.*\busers\b", r"\busers\b.*\bdata\b", r"\ball\b"
            ]
            if any(re.search(pat, user_input, re.IGNORECASE) for pat in all_patterns):
                return "SELECT * FROM users LIMIT 100"

            words = user_input.split()
            stopwords = {"show", "data", "for", "of", "info", "send", "me", "give", "i", "want", "to", "all", "users"}
            names = [w for w in words if w.lower() not in stopwords and w.isalpha()]
            if names:
                name = names[0]
                return f"SELECT * FROM users WHERE LOWER(name) LIKE '%{name.lower()}%' LIMIT 100"
            return "" # Return empty string if no valid SQL and no clear fallback

        return sql_query.strip()
    except Exception as e:
        print(f"Error generating SQL: {str(e)}")
        return ""

def execute_query(sql_query: str, db: Session) -> Optional[List[Dict]]:
    if not sql_query:
        return None
    try:
        result = db.execute(text(sql_query))
        colnames = result.keys()
        rows = result.fetchall()
        data = [dict(zip(colnames, row)) for row in rows]
        # Convert non-serializable types (like datetime) to string
        for row in data:
            for key, val in row.items():
                if isinstance(val, (float, int, str, bool)) or val is None:
                    continue
                row[key] = str(val)
        return data
    except Exception as e:
        print(f"Database error: {str(e)}")
        return None