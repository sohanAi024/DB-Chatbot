def get_table_info():
    return """
    Table: users
    Columns:
    - id (integer): Unique identifier
    - name (text): User's full name
    - email (text): Email address
    - phone (text): Phone number
    - address (text): Address
    - salary (integer): Salary
    - created_at (datetime): Created date
    """

# Prompt template for SQL generation
SQL_PROMPT_TEMPLATE = """
Analyze the following user input and determine if it's asking for database information.
If it is, convert it to a PostgreSQL SQL query. If not, return an empty string.

Available table information:
{table_info}

User input: {user_input}

Rules:
1. Only return SQL if the user is clearly asking for data
2. For greetings or casual conversation, return empty string
3. Use proper PostgreSQL syntax
4. Add LIMIT 100 if not specified
5. Use safe SQL practices (e.g., no DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE statements)

Response (SQL query or empty string):
"""