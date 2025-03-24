import re
import sqlparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def format_sql(sql_query):
    """
    Format SQL query for better readability
    
    Args:
        sql_query (str): Raw SQL query
        
    Returns:
        str: Formatted SQL query
    """
    if not sql_query:
        return ""
    
    try:
        # Format SQL with syntax highlighting
        formatted_sql = sqlparse.format(
            sql_query,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower'
        )
        return formatted_sql
    except Exception:
        # Return original if formatting fails
        return sql_query

def validate_sql(sql_query, schema):
    """
    Validate SQL query against a schema
    
    Args:
        sql_query (str): SQL query to validate
        schema (dict): Database schema
        
    Returns:
        dict: Validation result with success flag and error message if any
    """
    # Basic syntax validation
    if not sql_query:
        return {
            "valid": False,
            "error": "SQL query is empty"
        }
    
    # Check for SQL injection patterns
    potential_injection_patterns = [
        r"--",                  # SQL comment
        r"/\*.*?\*/",           # Block comment
        r";.*?;",               # Multiple statements
        r"EXEC\s+sp_",          # Stored procedure execution
        r"xp_cmdshell",         # Command shell
        r"UNION\s+ALL\s+SELECT" # UNION injection
    ]
    
    for pattern in potential_injection_patterns:
        if re.search(pattern, sql_query, re.IGNORECASE):
            return {
                "valid": False,
                "error": f"Potential SQL injection detected: {pattern}"
            }
    
    try:
        # Try parsing the SQL to check for syntax errors
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return {
                "valid": False,
                "error": "Failed to parse SQL query"
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"SQL syntax error: {str(e)}"
        }
    
    # Advanced validation could involve creating a temporary in-memory SQLite database
    # with the schema and trying to execute the query, but that's beyond the scope here
    
    return {
        "valid": True,
        "error": None
    }

def execute_query(sql_query, connection_string):
    """
    Execute SQL query against a database (if connected)
    
    Args:
        sql_query (str): SQL query to execute
        connection_string (str): Database connection string
        
    Returns:
        dict: Execution result with data, schema, and error message if any
    """
    if not connection_string:
        return {
            "success": False,
            "error": "No database connection provided",
            "data": None,
            "columns": None
        }
    
    try:
        engine = create_engine(connection_string)
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            
            if result.returns_rows:
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in result]
                
                return {
                    "success": True,
                    "error": None,
                    "data": data,
                    "columns": columns
                }
            else:
                return {
                    "success": True,
                    "error": None,
                    "data": [],
                    "columns": [],
                    "message": "Query executed successfully but returned no data"
                }
    
    except SQLAlchemyError as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "data": None,
            "columns": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}",
            "data": None,
            "columns": None
        }
