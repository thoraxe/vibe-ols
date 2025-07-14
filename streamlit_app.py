import streamlit as st
import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"

def main():
    st.set_page_config(
        page_title="Vibe OLS",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Vibe OLS - AI-Powered OpenShift Troubleshooting")
    st.markdown("---")
    
    # Add info about AI capabilities
    st.sidebar.markdown("### 🤖 AI-Powered Features")
    st.sidebar.info("The Query endpoint uses Pydantic AI with OpenShift expertise to provide intelligent troubleshooting guidance!")
    st.sidebar.markdown("**Configuration:** The backend uses dotenv for environment management. Create a `.env` file with your OpenAI API key.")
    st.sidebar.markdown("**Streaming:** Enable real-time streaming responses for a better user experience!")
    st.sidebar.markdown("**MCP Tools:** The AI agent can access external tools via Model Context Protocol (MCP) servers for enhanced capabilities!")
    
    # Add MCP server status
    st.sidebar.markdown("### 🔧 MCP Server Status")
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code == 200:
            st.sidebar.success("✅ API Server Connected")
        else:
            st.sidebar.error("❌ API Server Error")
    except requests.exceptions.RequestException:
        st.sidebar.error("❌ API Server Offline")
        st.sidebar.info("Make sure the FastAPI server is running on http://localhost:8000")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Operation", ["🤖 AI Query", "🔍 Investigate", "📥 Inbox", "🔧 MCP Tools"])
    
    if page == "🤖 AI Query":
        query_page()
    elif page == "🔍 Investigate":
        investigate_page()
    elif page == "📥 Inbox":
        inbox_page()
    elif page == "🔧 MCP Tools":
        mcp_tools_page()

def query_page():
    st.header("📝 OpenShift Query")
    st.write("🤖 **AI-Powered OpenShift Troubleshooting** - Submit your OpenShift-related questions and get expert guidance!")
    
    # Add some example queries
    st.info("**Example queries:**\n"
           "- My pods are stuck in CrashLoopBackOff state. How do I troubleshoot this?\n"
           "- How do I check if my OpenShift cluster is healthy?\n"
           "- What are the best practices for OpenShift resource management?\n"
           "- How do I troubleshoot networking issues in OpenShift?\n"
           "- List all pods in the default namespace and check their status\n"
           "- Show me the recent events in my cluster\n"
           "- Get the logs from a failing pod and analyze them")
    
    with st.form("query_form"):
        query_text = st.text_area("Enter your OpenShift query:", height=100, 
                                 placeholder="e.g., My application pods are failing to start. How can I debug this?")
        context = st.text_area("Context (JSON format - optional):", height=100, 
                              help="Enter context as JSON (namespace, cluster version, error messages, etc.)",
                              placeholder='{"namespace": "my-app", "cluster_version": "4.12", "error_message": "container failed to start"}')
        
        # Add streaming toggle
        use_streaming = st.checkbox("Enable streaming response", value=True, 
                                   help="Get real-time streaming response instead of waiting for complete response")
        
        submitted = st.form_submit_button("Submit Query")
        
        if submitted:
            if query_text.strip():
                try:
                    # Parse context if provided
                    context_dict = {}
                    if context.strip():
                        try:
                            context_dict = json.loads(context)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format in context field")
                            return
                    
                    # Make API call
                    payload = {
                        "query": query_text,
                        "context": context_dict
                    }
                    
                    if use_streaming:
                        # Handle streaming response
                        st.info("🔄 **Streaming Response:**")
                        response_container = st.empty()
                        accumulated_response = ""
                        
                        try:
                            with st.spinner("Connecting to AI..."):
                                response = requests.post(f"{API_BASE_URL}/query/stream", json=payload, stream=True)
                            
                            if response.status_code == 200:
                                st.success("Connected! Streaming response...")
                                
                                for line in response.iter_lines():
                                    if line:
                                        line_str = line.decode('utf-8')
                                        if line_str.startswith('data: '):
                                            try:
                                                data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                                                
                                                if data.get('type') == 'start':
                                                    st.write(f"**Query ID:** {data.get('query_id')}")
                                                elif data.get('type') == 'token':
                                                    accumulated_response += data.get('content', '')
                                                    response_container.markdown(accumulated_response)
                                                elif data.get('type') == 'done':
                                                    st.success("✅ **Response completed!**")
                                                    break
                                                elif data.get('type') == 'error':
                                                    st.error(f"❌ **Error:** {data.get('message')}")
                                                    break
                                                    
                                            except json.JSONDecodeError:
                                                continue
                            else:
                                st.error(f"Error: {response.status_code} - {response.text}")
                        except Exception as e:
                            st.error(f"Streaming error: {str(e)}")
                    else:
                        # Handle regular response
                        with st.spinner("Processing query..."):
                            response = requests.post(f"{API_BASE_URL}/query", json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("Query processed successfully!")
                            st.json(result)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8000")
            else:
                st.error("Please enter a query")

def investigate_page():
    st.header("🔍 Investigate")
    st.write("🤖 **AI-Powered OpenShift Investigation** - Submit a topic for comprehensive investigation and get detailed analysis!")
    
    # Add some example investigation topics
    st.info("**Example investigation topics:**\n"
           "- Pods failing to start in production namespace\n"
           "- High memory usage on worker nodes\n"
           "- Network connectivity issues between services\n"
           "- Persistent volume mount failures\n"
           "- Application performance degradation\n"
           "- Certificate expiration warnings\n"
           "- Resource quota limit exceeded errors")
    
    with st.form("investigate_form"):
        topic = st.text_input("Investigation Topic:", placeholder="e.g., Pods stuck in CrashLoopBackOff in my-app namespace")
        parameters = st.text_area("Parameters (JSON format - optional):", height=100, 
                                 help="Enter parameters as JSON (namespace, cluster info, etc.)",
                                 placeholder='{"namespace": "my-app", "cluster_version": "4.12", "time_range": "last 1 hour"}')
        
        # Add streaming toggle
        use_streaming = st.checkbox("Enable streaming response", value=True, 
                                   help="Get real-time streaming investigation updates instead of waiting for complete report")
        
        submitted = st.form_submit_button("Start Investigation")
        
        if submitted:
            if topic.strip():
                try:
                    # Parse parameters if provided
                    params_dict = {}
                    if parameters.strip():
                        try:
                            params_dict = json.loads(parameters)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format in parameters field")
                            return
                    
                    # Make API call
                    payload = {
                        "topic": topic,
                        "parameters": params_dict
                    }
                    
                    if use_streaming:
                        # Handle streaming response
                        st.info("🔄 **Streaming Investigation:**")
                        response_container = st.empty()
                        accumulated_response = ""
                        
                        try:
                            with st.spinner("Connecting to Investigation Agent..."):
                                response = requests.post(f"{API_BASE_URL}/investigate/stream", json=payload, stream=True)
                            
                            if response.status_code == 200:
                                st.success("Connected! Streaming investigation results...")
                                
                                for line in response.iter_lines():
                                    if line:
                                        line_str = line.decode('utf-8')
                                        if line_str.startswith('data: '):
                                            try:
                                                data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                                                
                                                if data.get('type') == 'start':
                                                    st.write(f"**Investigation ID:** {data.get('investigation_id')}")
                                                elif data.get('type') == 'token':
                                                    accumulated_response += data.get('content', '')
                                                    response_container.markdown(accumulated_response)
                                                elif data.get('type') == 'done':
                                                    st.success("✅ **Investigation completed!**")
                                                    break
                                                elif data.get('type') == 'error':
                                                    st.error(f"❌ **Error:** {data.get('message')}")
                                                    break
                                                    
                                            except json.JSONDecodeError:
                                                continue
                            else:
                                st.error(f"Error: {response.status_code} - {response.text}")
                        except Exception as e:
                            st.error(f"Streaming error: {str(e)}")
                    else:
                        # Handle regular response
                        with st.spinner("Investigating..."):
                            response = requests.post(f"{API_BASE_URL}/investigate", json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("Investigation completed!")
                            
                            # Display investigation metadata
                            col1, col2 = st.columns(2)
                            with col1:
                                st.info(f"**Investigation ID:** {result.get('investigation_id', 'N/A')}")
                            with col2:
                                st.info(f"**Status:** {result.get('status', 'N/A')}")
                            
                            # Display findings as markdown instead of JSON
                            st.subheader("📋 Investigation Findings")
                            findings = result.get('findings', 'No findings available')
                            st.markdown(findings)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8000")
            else:
                st.error("Please enter a topic to investigate")

def inbox_page():
    st.header("📥 Inbox")
    st.write("Submit a message to the inbox")
    
    with st.form("inbox_form"):
        message = st.text_area("Message:", height=100)
        metadata = st.text_area("Metadata (JSON format - optional):", height=100, help="Enter metadata as JSON")
        
        submitted = st.form_submit_button("Send to Inbox")
        
        if submitted:
            if message.strip():
                try:
                    # Parse metadata if provided
                    metadata_dict = {}
                    if metadata.strip():
                        try:
                            metadata_dict = json.loads(metadata)
                        except json.JSONDecodeError:
                            st.error("Invalid JSON format in metadata field")
                            return
                    
                    # Make API call
                    payload = {
                        "message": message,
                        "metadata": metadata_dict
                    }
                    
                    with st.spinner("Sending to inbox..."):
                        response = requests.post(f"{API_BASE_URL}/inbox", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Message sent to inbox!")
                        st.json(result)
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")
                    st.info("Make sure the FastAPI server is running on http://localhost:8000")
            else:
                st.error("Please enter a message")

def mcp_tools_page():
    st.header("🔧 MCP Tools")
    st.write("View and test available MCP (Model Context Protocol) tools")
    
    # Add explanation
    st.info("""
    **MCP Tools** are external capabilities that the AI agent can use to enhance its responses.
    These tools are loaded from configured MCP servers and can provide:
    - OpenShift/Kubernetes cluster information
    - Documentation searches
    - Log analysis
    - And more!
    """)
    
    # Configuration section
    st.subheader("📋 MCP Configuration")
    st.write("To enable MCP tools, configure your `.env` file with:")
    st.code("""
# Enable MCP integration
MCP_ENABLED=true

# Configure MCP servers (comma-separated: name=endpoint)
MCP_SERVERS=openshift_tools=http://localhost:8999/mcp

# Optional: MCP connection timeout (default: 30 seconds)
MCP_TIMEOUT=30
""")
    
    # Tool status section
    st.subheader("🔍 Available MCP Tools")
    
    if st.button("Refresh Tool List"):
        with st.spinner("Loading MCP tools..."):
            try:
                # Try to get server info which might include MCP status
                response = requests.get(f"{API_BASE_URL}/")
                if response.status_code == 200:
                    st.success("✅ Connected to API server")
                    st.info("MCP tools are loaded automatically when the API server starts. Check the server logs for MCP tool loading status.")
                else:
                    st.error("❌ Could not connect to API server")
            except requests.exceptions.RequestException:
                st.error("❌ API server is not running")
    
    # Test query with MCP tools
    st.subheader("🧪 Test MCP Tools")
    st.write("Try a query that can benefit from MCP tools:")
    
    example_queries = [
        "List all pods in the default namespace",
        "Show me the configuration of my OpenShift cluster",
        "Check the events in my cluster",
        "Get the logs from a failing pod"
    ]
    
    selected_query = st.selectbox("Example queries:", [""] + example_queries)
    
    if selected_query:
        st.write(f"**Selected query:** {selected_query}")
        if st.button("Test Query"):
            payload = {"query": selected_query, "context": {}}
            
            with st.spinner("Testing query with MCP tools..."):
                try:
                    response = requests.post(f"{API_BASE_URL}/query", json=payload, timeout=30)
                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Query executed successfully!")
                        st.json(result)
                    else:
                        st.error(f"❌ Query failed: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {e}")
    
    # Troubleshooting section
    st.subheader("🔧 Troubleshooting")
    st.write("Common MCP issues and solutions:")
    
    with st.expander("MCP Server Not Found"):
        st.write("""
        **Problem:** MCP server connection errors
        
        **Solutions:**
        1. Check if your MCP server is running
        2. Verify the MCP_SERVERS configuration in your .env file
        3. Ensure the server endpoint is accessible
        4. Check server logs for error messages
        """)
    
    with st.expander("No Tools Available"):
        st.write("""
        **Problem:** MCP tools are not being loaded
        
        **Solutions:**
        1. Verify MCP_ENABLED=true in your .env file
        2. Check MCP_SERVERS configuration format
        3. Restart the API server after configuration changes
        4. Check server logs for MCP loading messages
        """)
    
    with st.expander("Tool Execution Errors"):
        st.write("""
        **Problem:** MCP tools fail when called
        
        **Solutions:**
        1. Check if required credentials are configured
        2. Verify tool parameters are correct
        3. Check MCP server logs for detailed error messages
        4. Ensure the MCP server has necessary permissions
        """)

if __name__ == "__main__":
    main() 