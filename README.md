# MCP & ACP Configuration System

A comprehensive Model Context Protocol (MCP) orchestrator integrated with Azure OpenAI for intelligent tool selection and query processing. This system provides a flexible framework for connecting multiple data sources (Azure SQL, Azure AI Search, Google Search) and AI services through an intuitive Streamlit interface.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Available Tools](#available-tools)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

This project implements a **Model Context Protocol (MCP)** server that acts as a bridge between:
- **Data Sources**: Azure SQL Database, Azure AI Search (image similarity), Google Search via SerpAPI
- **AI Services**: Azure OpenAI for intelligent query routing and natural language processing
- **User Interfaces**: Streamlit web UI, command-line interface

The system uses Azure OpenAI to intelligently decide which tools/services to call based on user queries, making it a smart orchestrator that can handle diverse requests from SQL queries to image similarity searches.

## Features

### Core Features
- **MCP Server**: FastMCP-based server with dynamic tool registration
- **Azure OpenAI Integration**: GPT-4o for intelligent decision-making and query routing
- **Multi-Source Support**:
  - Azure SQL Database with natural language query generation
  - Azure AI Search with vector-based image similarity
  - Google Search via SerpAPI for web image search
- **Async Operations**: Full async/await support for concurrent operations
- **Streamlit UI**: Beautiful Affine-themed configuration and chat interface
- **Error Handling**: Robust error handling with detailed logging

### MCP Orchestrator Features
- **Intelligent Tool Selection**: Azure OpenAI decides which tool to use based on query context
- **Response Synthesis**: Natural language responses from structured tool outputs
- **Context Management**: Maintains conversation context and tool metadata
- **Stdio Communication**: Standard MCP protocol for tool communication

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Interface                         │
│  (Streamlit UI / CLI / Interactive Mode)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Orchestrator (main2.py)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Azure OpenAI Decision Engine                │  │
│  │  • Analyzes user query                               │  │
│  │  • Selects appropriate tool                          │  │
│  │  • Synthesizes natural language response             │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            MCP Client (stdio)                        │  │
│  │  • Communicates with MCP server                      │  │
│  │  • Manages tool calls                                │  │
│  │  • Handles streaming responses                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server (server.py)                     │
│  • Dynamic tool registration based on credentials.json      │
│  • Environment variable management                          │
│  • Tool routing and execution                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Tool Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │  Azure SQL   │  │  Azure AI    │  │  Google Search   │ │
│  │   (SQL DB)   │  │   Search     │  │   (SerpAPI)      │ │
│  │              │  │  (Images)    │  │                  │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Services
1. **Azure OpenAI**: GPT-4o deployment for orchestration
2. **Azure SQL Database** (optional): For SQL query processing
3. **Azure AI Search** (optional): For image similarity search
4. **Azure AI Vision** (optional): For image vectorization
5. **SerpAPI** (optional): For Google web search

### Software Requirements
- Python 3.13+
- ODBC Driver 18 for SQL Server (if using Azure SQL)
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository
```bash
cd /path/to/your/workspace
# Assuming the project is already at /Users/kavyanegi/Downloads/MCP
cd MCP
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Additional Requirements for MCP
```bash
pip install fastmcp mcp streamlit
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Azure OpenAI (REQUIRED)
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_DEPLOYMENT=gpt-4o-08-06

# Azure AI Vision (Required for image search)
AZURE_AI_VISION_API_KEY=your_vision_api_key_here
AZURE_AI_VISION_REGION=eastus
AZURE_AI_VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com/

# Optional: Will be set via UI or credentials.json
SERVICE_ENDPOINT=https://your-search-service.search.windows.net
INDEX_NAME=your-index-name
SEARCH_ADMIN_KEY=your_search_admin_key
IMAGES_DIR=/path/to/images

# SQL Database (Optional: Will be set via UI)
SQL_SERVER=your-server.database.windows.net
SQL_DATABASE=your-database
SQL_USERNAME=your-username
SQL_PASSWORD=your-password
SQL_DRIVER={ODBC Driver 18 for SQL Server}

# Google Search (Optional: Will be set via UI)
SERP_API_KEY=your_serpapi_key
```

### 2. Credentials Configuration

Create `credentials.json` to configure data sources:

```json
[
  {
    "form_type": "sql_database",
    "sql_server": "server.database.windows.net",
    "sql_database": "MyDatabase",
    "sql_username": "admin",
    "sql_password": "password",
    "sql_driver": "{ODBC Driver 18 for SQL Server}",
    "tool_description": "Processes queries on Azure SQL Database containing HR data"
  },
  {
    "form_type": "azure_ai_search",
    "service_endpoint": "https://search-service.search.windows.net",
    "search_admin_key": "your_key",
    "index_name": "images-index",
    "ai_vision_key": "your_vision_key",
    "ai_vision_region": "eastus",
    "ai_vision_endpoint": "https://vision-resource.cognitiveservices.azure.com/",
    "default_images_dir": "/path/to/images",
    "tool_description": "Searches for similar images using vector embeddings"
  },
  {
    "form_type": "google_database",
    "serp_api_key": "your_serpapi_key",
    "tool_description": "Searches the web for similar images using Google Lens"
  }
]
```

**⚠️ IMPORTANT**: Never commit `credentials.json` or `.env` files to version control. Add them to `.gitignore`.

## Usage

### 1. Streamlit UI (Recommended)

The Streamlit interface provides a visual way to configure services and interact with the MCP orchestrator.

```bash
streamlit run st5.py
```

Features:
- Configure Azure SQL, Azure AI Search, and Google Search
- View MCP connection status
- Chat with the orchestrator
- Upload images for similarity search
- View available tools and their descriptions

### 2. MCP Orchestrator (Command Line)

#### Interactive Mode
```bash
python main2.py
```

This starts an interactive chat session where you can:
- Ask questions about your SQL database
- Search for similar images
- Get intelligent responses synthesized by Azure OpenAI

Example queries:
```
💬 You: What are the differences between sabbatical, sick, and paid leave?
💬 You: Find images similar to /path/to/image.jpg
💬 You: How many employees are in the database?
```

#### Single Query Mode
```bash
python main2.py --query "What are the top 5 products by sales?"
```

### 3. Direct Server Usage

Start the MCP server directly:

```bash
python server.py
```

The server will:
1. Load credentials from `credentials.json`
2. Set environment variables
3. Register tools dynamically
4. Start FastMCP server on stdio

## Project Structure

```
MCP/
├── main2.py                      # MCP Orchestrator with Azure OpenAI
├── server.py                     # FastMCP Server with dynamic tool registration
├── st5.py                        # Streamlit UI for configuration and chat
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (NOT in git)
├── credentials.json              # Data source credentials (NOT in git)
├── .gitignore                    # Git ignore rules
│
├── app_tools/                    # Tool implementations
│   ├── __init__.py
│   ├── azure/
│   │   ├── azure_sql.py         # Azure SQL Database integration
│   │   └── azure_aisearch.py    # Azure AI Search + Vision integration
│   └── web_db.py                # Google Search via SerpAPI
│
├── images/                       # Image storage for similarity search
├── results/                      # Search results storage
└── unused/                       # Archived/experimental code
```

### Key Files

#### `main2.py`
- **MCPStdioClient**: Manages stdio communication with MCP server
- **AzureOpenAIOrchestrator**: Uses GPT-4o for tool selection and response synthesis
- **MCPOrchestrator**: Main orchestrator coordinating client and LLM

#### `server.py`
- Loads `credentials.json` and sets environment variables
- Dynamically registers tools based on configuration
- Maps form types to tool implementations
- Runs FastMCP server

#### `st5.py`
- Streamlit UI with Affine theme
- Configuration panels for each service
- MCP chat interface
- Image upload and search functionality

#### `app_tools/azure/azure_sql.py`
- Connects to Azure SQL Database
- Uses GPT-4o to generate SQL from natural language
- Executes queries and returns results
- Summarizes results in natural language

#### `app_tools/azure/azure_aisearch.py`
- Generates image vectors using Azure AI Vision
- Performs vector similarity search in Azure AI Search
- Returns similar images with metadata

#### `app_tools/web_db.py`
- Uses SerpAPI's Google Lens engine
- Searches web for visually similar images
- Returns top matches with titles and URLs

## Available Tools

### 1. `process_user_query` (Azure SQL)
**Description**: Processes natural language queries on Azure SQL Database

**Input**:
```json
{
  "user_query": "What are the differences between sabbatical and sick leave?"
}
```

**Output**:
```json
{
  "success": true,
  "content": ["Natural language answer based on SQL results"]
}
```

### 2. `search_similar` (Azure AI Search)
**Description**: Finds similar images using vector embeddings

**Input**:
```json
{
  "query_image_path": "/path/to/image.jpg",
  "k": 5
}
```

**Output**:
```json
{
  "success": true,
  "content": [
    {
      "description": "Image description",
      "decoded_path": "/path/to/similar/image.jpg",
      "exists": true,
      "score": 0.95
    }
  ]
}
```

### 3. `image_search` (Google Search)
**Description**: Searches web for visually similar images using Google Lens

**Input**:
```json
{
  "image_url": "https://example.com/image.jpg",
  "num": 5
}
```

**Output**:
```json
{
  "success": true,
  "content": [
    {
      "title": "Similar image title",
      "thumbnail": "https://...",
      "url": "https://...",
      "source": "example.com"
    }
  ]
}
```

## Security Considerations

### ⚠️ Critical Security Issues

**NEVER** hardcode credentials in source code. The current codebase has some hardcoded credentials that must be removed:

1. **Move all credentials to environment variables**:
   ```bash
   # Bad (hardcoded in code)
   SQL_PASSWORD = "intern@12345"

   # Good (from environment)
   SQL_PASSWORD = os.getenv("SQL_PASSWORD")
   ```

2. **Rotate compromised credentials immediately**:
   - Any credentials that were committed to git should be rotated
   - Change all API keys and passwords in Azure portal

3. **Use `.gitignore`**:
   ```
   .env
   credentials.json
   *.log
   __pycache__/
   venv/
   ```

4. **Use Azure Key Vault** (Recommended):
   ```python
   from azure.identity import DefaultAzureCredential
   from azure.keyvault.secrets import SecretClient

   credential = DefaultAzureCredential()
   client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)
   secret = client.get_secret("sql-password")
   ```

### Best Practices

1. **Environment Variables**: Always use `.env` file or environment variables for secrets
2. **Credential Rotation**: Rotate credentials regularly
3. **Least Privilege**: Use service accounts with minimal required permissions
4. **Audit Logging**: Enable audit logging on Azure SQL and other services
5. **Network Security**: Use private endpoints and VNets where possible

## Troubleshooting

### Issue: MCP Connection Failed

**Error**: `RuntimeError: Attempted to exit cancel scope in a different task`

**Solution**: This is a harmless cleanup warning from the MCP SDK. The connection still works. The error is suppressed in the latest version of `main2.py`.

### Issue: Azure OpenAI API Error

**Error**: `401 Unauthorized` or `API key invalid`

**Solution**:
1. Verify your API key in `.env`
2. Check that your Azure OpenAI endpoint is correct
3. Ensure your deployment name matches `AZURE_DEPLOYMENT`
4. Verify API version is supported

### Issue: SQL Connection Failed

**Error**: `Login failed for user` or `Server not found`

**Solution**:
1. Verify your SQL Server firewall allows your IP
2. Check username/password in `credentials.json` or `.env`
3. Ensure ODBC Driver 18 is installed
4. Test connection with Azure Data Studio

### Issue: Image Search Returns No Results

**Error**: No similar images found

**Solution**:
1. Verify Azure AI Vision credentials
2. Check that your index contains vector embeddings
3. Ensure image path is valid and readable
4. Verify Azure AI Search index name is correct

### Issue: Import Errors

**Error**: `ModuleNotFoundError: No module named 'mcp'`

**Solution**:
```bash
pip install fastmcp mcp
pip install -r requirements.txt
```

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push and create a pull request

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to all functions
- Keep functions focused and small
- Write unit tests for new features

### Testing

```bash
# Test individual components
python app_tools/azure/azure_sql.py
python app_tools/azure/azure_aisearch.py
python app_tools/web_db.py

# Test MCP server
python server.py

# Test orchestrator
python main2.py --query "test query"
```

## License

This project is proprietary. All rights reserved.

## Support

For issues and questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs in `search_index.log`
3. Enable DEBUG logging: `logging.basicConfig(level=logging.DEBUG)`
4. Contact the development team

---

**Version**: 1.0.0
**Last Updated**: October 2024
**Python**: 3.13+
**Status**: Production
