# from openai import AzureOpenAI
# import pyodbc
# import numpy as np
# import time
# import json

# # Azure OpenAI Config
# AZURE_OPENAI_API_KEY = "BmaiYil8P7o3Dgv0JzIEIA4JYd3AHl7Jh6SzBdjkwXfF4DNxCzC3JQQJ99BGACYeBjFXJ3w3AAABACOGZkhi"
# AZURE_OPENAI_API_BASE = "https://gpt-4o-intern.openai.azure.com" 
# EMBEDDING_MODEL = "text-embedding-3-small"
# AZURE_OPENAI_API_VERSION = "2024-02-01"



# # AZURE_OPENAI_ENDPOINT = "https://gpt-4o-intern.openai.azure.com/"
# # AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4o-08-06"
# # AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
# # AZURE_OPENAI_API_KEY = "BmaiYil8P7o3Dgv0JzIEIA4JYd3AHl7Jh6SzBdjkwXfF4DNxCzC3JQQJ99BGACYeBjFXJ3w3AAABACOGZkhi"
# # # Azure SQL Config
# SQL_SERVER = "sqlinternserver.database.windows.net"
# SQL_DATABASE = "sqlintern_database"
# SQL_USERNAME = "sqlserverintern"
# SQL_PASSWORD = "intern@12345"
# SQL_DRIVER = "{ODBC Driver 18 for SQL Server}"

# # Initialize Azure OpenAI client
# client = AzureOpenAI(
#     api_key=AZURE_OPENAI_API_KEY,
#     api_version=AZURE_OPENAI_API_VERSION,
#     azure_endpoint=AZURE_OPENAI_API_BASE
# )

# def generate_embedding(text):
#     """Generate embedding for query text using Azure OpenAI"""
#     embedding_data = client.embeddings.create(
#         input=[text],
#         model=EMBEDDING_MODEL
#     )
#     embedding_list = embedding_data.data[0].embedding
#     return np.array(embedding_list, dtype=np.float32)

# def search_sql_vectors(query_text, top_k=5):
#     """
#     Search for similar documents in SQL Server using vector similarity
#     """
#     start_time = time.time()
    
#     # Generate embedding for query
#     query_embedding = generate_embedding(query_text)
    
#     # Connect to SQL Server
#     conn = pyodbc.connect(
#         f'DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}'
#     )
#     cursor = conn.cursor()
    
#     # SQL Server vector similarity search using VECTOR_DISTANCE
#     # Using cosine distance (lower is better/more similar)
#     search_query = '''
#     SELECT TOP (?)
#         ID,
#         PDF_Name,
#         DocumentId,
#         Content,
#         VECTOR_DISTANCE('cosine', VectorBinary, CAST(? AS VECTOR(1536))) AS Distance
#     FROM dbo.HRs4
#     ORDER BY Distance ASC
#     '''
    
#     # Execute search
#     cursor.execute(search_query, top_k, query_embedding.tobytes())
    
#     # Fetch results
#     results = []
#     for row in cursor.fetchall():
#         results.append({
#             "id": row[0],
#             "pdf_name": row[1],
#             "document_id": row[2],
#             "content": row[3].replace('\n', ' ').strip(),
#             "distance": float(row[4])  # Lower distance = more similar
#         })
    
#     cursor.close()
#     conn.close()
    
#     end_time = time.time()
    
#     return results, end_time - start_time

# # Example usage
# if __name__ == "__main__":
#     query = "what are differences between sabbatical, sick and paid leave?"
    
#     print(f"Searching for: '{query}'\n")
    
#     results, search_time = search_sql_vectors(query, top_k=5)
    
#     print(f"Search completed in {search_time:.3f} seconds")
#     print(f"\nTop {len(results)} Most Similar Documents:\n")
#     print("=" * 80)
    
#     for i, result in enumerate(results, 1):
#         print(f"\n{i}. PDF: {result['pdf_name']}")
#         print(f"   Document ID: {result['document_id']}")
#         print(f"   Similarity Score: {1 - result['distance']:.4f}")  # Convert distance to similarity
#         print(f"   Distance: {result['distance']:.4f}")
#         print(f"   Content Preview: {result['content'][:200]}...")
#         print("-" * 80)




import urllib
from sqlalchemy import create_engine, inspect

import os
import pyodbc
from openai import AzureOpenAI

# Azure SQL Server configuration
SQL_SERVER = "sqlinternserver.database.windows.net"
SQL_DATABASE = "sqlintern_database"
SQL_USERNAME = "sqlserverintern"
SQL_PASSWORD = "intern@12345"
SQL_DRIVER = "ODBC Driver 18 for SQL Server"

# Set the schema name
schema_name = "Table"

# Step 1: Create connection string for Azure SQL Database
connection_string = (
    f"mssql+pyodbc:///?odbc_connect="
    f"{urllib.parse.quote_plus(f'DRIVER={SQL_DRIVER};SERVER={SQL_SERVER};DATABASE={SQL_DATABASE};UID={SQL_USERNAME};PWD={SQL_PASSWORD}')}"
)

# Step 2: Create the SQLAlchemy engine
engine = create_engine(connection_string)

# Step 3: Function to fetch column names from the specified schema
def get_column_names(engine, schema_name):
    """
    Retrieve column names for all tables in the specified schema.
    
    Args:
        engine: SQLAlchemy engine object for database connection.
        schema_name (str): Name of the schema to inspect.
    
    Returns:
        str: A formatted string listing table names and their column names.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema=schema_name)
    result = ""
    
    if not tables:
        return f"No tables found in schema '{schema_name}'.\n"
    
    for table_name in tables:
        columns = inspector.get_columns(table_name, schema=schema_name)
        column_names = [column['name'] for column in columns]
        result += f"Table: {schema_name}.{table_name}\nColumns: {', '.join(column_names)}\n\n"
    
    return result

# Step 4: Fetch and print column names from the specified schema
column_names_output = get_column_names(engine, schema_name)
print(column_names_output)

# Step 5: Dispose of the engine to close connections
engine.dispose()
#________________________

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = "https://gpt-4o-intern.openai.azure.com/"
#AZURE_OPENAI_DEPLOYMENT_NAME = "text-embedding-3-small"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
AZURE_OPENAI_API_KEY = "BmaiYil8P7o3Dgv0JzIEIA4JYd3AHl7Jh6SzBdjkwXfF4DNxCzC3JQQJ99BGACYeBjFXJ3w3AAABACOGZkhi"

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# # Azure SQL Server configuration
# SQL_SERVER = "sqlinternserver.database.windows.net"
# SQL_DATABASE = "sqlintern_database"
# SQL_USERNAME = "sqlserverintern"
# SQL_PASSWORD = "intern@12345"
# SQL_DRIVER = "{ODBC Driver 18 for SQL Server}"

# Establish Azure SQL connection
conn_str = (
    f"Driver={SQL_DRIVER};"
    f"Server={SQL_SERVER};"
    f"Database={SQL_DATABASE};"
    f"Uid={SQL_USERNAME};"
    f"Pwd={SQL_PASSWORD};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Function to generate SQL query using Azure OpenAI
def generate_sql_query(natural_language_query, sql_schema=column_names_output):
    prompt = f"""
You are an expert SQL query generator for Azure SQL Server.

Below is the database schema in a structured format:

{sql_schema}

Your task:
- Write a valid SQL query to answer the question: "{natural_language_query}"
- Only use tables and columns present in the schema above.
- Return **only the SQL query**, no explanation or extra text.
- Use standard Azure SQL syntax (square brackets for identifiers if needed).
"""

    response = client.chat.completions.create(
        model="gpt-4o-08-06",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    sql_query = response.choices[0].message.content.strip()
    # Remove any potential code fences or backticks
    sql_query = sql_query.replace('```sql', '').replace('```', '').replace('`', '')
    return sql_query.strip()

# Function to execute SQL query and retrieve results
def execute_sql_query(sql_query):
    try:
        cursor.execute(sql_query)
        return [list(row) for row in cursor.fetchall()]
    except pyodbc.Error as e:
        print(f"SQL Error: {e}")
        raise

# Function to summarize SQL results in natural language
def summarize_sql_results(results, user_query):
    results_text = str(results)
    summary_prompt = f"""
        Based on the SQL query results: {results_text}
        Provide a concise natural-language answer to the question: {user_query}
    """
    response = client.chat.completions.create(
        model="gpt-4o-08-06",
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# Main pipeline to process user query
def process_user_query(user_query):
    sql_query = generate_sql_query(user_query)
    print("Generated SQL Query:", sql_query)
    results = execute_sql_query(sql_query)
    print("Query Results:", results)
    summary = summarize_sql_results(results, user_query)
    print("Summary Answer:", summary)
    return summary

# Example usage
if __name__ == "__main__":
    try:
        user_query = "What are the differences between sabbatical, sick, and paid leave?"
        process_user_query(user_query)
    finally:
        # Clean up database connection
        cursor.close()
        conn.close()