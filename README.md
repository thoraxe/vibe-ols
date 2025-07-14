# Vibe OLS - FastAPI with Streamlit Frontend

A Python FastAPI application with a Streamlit frontend that provides AI-powered OpenShift troubleshooting, investigation, and inbox management capabilities.

## Features

- **FastAPI Backend** with six endpoints:
  - `/` - API information and available endpoints
  - `/query` - AI-powered OpenShift troubleshooting queries (powered by Pydantic AI)
  - `/query/stream` - Real-time streaming OpenShift troubleshooting queries
  - `/investigate` - Comprehensive OpenShift investigation with AI agent
  - `/investigate/stream` - Real-time streaming investigation with live progress updates
  - `/inbox` - Handle inbox messages with optional metadata

- **AI-Powered Query Processing**:
  - OpenShift troubleshooting expert agent using Pydantic AI
  - Deep knowledge of OpenShift architecture, Kubernetes, and common issues
  - Provides actionable troubleshooting steps and oc commands
  - Context-aware responses based on additional information provided
  - **Real-time streaming responses** for immediate feedback and better user experience
  - **MCP Integration**: Enhanced context via Model Context Protocol servers with comprehensive tool support

- **AI-Powered Investigation System**:
  - Dedicated investigation agent for comprehensive OpenShift troubleshooting
  - **Systematic investigation workflow** with planning, execution, and reporting phases
  - **Real-time streaming investigation** with live progress updates
  - **Structured markdown reports** with findings and recommendations
  - **Tool-based data collection** from OpenShift APIs via MCP servers
  - **Comprehensive analysis** including root cause analysis and remediation steps

- **Streamlit Frontend** - Modern web interface with:
  - Sidebar navigation between different operations
  - Form-based input for each endpoint
  - JSON support for optional fields
  - Real-time API interaction
  - **Streaming response support** with real-time message display for both queries and investigations
  - Toggle between streaming and regular responses
  - **MCP Tools page** for viewing and testing available tools
  - Error handling and user feedback

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables (required for /query and /investigate endpoints):**
   
   **Option A: Using .env file (Recommended)**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env file and add your OpenAI API key
   nano .env
   ```
   
   **Option B: Using environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Configure MCP Servers (Optional but Recommended):**
   
   MCP (Model Context Protocol) servers provide additional context and tools to enhance AI responses.
   
   **In your .env file:**
   ```bash
   # Enable MCP integration
   MCP_ENABLED=true
   
   # Configure MCP servers (comma-separated: name=base_endpoint_url)
   MCP_SERVERS=openshift_tools=http://localhost:8999,kb_search=http://localhost:3002
   
   # Optional: MCP connection timeout (default: 30 seconds)
   MCP_TIMEOUT=30
   ```
   
   **MCP Server Format:**
   - Each server should be specified as `name=base_endpoint_url`
   - Multiple servers can be configured by separating them with commas
   - The application automatically appends `/mcp` to the base endpoint URL
   - MCP servers should provide tools that the AI agents can invoke
   - Both query and investigation agents have access to all configured MCP tools

4. **Run the FastAPI backend:**
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`

5. **Run the Streamlit frontend (in a new terminal):**
   ```bash
   streamlit run streamlit_app.py
   ```
   The frontend will be available at `http://localhost:8501`

## API Endpoints

### GET /
- Returns API information and available endpoints
- **Response:**
  ```json
  {
    "message": "Vibe OLS API",
    "version": "1.0.0",
    "endpoints": ["/query", "/query/stream", "/investigate", "/investigate/stream", "/inbox"],
    "docs_url": "/docs",
    "redoc_url": "/redoc"
  }
  ```

### POST /query
- **AI-Powered OpenShift Troubleshooting**
- **Request Body:**
  ```json
  {
    "query": "My pods are stuck in CrashLoopBackOff state. How do I troubleshoot this?",
    "context": {
      "namespace": "my-app",
      "cluster_version": "4.12",
      "error_message": "container failed to start"
    }
  }
  ```
- **Response:**
  ```json
  {
    "result": "To troubleshoot CrashLoopBackOff pods:\n\n1. Check pod logs: `oc logs <pod-name> -n my-app`\n2. Describe the pod: `oc describe pod <pod-name> -n my-app`\n3. Check events: `oc get events -n my-app --sort-by='.lastTimestamp'`\n4. Verify resource limits and requests\n5. Check for image pull issues or configuration errors",
    "status": "success",
    "query_id": "query_a1b2c3d4"
  }
  ```

### POST /query/stream
- **AI-Powered OpenShift Troubleshooting with Streaming**
- **Request Body:** (Same as `/query`)
- **Response:** Server-Sent Events (SSE) stream
  ```
  data: {"type": "start", "query_id": "query_a1b2c3d4"}
  
  data: {"type": "token", "content": "To"}
  
  data: {"type": "token", "content": " troubleshoot"}
  
  data: {"type": "token", "content": " CrashLoopBackOff"}
  
  ...
  
  data: {"type": "done", "query_id": "query_a1b2c3d4"}
  ```

### POST /investigate
- **AI-Powered OpenShift Investigation**
- **Request Body:**
  ```json
  {
    "topic": "Pods failing to start in production namespace",
    "parameters": {
      "namespace": "production",
      "cluster_version": "4.12",
      "time_range": "last 1 hour"
    }
  }
  ```
- **Response:**
  ```json
  {
    "findings": "# Investigation Report\n\n## Investigation Summary\n**Request**: Pods failing to start in production namespace\n**Scope**: Production namespace pod failures\n**Key Findings**: Container image pull failures detected\n\n## Analysis & Recommendations\n1. Update image registry credentials\n2. Verify network connectivity to registry\n3. Check image availability",
    "status": "success",
    "investigation_id": "inv_456"
  }
  ```

### POST /investigate/stream
- **AI-Powered OpenShift Investigation with Real-time Streaming**
- **Request Body:** (Same as `/investigate`)
- **Response:** Server-Sent Events (SSE) stream with live investigation progress
  ```
  data: {"type": "start", "investigation_id": "inv_456"}
  
  data: {"type": "token", "content": "# Investigation Report\n\n"}
  
  data: {"type": "token", "content": "## Investigation Summary\n"}
  
  data: {"type": "token", "content": "**Request**: Pods failing to start...\n"}
  
  ...
  
  data: {"type": "done", "investigation_id": "inv_456"}
  ```

### POST /inbox
- **Request Body:**
  ```json
  {
    "message": "Your message",
    "metadata": {
      "priority": "high",
      "category": "support"
    }
  }
  ```
- **Response:**
  ```json
  {
    "message_id": "msg_789",
    "status": "received",
    "processed": true
  }
  ```

## Usage

1. Start the FastAPI backend server
2. Start the Streamlit frontend
3. Navigate to `http://localhost:8501` in your browser
4. Use the sidebar to select different operations:
   - **🤖 AI Query** - Quick OpenShift troubleshooting questions
   - **🔍 Investigate** - Comprehensive OpenShift investigation with detailed reporting
   - **📥 Inbox** - Message handling system
   - **🔧 MCP Tools** - View and test available MCP tools
5. For both AI Query and Investigation:
   - **Enable streaming** (recommended) for real-time response generation
   - **Disable streaming** for traditional request-response interaction
6. Fill in the forms and submit requests to interact with the API

## MCP Server Integration

The application supports Model Context Protocol (MCP) servers to enhance AI responses with tools that provide additional capabilities and knowledge sources. Both the query and investigation agents have access to all configured MCP tools.

### MCP Server Requirements

MCP servers must implement the following endpoints:

**GET /mcp/tools**
- **Accept**: `application/json`
- **Returns**: List of available tools

**Response Format:**
```json
{
  "tools": [
    {
      "name": "search_docs",
      "description": "Search OpenShift documentation for specific topics",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query"
          },
          "category": {
            "type": "string",
            "description": "Documentation category (optional)"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

**POST /mcp/execute**
- **Content-Type**: `application/json`
- **Accept**: `application/json`

**Request Body:**
```json
{
  "tool": "search_docs",
  "parameters": {
    "query": "CrashLoopBackOff troubleshooting",
    "category": "troubleshooting"
  },
  "timestamp": 1234567890.123
}
```

**Response Format:**
```json
{
  "result": "To troubleshoot CrashLoopBackOff: 1. Check logs with 'oc logs <pod>' 2. Verify resource limits...",
  "metadata": {
    "source": "openshift_docs",
    "confidence": 0.95
  }
}
```

### MCP Integration Flow

1. Application starts and loads tools from all configured MCP servers
2. AI agents (query and investigation) are initialized with access to all available MCP tools
3. User submits query via `/query`, `/investigate`, or their streaming counterparts
4. AI agent processes request and automatically chooses which tools to use
5. AI agent invokes selected MCP tools to gather additional information
6. AI agent provides enhanced response using both internal knowledge and tool results

### Example MCP Tool Usage

**Query Example:**
When a user asks: "Why are my pods crashing?"
1. AI agent recognizes this as an OpenShift troubleshooting question
2. AI agent may use tools like `openshift_tools_get_pods` to check pod status
3. AI agent incorporates tool results into comprehensive response

**Investigation Example:**
When investigating "Pod startup failures":
1. Investigation agent creates a systematic plan
2. Agent uses multiple tools: `list_pods`, `get_events`, `check_logs`
3. Agent analyzes all tool outputs and generates comprehensive report

## Development

The application follows a modular architecture with clear separation of concerns:

```
vibe-ols/
├── main.py                    # FastAPI application entry point
├── streamlit_app.py          # Streamlit frontend application
├── requirements.txt          # Python dependencies
├── env.example              # Example environment file
├── app/                     # Main application package
│   ├── __init__.py
│   ├── core/                # Core application components
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration and environment variables
│   │   ├── logging.py       # Logging setup and configuration
│   │   └── middleware.py    # Request/response middleware
│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   ├── requests.py      # Request models (QueryRequest, etc.)
│   │   └── responses.py     # Response models (QueryResponse, etc.)
│   ├── agents/              # AI agents
│   │   ├── __init__.py
│   │   ├── openshift_agent.py      # OpenShift troubleshooting AI agent
│   │   └── investigation_agent.py  # OpenShift investigation AI agent
│   ├── routes/              # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── info.py          # API information endpoint
│   │   ├── query.py         # Query endpoints (/query, /query/stream)
│   │   ├── investigate.py   # Investigation endpoints (/investigate, /investigate/stream)
│   │   └── inbox.py         # Inbox endpoint
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── helpers.py       # Common helper functions
├── .gitignore               # Git ignore file
└── app.log                  # Application log file (auto-generated)
```

### Architecture Benefits:
- **Modular Design**: Each component has a single responsibility
- **Easy Testing**: Individual modules can be tested in isolation
- **Maintainability**: Code is organized logically and easy to navigate
- **Scalability**: New features can be added without affecting existing code
- **Reusability**: Common functionality is centralized in utility modules

### AI Integration Details:
- **Query Agent**: Uses Pydantic AI for quick OpenShift troubleshooting responses
- **Investigation Agent**: Uses Pydantic AI for comprehensive, systematic OpenShift investigation
- Both agents use OpenAI's GPT-4o-mini model by default (configurable via `OPENAI_MODEL`)
- Context information is automatically incorporated into AI responses
- System prompts are optimized for OpenShift expertise
- Both agents have access to MCP tools for enhanced capabilities

### Environment Variables:
The application supports the following environment variables:
- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `OPENAI_MODEL` (optional) - OpenAI model to use (default: `openai:gpt-4o-mini`)
- `OPENAI_ORG` (optional) - Your OpenAI organization ID
- `MCP_ENABLED` (optional) - Enable MCP integration (default: `true`)
- `MCP_SERVERS` (optional) - MCP server configuration (format: `name=endpoint,name2=endpoint2`)
- `MCP_TIMEOUT` (optional) - MCP connection timeout in seconds (default: `30`)
- `DEBUG_MODE` (optional) - Enable debug logging (default: `false`)
- `VERBOSE_MODE` (optional) - Enable verbose logging (default: `false`)
- `ENVIRONMENT` (optional) - Environment name for logging (default: `development`)
- `HOST` (optional) - Server host (default: `0.0.0.0`)
- `PORT` (optional) - Server port (default: `8000`)

These can be set in a `.env` file (copy from `env.example`) or as system environment variables.

## Logging and Monitoring

The application includes comprehensive logging for debugging and monitoring:

### Logging Features:
- **Multi-level logging**: INFO, DEBUG, WARNING, ERROR levels
- **Dual output**: Console and file logging (`app.log`)
- **Request/Response logging**: Automatic logging of all HTTP requests
- **Processing time tracking**: Response headers include processing time
- **Detailed endpoint logging**: Each endpoint logs its operations
- **AI interaction logging**: OpenAI API calls and responses are logged
- **MCP tool logging**: MCP server interactions and tool calls are logged
- **Streaming progress**: Real-time streaming progress logs for both queries and investigations
- **Investigation workflow logging**: Detailed logs of investigation phases and tool usage
- **Error tracking**: Full exception tracebacks for debugging

### Log Levels:
- **INFO**: General application flow and important events
- **DEBUG**: Detailed information for debugging (enable with `DEBUG_MODE=true`)
- **WARNING**: Potential issues that don't stop execution
- **ERROR**: Critical errors with full tracebacks

### Log File:
The application writes logs to `app.log` in the project directory. This file includes:
- Timestamped entries
- Request/response details
- Processing times
- Error information
- AI interaction logs
- MCP tool interaction logs
- Investigation workflow details

### Enable Debug Mode:
For verbose logging, set `DEBUG_MODE=true` in your `.env` file:
```bash
DEBUG_MODE=true
```

This will enable detailed debugging information including:
- Full request/response bodies
- AI prompt details
- MCP tool call details
- Investigation workflow steps
- Processing step details
- Extended error information

## FastAPI Interactive Documentation

When the FastAPI server is running, you can access the comprehensive interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs` - Interactive API explorer with request/response examples
- **ReDoc**: `http://localhost:8000/redoc` - Clean, three-panel documentation
- **OpenAPI Schema**: `http://localhost:8000/openapi.json` - Raw OpenAPI specification

The SwaggerUI includes:
- Complete request/response schemas with examples
- Interactive "Try it out" functionality
- Organized endpoints by operation type (Query, Investigation, Inbox)
- Detailed parameter descriptions
- Response status codes and examples
- Built-in request validation 