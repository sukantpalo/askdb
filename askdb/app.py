import streamlit as st
import json
import os
from utils.openai_helper import nl_to_sql, analyze_schema
from utils.sql_helper import validate_sql, format_sql
from utils.schema_helper import parse_schema_text, schema_to_visual
from examples.sample_schemas import SAMPLE_SCHEMAS

# Page configuration
st.set_page_config(
    page_title="NL to SQL Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

if "schema" not in st.session_state:
    st.session_state.schema = None

if "schema_text" not in st.session_state:
    st.session_state.schema_text = ""

if "schema_visual" not in st.session_state:
    st.session_state.schema_visual = None

if "example_queries" not in st.session_state:
    st.session_state.example_queries = []

# Header
st.title("💬 Natural Language to SQL Chat")
st.write("""
Ask questions about your database in plain English, and I'll convert them to SQL queries!
""")

# Sidebar for schema input and settings
with st.sidebar:
    st.header("Database Schema")
    
    schema_source = st.radio(
        "Select schema source:",
        ["Sample Schemas", "Custom Schema"]
    )
    
    if schema_source == "Sample Schemas":
        schema_selection = st.selectbox(
            "Choose a sample schema:",
            list(SAMPLE_SCHEMAS.keys())
        )
        
        if st.button("Load Sample Schema"):
            selected_schema = SAMPLE_SCHEMAS[schema_selection]
            st.session_state.schema_text = selected_schema
            try:
                st.session_state.schema = parse_schema_text(selected_schema)
                st.session_state.schema_visual = schema_to_visual(st.session_state.schema)
                
                # Generate example queries based on the schema
                with st.spinner("Generating example queries..."):
                    example_queries = analyze_schema(st.session_state.schema_text)
                    st.session_state.example_queries = example_queries
                
                st.success("Schema loaded successfully!")
            except Exception as e:
                st.error(f"Failed to parse schema: {str(e)}")
    else:
        st.session_state.schema_text = st.text_area(
            "Enter your database schema:",
            height=300,
            placeholder="CREATE TABLE users (\n  id INTEGER PRIMARY KEY,\n  name TEXT,\n  email TEXT\n);\n\nCREATE TABLE orders (\n  id INTEGER PRIMARY KEY,\n  user_id INTEGER,\n  amount REAL,\n  created_at TIMESTAMP,\n  FOREIGN KEY (user_id) REFERENCES users(id)\n);"
        )
        
        if st.button("Parse Schema"):
            try:
                st.session_state.schema = parse_schema_text(st.session_state.schema_text)
                st.session_state.schema_visual = schema_to_visual(st.session_state.schema)
                
                # Generate example queries based on the schema
                with st.spinner("Generating example queries..."):
                    example_queries = analyze_schema(st.session_state.schema_text)
                    st.session_state.example_queries = example_queries
                
                st.success("Schema parsed successfully!")
            except Exception as e:
                st.error(f"Failed to parse schema: {str(e)}")
    
    st.divider()
    
    # Example queries section
    if st.session_state.example_queries:
        st.header("Example Queries")
        for i, query in enumerate(st.session_state.example_queries):
            if st.button(f"📝 {query}", key=f"example_{i}"):
                # Add the example query to the chat
                st.session_state.messages.append({"role": "user", "content": query})
                
                # Process the example query
                with st.spinner("Generating SQL..."):
                    sql_result = nl_to_sql(
                        query,
                        st.session_state.schema_text
                    )
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": sql_result
                    })
                st.rerun()

# Main chat interface
if st.session_state.schema is None:
    st.info("👈 Please select or input a database schema to get started.")
else:
    # Display schema visualization
    st.header("Database Schema")
    st.write(st.session_state.schema_visual)
    
    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and isinstance(message["content"], dict):
                # Display SQL query with explanation
                sql_result = message["content"]
                st.code(sql_result["sql"], language="sql")
                st.write("**Explanation:**")
                st.write(sql_result["explanation"])
                
                if "error" in sql_result and sql_result["error"]:
                    st.error(sql_result["error"])
            else:
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data in plain English"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate SQL from natural language
        with st.spinner("Thinking..."):
            with st.chat_message("assistant"):
                try:
                    sql_result = nl_to_sql(
                        prompt,
                        st.session_state.schema_text
                    )
                    
                    # Display SQL with syntax highlighting
                    st.code(sql_result["sql"], language="sql")
                    
                    # Display explanation
                    st.write("**Explanation:**")
                    st.write(sql_result["explanation"])
                    
                    # Check for errors
                    if "error" in sql_result and sql_result["error"]:
                        st.error(sql_result["error"])
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": sql_result
                    })
                except Exception as e:
                    error_message = f"Error generating SQL: {str(e)}"
                    st.error(error_message)
                    
                    # Add error message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": {"sql": "", "explanation": "", "error": error_message}
                    })

# Clear chat button
if st.session_state.messages:
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
