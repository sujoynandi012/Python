import pymysql
import os
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a database connection"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "employee_registration"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        cursorclass=pymysql.cursors.DictCursor
    )

def parse_query(query: str) -> Dict[str, Any]:
    """Parse the update query and extract components"""
    query = query.strip()
    result = {
        'field': None,
        'identifier': None,
        'value': None,
        'error': None
    }
    
    # Extract field to update
    field_map = {
        'employee id': 'employee_id',
        'id': 'employee_id',
        'name': 'name',
        'office': 'office',
        'address': 'address',
        'experience': 'experience',
        'phone': 'phone_number',
        'phone number': 'phone_number',
        'skill': 'skill_set',
        'skills': 'skill_set'
    }
    
    # Find field in query
    for term, field in field_map.items():
        if term in query.lower():
            result['field'] = field
            break
    
    if not result['field']:
        result['error'] = "Could not determine which field to update."
        return result
    
    # Extract identifier (employee_id or name)
    id_match = re.search(r'(?:employee\s+id|id)\s*[=:]\s*(\d+)', query, re.IGNORECASE)
    if id_match:
        result['identifier'] = ('employee_id', int(id_match.group(1)))
    else:
        # Look for a name pattern (capitalized words that might be a name)
        name_match = re.search(r'(?:name|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', query, re.IGNORECASE)
        if name_match:
            result['identifier'] = ('name', name_match.group(1))
    
    if not result['identifier']:
        result['error'] = "Could not determine employee identifier. Please specify an ID or name."
        return result
    
    # Extract new value (after 'to' or 'as')
    value_match = re.search(r'(?:to|as|with)\s+([^.,;!?]+)(?:$|[.,;!?])', query, re.IGNORECASE)
    if value_match:
        result['value'] = value_match.group(1).strip()
    
    if not result['value']:
        result['error'] = "Could not determine the new value to set."
    
    return result

def updatedata(query: str) -> str:
    """
    Update employee information in the database.
    
    Examples:
        - "Update employee id 123 to set phone number to 555-1234"
        - "Change office for John Doe to New York"
        - "Set experience to 5 years for employee id 456"
        - "Update skills for Jane Smith to Python, SQL, Data Analysis"
    """
    try:
        # Parse the query
        parsed = parse_query(query)
        if parsed['error']:
            return f"❌ {parsed['error']}"
        
        # Get database connection
        conn = get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                # Build and execute the update query
                sql = f"UPDATE employees SET {parsed['field']} = %s WHERE {parsed['identifier'][0]} = %s"
                cursor.execute(sql, (parsed['value'], parsed['identifier'][1]))
                
                if cursor.rowcount == 0:
                    return f"⚠️ No matching employee found with {parsed['identifier'][0]} = {parsed['identifier'][1]}"
                
                conn.commit()
                return f"✅ Successfully updated {parsed['field']} for employee {parsed['identifier'][1]}"
                
        except pymysql.Error as e:
            conn.rollback()
            return f"❌ Database error: {str(e)}"
        finally:
            conn.close()
            
    except Exception as e:
        return f"❌ Error: {str(e)}"