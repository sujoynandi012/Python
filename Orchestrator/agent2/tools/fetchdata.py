import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

# Natural language → DB column mapping
COLUMN_MAP = {
    "id": "employee_id",
    "employee id": "employee_id",
    "name": "name",
    "office": "office",
    "address": "address",
    "experience": "experience",
    "phone": "phone_number",
    "phone number": "phone_number",
    "ph no": "phone_number",
    "skill": "skill_set",
    "skills": "skill_set",
    "skill set": "skill_set",
}

def fetchdata(query: str) -> str:
    """
    Tool: FetchData
    Description:
        Fetch employee details from the `employees` table in MySQL.

        Args:
            query (str): Natural language user query (e.g., "What is the phone number of employee id 2?").

        Example calls:
            fetchdata("What is the employee id of Sujoy?")
            fetchdata("What is the phone number of employee id 2?")
            fetchdata("What is the address of Sujoy?")
            fetchdata("What is the skill set of employee id 1?")
            fetchdata("What is the skill set of Sunita?")

        Supports queries like:
        - "What is the employee id of Sujoy?"
        - "What is the phone number of employee id 2?"
        - "What is the address of Sujoy?"
        - "What is the skill set of employee id 1?"
        - "What is the skill set of Sunita?"
    """
    try:
        # Detect which column is being requested
        column = None
        for key, col in COLUMN_MAP.items():
            if key in query.lower():
                column = col
                break
        if not column:
            return "❌ Could not determine which field to fetch."

        # Detect identifier (employee_id or name)
        identifier, value = None, None
        if "employee id" in query.lower() or "id" in query.lower():
            identifier = "employee_id"
            value = "".join([c for c in query if c.isdigit()])
        else:
            words = query.split()
            for w in words:
                if w[0].isupper():  # crude name detection
                    identifier = "name"
                    value = w
                    break
        if not identifier or not value:
            return "❌ Could not determine employee identifier."

        # DB connection
        conn = pymysql.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            port=3306
        )
        cursor = conn.cursor()
        sql = f"SELECT {column} FROM employees WHERE {identifier} = %s"
        print(f"DEBUG SQL: {sql}, Value: {value}")
        cursor.execute(sql, (value,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return f"{column}: {result[0]}"
        else:
            return f"❌ No record found for {identifier} = {value}"

    except Exception as e:
        return f"❌ Database error: {str(e)}"
