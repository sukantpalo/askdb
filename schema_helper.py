import re
import pandas as pd
import sqlparse
import streamlit as st

def parse_schema_text(schema_text):
    """
    Parse schema text into a structured representation
    
    Args:
        schema_text (str): SQL schema definition
        
    Returns:
        dict: Structured schema representation
    """
    # Initialize schema dictionary
    schema = {
        "tables": [],
        "relationships": []
    }
    
    # Parse the schema using sqlparse
    statements = sqlparse.split(schema_text)
    
    for statement in statements:
        # Skip empty statements
        if not statement.strip():
            continue
            
        # Parse the statement
        parsed = sqlparse.parse(statement)[0]
        
        # Check if it's a CREATE TABLE statement
        if parsed.get_type() == 'CREATE' and any(token.value.upper() == 'TABLE' for token in parsed.tokens):
            # Extract table name
            table_info = {"name": "", "columns": [], "primary_keys": [], "foreign_keys": []}
            
            # Get table name
            for i, token in enumerate(parsed.tokens):
                if token.value.upper() == 'TABLE':
                    # Table name should be the next token
                    if i + 1 < len(parsed.tokens):
                        table_name_token = parsed.tokens[i + 1]
                        table_info["name"] = table_name_token.value.strip('`"\' ')
                        break
            
            # Extract column definitions and constraints
            in_paren = None
            for token in parsed.tokens:
                if token.ttype is None and token.is_group:
                    if '(' in token.value and ')' in token.value:
                        in_paren = token
                        break
            
            if in_paren:
                # Process column definitions and constraints
                column_definitions = [t for t in in_paren.tokens if t.ttype is None and t.value not in ['(', ')', ',', ' ']]
                
                for col_def in column_definitions:
                    col_text = col_def.value.strip()
                    
                    # Skip if empty
                    if not col_text:
                        continue
                    
                    # Check if it's a constraint
                    if col_text.upper().startswith(('PRIMARY KEY', 'FOREIGN KEY', 'CONSTRAINT')):
                        # Primary key constraint
                        if 'PRIMARY KEY' in col_text.upper():
                            pk_match = re.search(r'PRIMARY\s+KEY\s*\(\s*([^)]+)\s*\)', col_text, re.IGNORECASE)
                            if pk_match:
                                pk_columns = [c.strip('`"\' ') for c in pk_match.group(1).split(',')]
                                table_info["primary_keys"].extend(pk_columns)
                        
                        # Foreign key constraint
                        if 'FOREIGN KEY' in col_text.upper():
                            fk_match = re.search(r'FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s*REFERENCES\s*([^\s(]+)\s*\(\s*([^)]+)\s*\)', col_text, re.IGNORECASE)
                            if fk_match:
                                fk_columns = [c.strip('`"\' ') for c in fk_match.group(1).split(',')]
                                ref_table = fk_match.group(2).strip('`"\' ')
                                ref_columns = [c.strip('`"\' ') for c in fk_match.group(3).split(',')]
                                
                                for i, fk_col in enumerate(fk_columns):
                                    ref_col = ref_columns[i] if i < len(ref_columns) else ref_columns[-1]
                                    table_info["foreign_keys"].append({
                                        "column": fk_col,
                                        "reference_table": ref_table,
                                        "reference_column": ref_col
                                    })
                                    
                                    # Add relationship to schema
                                    schema["relationships"].append({
                                        "from_table": table_info["name"],
                                        "from_column": fk_col,
                                        "to_table": ref_table,
                                        "to_column": ref_col
                                    })
                        
                    else:
                        # Regular column definition
                        col_parts = col_text.split(' ', 1)
                        if len(col_parts) >= 2:
                            col_name = col_parts[0].strip('`"\' ')
                            col_type = col_parts[1].strip()
                            
                            # Check if it has PRIMARY KEY constraint inline
                            is_primary = 'PRIMARY KEY' in col_type.upper()
                            if is_primary:
                                table_info["primary_keys"].append(col_name)
                                col_type = col_type.replace('PRIMARY KEY', '').replace('primary key', '').strip()
                            
                            # Add column to table info
                            table_info["columns"].append({
                                "name": col_name,
                                "type": col_type,
                                "is_primary": is_primary
                            })
            
            # Add table to schema
            schema["tables"].append(table_info)
    
    return schema

def schema_to_visual(schema):
    """
    Convert schema to a visual representation
    
    Args:
        schema (dict): Structured schema representation
        
    Returns:
        str: Visual representation of the schema
    """
    if not schema or "tables" not in schema:
        return "No schema available"
    
    # Create a DataFrame to display the tables
    tables_data = []
    
    for table in schema["tables"]:
        table_name = table["name"]
        
        for column in table["columns"]:
            col_name = column["name"]
            col_type = column["type"]
            is_primary = column["is_primary"] or col_name in table["primary_keys"]
            
            # Check if it's a foreign key
            is_foreign = False
            reference = ""
            for fk in table["foreign_keys"]:
                if fk["column"] == col_name:
                    is_foreign = True
                    reference = f"{fk['reference_table']}.{fk['reference_column']}"
                    break
            
            tables_data.append({
                "Table": table_name,
                "Column": col_name,
                "Type": col_type,
                "PK": "✓" if is_primary else "",
                "FK": "✓" if is_foreign else "",
                "References": reference if is_foreign else ""
            })
    
    # Create DataFrame
    df = pd.DataFrame(tables_data)
    
    # Group by table
    tables_html = []
    
    for table_name, group in df.groupby("Table"):
        table_df = group[["Column", "Type", "PK", "FK", "References"]].copy()
        tables_html.append(f"### Table: {table_name}")
        tables_html.append(table_df.to_html(index=False, escape=False))
    
    return "\n\n".join(tables_html)
