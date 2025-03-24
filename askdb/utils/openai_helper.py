import os
import json
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_MODEL = "gpt-4o"

# Initialize OpenAI client
os.environ['OPENAI_API_KEY'] = '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'
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def nl_to_sql(query, schema):
    """
    Convert natural language query to SQL using OpenAI API
    
    Args:
        query (str): Natural language query
        schema (str): Database schema in SQL format
        
    Returns:
        dict: SQL query, explanation, and optional error
    """
    if not OPENAI_API_KEY:
        return {
            "sql": "",
            "explanation": "",
            "error": "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable."
        }
    
    system_prompt = """
    You are an expert SQL generator that converts natural language questions into accurate SQL queries.
    Given a database schema and a natural language question, generate the most appropriate SQL query.
    
    Provide your response in JSON format with the following fields:
    - sql: The generated SQL query
    - explanation: A step-by-step explanation of how the SQL query works and why you chose this approach
    
    Important:
    - Use only tables and columns from the provided schema
    - Avoid using functions that might not exist in all SQL implementations
    - For ambiguous questions, make reasonable assumptions
    - If the query is impossible to generate with the given schema, provide an explanation why
    """
    
    user_prompt = f"""
    Database Schema:
    ```
    {schema}
    ```
    
    Natural Language Question:
    ```
    {query}
    ```
    
    Generate a SQL query that answers this question based on the schema.
    """
    
    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure we have the required fields
        if "sql" not in result:
            result["sql"] = ""
        if "explanation" not in result:
            result["explanation"] = "No explanation provided."
            
        return result
    
    except Exception as e:
        return {
            "sql": "",
            "explanation": "",
            "error": f"Error while generating SQL: {str(e)}"
        }

def analyze_schema(schema):
    """
    Analyze a database schema and generate example natural language queries
    
    Args:
        schema (str): Database schema in SQL format
        
    Returns:
        list: Example natural language queries
    """
    if not OPENAI_API_KEY:
        return ["How many users do we have?", 
                "What is the total sales amount?", 
                "Find the top 5 customers by order value"]
    
    system_prompt = """
    You are an expert at analyzing database schemas and generating useful example queries.
    Given a database schema, generate 5 useful natural language questions that users might ask.
    
    Provide your response as a JSON array of strings, where each string is a natural language question.
    
    Your questions should:
    - Cover a range of SQL features (selects, joins, grouping, filtering, etc.)
    - Be diverse and practical
    - Reference actual tables and columns from the schema
    - Be phrased as natural language questions, not SQL
    """
    
    user_prompt = f"""
    Database Schema:
    ```
    {schema}
    ```
    
    Generate 5 diverse and practical natural language questions that users might ask about this database.
    """
    
    try:
        response = openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Handle different possible JSON structures
        if isinstance(result, list):
            return result
        elif "questions" in result:
            return result["questions"]
        elif "examples" in result:
            return result["examples"]
        else:
            # Try to extract any list from the response
            for key, value in result.items():
                if isinstance(value, list) and len(value) > 0:
                    return value
            
            # Fallback to default questions if we can't parse the response
            return ["How many users do we have?", 
                    "What is the total sales amount?", 
                    "Find the top 5 customers by order value",
                    "What is the average order value?",
                    "Which products were ordered most frequently?"]
    
    except Exception as e:
        # Return default questions on error
        return ["How many users do we have?", 
                "What is the total sales amount?", 
                "Find the top 5 customers by order value",
                "What is the average order value?",
                "Which products were ordered most frequently?"]
