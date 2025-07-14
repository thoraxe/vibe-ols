# Vibe OLS - FastAPI with Streamlit Frontend

A Python FastAPI application with a Streamlit frontend that provides three main endpoints for query processing, investigation, and inbox management.

## Features

- **FastAPI Backend** with four POST endpoints:
  - `/query` - AI-powered OpenShift troubleshooting queries (powered by Pydantic AI)
  - `/query/stream` - Real-time streaming OpenShift troubleshooting queries
  - `/investigate` - Investigate topics with optional parameters
  - `/inbox` - Handle inbox messages with optional metadata

- **AI-Powered Query Processing**:
  - OpenShift troubleshooting expert agent using Pydantic AI
  - Deep knowledge of OpenShift architecture, Kubernetes, and common issues
  - Provides actionable troubleshooting steps and oc commands
  - Context-aware responses based on additional information provided
  - **Real-time streaming responses** for immediate feedback and better user experience
  - **MCP Integration**: Enhanced context via Model Context Protocol servers with SSE support

- **Streamlit Frontend** - Modern web interface with:
  - Sidebar navigation between different operations
  - Form-based input for each endpoint
  - JSON support for optional fields
  - Real-time API interaction
  - **Streaming response support** with real-time message display
  - Toggle between streaming and regular responses
  - Error handling and user feedback

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables (required for /query endpoint):**
   
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

3. **Configure MCP Servers (Optional):**
   
   MCP (Model Context Protocol) servers provide additional context to enhance AI responses.
   
   **In your .env file:**
   ```bash
   # Enable MCP integration
   MCP_ENABLED=true
   
   # Configure MCP servers (comma-separated: name=base_endpoint_url)
   MCP_SERVERS=openshift_docs=http://localhost:3001,kb_search=http://localhost:3002
   
   # Optional: MCP connection timeout (default: 30 seconds)
   MCP_TIMEOUT=30
   ```
   
   **MCP Server Format:**
   - Each server should be specified as `name=base_endpoint_url`
   - Multiple servers can be configured by separating them with commas
   - MCP servers should provide tools that the AI agent can invoke
   - The AI agent will automatically have access to all tools from configured MCP servers

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
- **Request Body:**
  ```json
  {
    "topic": "Investigation topic",
    "parameters": {} // Optional parameters object
  }
  ```
- **Response:**
  ```json
  {
    "findings": "Investigation results",
    "status": "success",
    "investigation_id": "inv_456"
  }
  ```

### POST /inbox
- **Request Body:**
  ```json
  {
    "message": "Your message",
    "metadata": {} // Optional metadata object
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
4. Use the sidebar to select different operations (🤖 AI Query, 🔍 Investigate, 📥 Inbox)
5. For AI Query:
   - **Enable streaming** (recommended) for real-time response generation
   - **Disable streaming** for traditional request-response interaction
6. Fill in the forms and submit requests to interact with the API

## MCP Server Integration

The application supports Model Context Protocol (MCP) servers to enhance AI responses with tools that provide additional capabilities and knowledge sources.

### MCP Server Requirements

MCP servers must implement the following endpoints:

**GET /tools**
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

**POST /execute**
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
2. AI agent is initialized with access to all available MCP tools
3. User submits query via `/query` or `/investigate` endpoints
4. AI agent processes query and automatically chooses which tools to use
5. AI agent invokes selected MCP tools to gather additional information
6. AI agent provides enhanced response using both internal knowledge and tool results

### Example MCP Tool Usage

When a user asks: "Why are my pods crashing?"

1. AI agent recognizes this as an OpenShift troubleshooting question
2. AI agent may choose to use tools like:
   - `openshift_docs_search_docs` to find relevant documentation
   - `kb_search_find_solutions` to search knowledge base for similar issues
3. AI agent receives tool results and incorporates them into the response
4. User gets a comprehensive answer with relevant documentation and solutions

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
│   │   ├── middleware.py    # Request/response middleware

│   ├── models/              # Pydantic data models
│   │   ├── __init__.py
│   │   ├── requests.py      # Request models (QueryRequest, etc.)
│   │   └── responses.py     # Response models (QueryResponse, etc.)
│   ├── agents/              # AI agents
│   │   ├── __init__.py
│   │   └── openshift_agent.py # OpenShift troubleshooting AI agent
│   ├── routes/              # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── query.py         # Query endpoints (/query, /query/stream)
│   │   ├── investigate.py   # Investigation endpoint
│   │   ├── inbox.py         # Inbox endpoint
│   │   └── info.py          # API information endpoint
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
- The `/query` endpoint uses a Pydantic AI agent specifically trained for OpenShift troubleshooting
- The agent uses OpenAI's GPT-4o-mini model by default (configurable via `OPENAI_MODEL` env var)
- Context information is automatically incorporated into AI responses
- The system prompt is optimized for OpenShift expertise
- Configuration is managed through environment variables and `.env` file support

### Customization:
- The `/investigate` and `/inbox` endpoints currently return placeholder responses
- Implement your actual business logic in the respective endpoint functions in `main.py`
- You can modify the AI model or system prompt in the `openshift_agent` configuration
- Add additional agents for other endpoints if needed

### Environment Variables:
The application supports the following environment variables:
- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `OPENAI_MODEL` (optional) - OpenAI model to use (default: `openai:gpt-4o-mini`)
- `OPENAI_ORG` (optional) - Your OpenAI organization ID
- `DEBUG_MODE` (optional) - Enable debug logging (default: `false`)
- `ENVIRONMENT` (optional) - Environment name for logging (default: `development`)

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
- **Streaming progress**: Real-time streaming progress logs
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

### Enable Debug Mode:
For verbose logging, set `DEBUG_MODE=true` in your `.env` file:
```bash
DEBUG_MODE=true
```

This will enable detailed debugging information including:
- Full request/response bodies
- AI prompt details
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