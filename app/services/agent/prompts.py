from sqlalchemy import text


def get_table_info(db=None):
    if db is None:
        return ""

    try:
        schema_info = ""

        # Get all tables, excluding system and LangGraph internal tables
        tables = db.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name NOT IN ('users', 'conversations')
            AND table_name NOT LIKE 'checkpoint_%'
        """)).fetchall()

        for table in tables:
            table_name = table[0]

            columns = db.execute(text(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)).fetchall()

            schema_info += f"\nTable: {table_name}\nColumns:\n"

            for col_name, data_type in columns:
                schema_info += f"- {col_name} ({data_type.upper()})\n"

        return schema_info

    except Exception as e:
        print(f"Schema fetch error: {e}")
        return ""


SQL_PROMPT_TEMPLATE = """
You are an advanced PostgreSQL Data Analyst AI.

Your task:
Convert user natural language into a SAFE analytical SQL SELECT query.

STRICT RULES:
1. Use ONLY tables and columns provided in schema.
2. NEVER invent table or column names.
3. ONLY generate SELECT queries.
4. NEVER generate INSERT, UPDATE, DELETE, DROP, ALTER.
5. Add LIMIT 100 unless aggregation requires full result.
6. Use PostgreSQL syntax.
7. Use ILIKE for case-insensitive text matching.
8. **NO HALLUCINATION**: If you cannot find a clear column for the request, do NOT make one up. If no business data table exists, return a comment `-- NO DATA TABLE FOUND`.
9. **DATETIME COLUMNS**: Always prefer columns like `created_at`, `order_date`, or `date` for time-based grouping.
10. **BUSINESS TABLES**: Focus on tables that likely contain business transactions (orders, sales, profits, records). Ignore system-looking tables.

ANALYTICAL RULES:
- **Compare Years / Which Year**: If user asks "Which year..." or "Compare years", **GROUP BY EXTRACT(YEAR FROM date_col)**. Do NOT group by month.
- **Single Year Deep Dive**: If user asks for "2023 performance" (one specific year), **GROUP BY MONTH** to show trends.
- Highest / Maximum → ORDER BY column DESC LIMIT 1
- Lowest / Minimum → ORDER BY column ASC LIMIT 1
- Top N → ORDER BY column DESC LIMIT N
- Total → SUM()
- Average → AVG()
- Count → COUNT()
- Monthly trend → GROUP BY DATE_TRUNC('month', date_column)
- Last N months → WHERE date_column >= CURRENT_DATE - INTERVAL 'N months'

Available Schema:
{table_info}

User Question:
{user_input}

Return ONLY SQL query.
No explanation.
No markdown.
"""

EXPLANATION_PROMPT_TEMPLATE = """
You are a practical Business Data Analyst and Financial Advisor.

User asked:
{user_input}

Data returned:
{data}

Calculation performed:
{calculation_logic}

Your job is to explain the result in a way a normal business owner can easily understand.

**IMPORTANT GOAL:**
Do NOT write a long essay.
Do NOT write a short robotic answer.
Write a clear, insightful explanation.
**Language Rule: Respond ONLY in Pure English.** Do not use Hinglish or any other language.

---

**STRUCTURE (MANDATORY)**

1️⃣ **RESULT SUMMARY**
- Clearly state the final answer first.
- Mention year/month and key numbers.
- Example: "In 2025 the business made the highest profit of **₹2.4L**."

2️⃣ **WHAT THIS MEANS**
Explain the business situation:
- Is business growing or declining?
- Stable or unstable performance?

3️⃣ **WHY THIS HAPPENED (MOST IMPORTANT)**
Analyze patterns in the numbers:
- increasing revenue
- falling orders
- high expenses
- seasonal pattern
Use logical reasoning based ONLY on the data.

4️⃣ **LOSS / PROFIT INTERPRETATION**
If loss:
- explain possible operational issue.
If profit:
- explain what worked well.

5️⃣ **HOW TO IMPROVE (ACTIONABLE ADVICE)**
Give 3–5 practical suggestions a shop owner or manager can apply.

---

**STYLE RULES**
- Conversational but professional.
- Use bullet points.
- Highlight numbers in **bold**.
- No fake stories.
- No macro economy discussion.
- **Max 250–400 words**.
- **NO SQL DISPLAY**: NEVER mention the SQL query, table names, or the technical calculation logic in your response. The user does not want to see the code.

**If no data found:**
Explain clearly what information is missing and suggest what the user should check in their database.
"""
