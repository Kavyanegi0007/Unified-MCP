# # # from fastmcp import FastMCP
# # # import logging
# # # #from app_tools.sql import list_tables, describe_table, query_customers
# # # from app_tools.web_db import image_search
# # # #from app_tools.azure_sql import azure_list_tables, azure_describe_table, azure_query_customers
# # # from app_tools.azure.azure_aisearch import search_similar

# # # from app_tools.azure.azure_sql import process_user_query 


# # # logging.basicConfig(level=logging.DEBUG)
# # # logger = logging.getLogger(__name__)

# # # mcp = FastMCP("database server")

# # # # #  SQL tools
# # # # mcp.tool(name="list_tables",
# # # #          description="lists all the tables")(list_tables)

# # # # mcp.tool(name="describe_table",
# # # #          description="describes tables")(describe_table)

# # # # mcp.tool(name="query_customers",
# # # #          description="queries all the tables")(query_customers)
# # # # Register tools from sql.py

# # # # Azure Ai search tools 

# # # mcp.tool(name="image_search", description="Searches for images using an image URL")(image_search)
# # # mcp.tool(name="search_similar", description="Displays the cumulative index of all video content")(search_similar)
# # # mcp.tool(name="process_user_query", description="Processes user queries on Azure SQL Database")(process_user_query)
# # # #add these tools based on the user requirements
# # # #user will give the desc during cofigurstin , that agent will use to pick the tool 
# # # #tool name will be made/fixed

# # # #final flow 

# # # #user opens the config page, and chooses azure db, in azure picks the sql db, then adds the connecton to their azure sql db and gives a desc about the tool that they have added 
# # # #now user has cnnected the server with their azure sql db and a desc about the tool, now they go to google db and connect with it also and add a desc about it
# # # #user goes to new page after connection and starting the mcp server and gives a query + info like fetch this from azure db +google db
# # # #agent will pick the tool based on the desc provided by the user during configuration and will cll the tool
# # # #before this, agent will process the user query and if the query is for sql then metadata schema connect of database for sql query , if the query is for image search then it will call the image search tool
# # # #in total there will be 3 llm calls, first for query + metadate schema connect of database for sql query , second for tool selection,  , third for final response generation



# # # # # Azure SQL endpoints
# # # # @mcp.tool("/azure_list_tables")
# # # # async def get_azure_tables():
# # # #     logger.debug("Calling azure_list_tables")
# # # #     return {"result": azure_list_tables()}

# # # # @mcp.tool("/azure_describe_table/{table_name}")
# # # # async def get_azure_table_structure(table_name: str):
# # # #     logger.debug(f"Calling azure_describe_table with table_name: {table_name}")
# # # #     return {"result": azure_describe_table(table_name)}

# # # # @mcp.tool("/azure_query_customers")
# # # # async def get_azure_customers():
# # # #     logger.debug("Calling azure_query_customers")
# # # #     return {"result": azure_query_customers()}
# # # if __name__ == "__main__":
# # #     mcp.run()
# # #__________________________new


# import logging
# import json
# import os
# from fastmcp import FastMCP
# from typing import Dict, Any, List
# import asyncio

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# # Initialize FastMCP server
# mcp = FastMCP("database server")

# def load_credentials(credentials_path: str = "/Users/kavyanegi/Downloads/MCP/credentials.json") -> List[Dict[str, Any]]:
#     """
#     Load credentials from a JSON file.
#     """
#     try:
#         with open(credentials_path, "r") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         logger.warning("Credentials file not found, using empty credentials")
#         return []
#     except json.JSONDecodeError:
#         logger.error("Invalid JSON format in credentials file")
#         return []

# def set_environment_variables(credentials: List[Dict[str, Any]]) -> None:
#     """
#     Set environment variables based on credentials.
#     """
#     for cred in credentials:
#         if cred.get("form_type") == "azure_ai_search":
#             os.environ["SERVICE_ENDPOINT"] = cred.get("service_endpoint", "")
#             os.environ["SEARCH_ADMIN_KEY"] = cred.get("search_admin_key", "")
#             os.environ["INDEX_NAME"] = cred.get("index_name", "")
#             os.environ["AZURE_AI_VISION_API_KEY"] = cred.get("ai_vision_key", "")
#             os.environ["AI_VISION_REGION"] = cred.get("ai_vision_region", "")
#             os.environ["AI_VISION_ENDPOINT"] = cred.get("ai_vision_endpoint", "")
#             os.environ["IMAGES_DIR"] = cred.get("default_images_dir", "")
#             logger.debug(f"Set Azure AI Search env vars: SERVICE_ENDPOINT={os.environ['SERVICE_ENDPOINT']}, "
#                         f"INDEX_NAME={os.environ['INDEX_NAME']}, "
#                         f"AI_VISION_KEY={'*' * 10 if os.environ['AZURE_AI_VISION_API_KEY'] else ''}, "
#                         f"AI_VISION_REGION={os.environ['AI_VISION_REGION']}, "
#                         f"AI_VISION_ENDPOINT={os.environ['AI_VISION_ENDPOINT']}, "
#                         f"IMAGES_DIR={os.environ['IMAGES_DIR']}")
#         elif cred.get("form_type") == "sql_database":
#             os.environ["SQL_SERVER"] = cred.get("sql_server", "")
#             os.environ["SQL_DATABASE"] = cred.get("sql_database", "")
#             os.environ["SQL_USERNAME"] = cred.get("sql_username", "")
#             os.environ["SQL_PASSWORD"] = cred.get("sql_password", "")
#             os.environ["SQL_DRIVER"] = cred.get("sql_driver", "")
#             logger.debug(f"Set SQL Database env vars: SQL_SERVER={os.environ['SQL_SERVER']}, "
#                         f"SQL_DATABASE={os.environ['SQL_DATABASE']}")
#         elif cred.get("form_type") == "google_database":
#             os.environ["SERP_API_KEY"] = cred.get("serp_api_key", "")
#             logger.debug(f"Set SERP_API_KEY for Google Database: {'*' * 10 if os.environ['SERP_API_KEY'] else ''}")

# def load_user_config(config_path: str = "/Users/kavyanegi/Downloads/MCP/credentials.json") -> Dict[str, Any]:
#     """
#     Load user configuration from a JSON file and map credentials to service configurations.
#     Returns a dictionary with a 'services' key containing service definitions.
#     """
#     try:
#         with open(config_path, "r") as f:
#             credentials = json.load(f)
#     except FileNotFoundError:
#         logger.warning("Config file not found, using default configuration")
#         credentials = []
#     except json.JSONDecodeError:
#         logger.error("Invalid JSON format in config file, using default configuration")
#         credentials = []

#     # Define mappings for form_type to service configurations
#     service_mappings = {
#         "azure_ai_search": [
#             {
#                 "type": "azure_ai_search",
#                 "description": "Searches for images using an image URL",
#                 "tool_name": "image_search"
#             },
#             {
#                 "type": "azure_ai_search",
#                 "description": "Displays the cumulative index of all video content",
#                 "tool_name": "search_similar"
#             }
#         ],
#         "sql_database": [
#             {
#                 "type": "azure_sql",
#                 "description": "Processes user queries on Azure SQL Database",
#                 "tool_name": "process_user_query"
#             }
#         ],
#         "google_database": [
#             {
#                 "type": "google_db",
#                 "description": "Queries Google Cloud SQL Database",
#                 "tool_name": "google_db_query"
#             }
#         ]
#     }

#     # Build services list based on credentials
#     services = []
#     for cred in credentials:
#         form_type = cred.get("form_type")
#         if form_type in service_mappings:
#             services.extend(service_mappings[form_type])
#         else:
#             logger.warning(f"Unknown form_type in config: {form_type}")


#     return {"services": services}

# def register_tools(config: Dict[str, Any]) -> None:
#     """
#     Register tools dynamically based on user configuration.
#     """
#     for service in config.get("services", []):
#         service_type = service.get("type")
#         tool_name = service.get("tool_name")
#         description = service.get("description")
#         if not all([service_type, tool_name, description]):
#             logger.error(f"Invalid service configuration: {service}")
#             continue
#         if service_type == "azure_ai_search":
#             # if tool_name == "image_search":
#             #     from app_tools.web_db import image_search
#             #     mcp.tool(name=tool_name, description=description)(image_search)
#             #     logger.debug(f"Registered tool: {tool_name} for Azure AI Search")
#             if tool_name == "search_similar":
#                 from app_tools.azure.azure_aisearch import search_similar
#                 mcp.tool(name=tool_name, description=description)(search_similar)
#                 logger.debug(f"Registered tool: {tool_name} for Azure AI Search")
#             else:
#                 logger.warning(f"Unknown tool {tool_name} for Azure AI Search")
#         elif service_type == "azure_sql":
#             if tool_name == "process_user_query":
#                 from app_tools.azure.azure_sql import process_user_query
#                 mcp.tool(name=tool_name, description=description)(process_user_query)
#                 logger.debug(f"Registered tool: {tool_name} for Azure SQL Database")
#             else:
#                 logger.warning(f"Unknown tool {tool_name} for Azure SQL Database")
#         elif service_type == "google_db":
#             if tool_name == "image_search":
                         
#                 from app_tools.web_db import image_search
#                 mcp.tool(name=tool_name, description=description)(image_search)
#                 logger.debug(f"Registered tool: {tool_name} for google search ")
    
#                 logger.warning(f"Unknown tool {tool_name} for Google Database")
#         else:
#             logger.warning(f"Unknown service type: {service_type}")

# async def process_query_llm(query: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     First LLM call: Process user query and combine with database metadata/schema.
#     """
#     logger.debug(f"Processing query with LLM: {query}")
#     return {
#         "processed_query": query,
#         "context": "Processed with metadata: " + str(metadata)
#     }

# async def select_tool_llm(processed_query: Dict[str, Any], tool_descriptions: List[Dict[str, str]]) -> str:
#     """
#     Second LLM call: Select the appropriate tool based on processed query and tool descriptions.
#     """
#     logger.debug(f"Selecting tool for processed query: {processed_query}")
#     query_text = processed_query.get("processed_query", "").lower()
#     for tool in tool_descriptions:
#         if any(keyword in query_text for keyword in tool["description"].lower().split()):
#             return tool["tool_name"]
#     return "process_user_query"

# async def generate_response_llm(processed_query: Dict[str, Any], tool_result: Any) -> str:
#     """
#     Third LLM call: Generate final response based on processed query and tool result.
#     """
#     logger.debug(f"Generating final response with tool result: {tool_result}")
#     return f"Final response: {tool_result}"

# async def handle_user_query(query: str, config: Dict[str, Any]) -> str:
#     """
#     Handle user query by processing it through three LLM calls and invoking the selected tool.
#     """
#     metadata = {"schema": "example_schema"}
#     processed_query = await process_query_llm(query, metadata)
#     tool_descriptions = [
#         {"tool_name": service["tool_name"], "description": service["description"]}
#         for service in config.get("services", [])
#     ]
#     selected_tool = await select_tool_llm(processed_query, tool_descriptions)
#     logger.debug(f"Selected tool: {selected_tool}")
#     tool_result = None
#     if selected_tool == "image_search":
#         from app_tools.web_db import image_search
#         tool_result = await image_search(query)
#     elif selected_tool == "search_similar":
#         from app_tools.azure.azure_aisearch import search_similar
#         tool_result = await search_similar(query)
#     elif selected_tool == "process_user_query":
#         from app_tools.azure.azure_sql import process_user_query
#         tool_result = await process_user_query(query)
#     elif selected_tool == "google_db_query":
#         try:
#             from app_tools.web_db import google_db_query
#             tool_result = await google_db_query(query)
#         except ImportError:
#             tool_result = "Error: Google DB query tool not implemented"
#     else:
#         tool_result = "Error: No valid tool selected"
#     final_response = await generate_response_llm(processed_query, tool_result)
#     return final_response

# if __name__ == "__main__":
#     # Load credentials and set environment variables
#     credentials = load_credentials()
#     set_environment_variables(credentials)
    
#     # Load user configuration
#     config = load_user_config()
    
#     # Register tools based on configuration
#     register_tools(config)
    
#     # Start the FastMCP server
#     mcp.run()


import logging
import json
import os
from fastmcp import FastMCP
from typing import Dict, Any, List
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("database server")

def load_credentials(credentials_path: str = "/Users/kavyanegi/Downloads/MCP/credentials.json") -> List[Dict[str, Any]]:
    """
    Load credentials from a JSON file.
    """
    try:
        with open(credentials_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Credentials file not found, using empty credentials")
        return []
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in credentials file")
        return []

def set_environment_variables(credentials: List[Dict[str, Any]]) -> None:
    """
    Set environment variables based on credentials.
    """
    for cred in credentials:
        if cred.get("form_type") == "azure_ai_search":
            os.environ["SERVICE_ENDPOINT"] = cred.get("service_endpoint", "")
            os.environ["SEARCH_ADMIN_KEY"] = cred.get("search_admin_key", "")
            os.environ["INDEX_NAME"] = cred.get("index_name", "")
            os.environ["AZURE_AI_VISION_API_KEY"] = cred.get("ai_vision_key", "")
            os.environ["AI_VISION_REGION"] = cred.get("ai_vision_region", "")
            os.environ["AI_VISION_ENDPOINT"] = cred.get("ai_vision_endpoint", "")
            os.environ["IMAGES_DIR"] = cred.get("default_images_dir", "")
            logger.debug(f"Set Azure AI Search env vars: SERVICE_ENDPOINT={os.environ.get('SERVICE_ENDPOINT', '')}, "
                        f"INDEX_NAME={os.environ.get('INDEX_NAME', '')}, "
                        f"AI_VISION_KEY={'*' * 10 if os.environ.get('AZURE_AI_VISION_API_KEY', '') else ''}, "
                        f"AI_VISION_REGION={os.environ.get('AI_VISION_REGION', '')}, "
                        f"AI_VISION_ENDPOINT={os.environ.get('AI_VISION_ENDPOINT', '')}, "
                        f"IMAGES_DIR={os.environ.get('IMAGES_DIR', '')}")
        elif cred.get("form_type") == "sql_database":
            os.environ["SQL_SERVER"] = cred.get("sql_server", "")
            os.environ["SQL_DATABASE"] = cred.get("sql_database", "")
            os.environ["SQL_USERNAME"] = cred.get("sql_username", "")
            os.environ["SQL_PASSWORD"] = cred.get("sql_password", "")
            os.environ["SQL_DRIVER"] = cred.get("sql_driver", "")
            logger.debug(f"Set SQL Database env vars: SQL_SERVER={os.environ.get('SQL_SERVER', '')}, "
                        f"SQL_DATABASE={os.environ.get('SQL_DATABASE', '')}")
        elif cred.get("form_type") == "google_database":
            os.environ["SERP_API_KEY"] = cred.get("serp_api_key", "")
            logger.debug(f"Set SERP_API_KEY for Google Database: {'*' * 10 if os.environ.get('SERP_API_KEY', '') else ''}")

def load_user_config(config_path: str = "/Users/kavyanegi/Downloads/MCP/credentials.json") -> Dict[str, Any]:
    """
    Load user configuration from a JSON file and map credentials to service configurations.
    Returns a dictionary with a 'services' key containing service definitions.
    """
    try:
        with open(config_path, "r") as f:
            credentials = json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, using default configuration")
        credentials = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in config file, using default configuration")
        credentials = []

    # Define mappings for form_type to service configurations
    service_mappings = {
        "azure_ai_search": [
            {
                "type": "azure_ai_search",
                "description": "Searches for images using an image URL",   #make this dynamic 
                "tool_name": "image_search"
            },
            {
                "type": "azure_ai_search",
                "description": "Displays the cumulative index of all video content",
                "tool_name": "search_similar"
            }
        ],
        "sql_database": [
            {
                "type": "azure_sql",
                "description": "Processes user queries on Azure SQL Database",
                "tool_name": "process_user_query"
            }
        ],
        "google_database": [
            {
                "type": "google_db",
                "description": "Queries Google Cloud SQL Database",
                "tool_name": "google_db_query"
            }
        ]
    }
#USE HTTPS AND UVICORN , 
#git stash 
    # Build services list based on credentials
    services = []
    for cred in credentials:
        form_type = cred.get("form_type")
        if form_type in service_mappings:
            services.extend(service_mappings[form_type])
        else:
            logger.warning(f"Unknown form_type in config: {form_type}")


    return {"services": services}

def register_tools(config: Dict[str, Any]) -> None:
    """
    Register tools dynamically based on user configuration.
    """
    for service in config.get("services", []):
        service_type = service.get("type")
        tool_name = service.get("tool_name")
        description = service.get("description")
        if not all([service_type, tool_name, description]):
            logger.error(f"Invalid service configuration: {service}")
            continue
        if service_type == "azure_ai_search":
            # if tool_name == "image_search":
            #     from app_tools.web_db import image_search
            #     mcp.tool(name=tool_name, description=description)(image_search)
            #     logger.debug(f"Registered tool: {tool_name} for Azure AI Search")
            if tool_name == "search_similar":
                from app_tools.azure.azure_aisearch import search_similar
                mcp.tool(name=tool_name, description=description)(search_similar)
                logger.debug(f"Registered tool: {tool_name} for Azure AI Search")
            else:
                logger.warning(f"Unknown tool {tool_name} for Azure AI Search")
        elif service_type == "azure_sql":
            if tool_name == "process_user_query":
                from app_tools.azure.azure_sql import process_user_query
                mcp.tool(name=tool_name, description=description)(process_user_query)
                logger.debug(f"Registered tool: {tool_name} for Azure SQL Database")
            else:
                logger.warning(f"Unknown tool {tool_name} for Azure SQL Database")
        elif service_type == "google_db":
            if tool_name == "image_search":
                         
                from app_tools.web_db import image_search
                mcp.tool(name=tool_name, description=description)(image_search)
                logger.debug(f"Registered tool: {tool_name} for Azure AI Search")
   
            else:
                logger.warning(f"Unknown tool {tool_name} for Google Database")
        else:
            logger.warning(f"Unknown service type: {service_type}")


if __name__ == "__main__":
    # Load credentials and set environment variables
    credentials = load_credentials()
    set_environment_variables(credentials)
    
    # Load user configuration
    config = load_user_config()
    
    # Register tools based on configuration
    register_tools(config)
    
    # Start the FastMCP server
    mcp.run()