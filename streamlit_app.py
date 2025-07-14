import streamlit as st
import requests
import json
from typing import Dict, Any, List
import uuid
from datetime import datetime
import re

# Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state for navigation and chat history
if "current_page" not in st.session_state:
    st.session_state.current_page = "query"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def main():
    st.set_page_config(
        page_title="Vibe OLS",
        page_icon="🔍",
        layout="wide"
    )
    
    # Simplified CSS - removing chat bubble styling since we're using native elements
    st.markdown("""
    <style>
    .nav-link {
        display: block;
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        text-decoration: none;
        color: #262730;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .nav-link:hover {
        background-color: #f0f2f6;
        text-decoration: none;
        color: #262730;
    }
    .nav-link.active {
        background-color: #ff6b6b;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔍 Vibe OLS - AI-Powered OpenShift Troubleshooting")
    st.markdown("---")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Create navigation links
        pages = [
            ("query", "🤖 AI Query"),
            ("investigate", "🔍 Investigate"),
            ("inbox", "📥 Inbox")
        ]
        
        for page_key, page_name in pages:
            if page_key == st.session_state.current_page:
                st.markdown(f'<div class="nav-link active">{page_name}</div>', unsafe_allow_html=True)
            else:
                if st.button(page_name, key=f"nav_{page_key}"):
                    st.session_state.current_page = page_key
                    st.rerun()
        
        st.markdown("---")
        
        # Add info about AI capabilities
        st.markdown("### 🤖 AI-Powered Features")
        st.info("The Query endpoint uses Pydantic AI with OpenShift expertise to provide intelligent troubleshooting guidance!")
        st.markdown("**Configuration:** The backend uses dotenv for environment management. Create a `.env` file with your OpenAI API key.")
        st.markdown("**Streaming:** Enable real-time streaming responses for a better user experience!")
        
        # Add server status
        st.markdown("### 🔧 Server Status")
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=2)
            if response.status_code == 200:
                st.success("✅ API Server Connected")
            else:
                st.error("❌ API Server Error")
        except requests.exceptions.RequestException:
            st.error("❌ API Server Offline")
            st.info("Make sure the FastAPI server is running on http://localhost:8000")
    
    # Route to the appropriate page
    if st.session_state.current_page == "query":
        query_page()
    elif st.session_state.current_page == "investigate":
        investigate_page()
    elif st.session_state.current_page == "inbox":
        inbox_page()

def query_page():
    st.header("💬 AI Chat Interface")
    st.write("🤖 **AI-Powered OpenShift Troubleshooting** - Chat with the AI assistant for expert guidance!")
    
    # Display chat history using native Streamlit chat elements
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Show example queries for new users
    if not st.session_state.chat_history:
        st.info("**Example queries:**\n"
               "- My pods are stuck in CrashLoopBackOff state. How do I troubleshoot this?\n"
               "- How do I check if my OpenShift cluster is healthy?\n"
               "- What are the best practices for OpenShift resource management?\n"
               "- How do I troubleshoot networking issues in OpenShift?\n"
               "- List all pods in the default namespace and check their status\n"
               "- Show me the recent events in my cluster")
    
    # Add advanced options in sidebar for cleaner interface
    with st.sidebar:
        st.markdown("### ⚙️ Advanced Options")
        context = st.text_area("Context (JSON):", height=80, 
                              help="Optional context as JSON",
                              placeholder='{"namespace": "my-app"}')
        use_streaming = st.checkbox("Stream response", value=True, 
                                  help="Get real-time streaming response")
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Chat input at bottom (native Streamlit chat input)
    if query_text := st.chat_input("Ask a question about OpenShift troubleshooting..."):
        # Add user message to history and display it
        user_message = {
            "role": "user",
            "content": query_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.chat_history.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(query_text)
        
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
            
            # Display assistant response
            with st.chat_message("assistant"):
                if use_streaming:
                    # Handle streaming response
                    try:
                        response = requests.post(f"{API_BASE_URL}/query/stream", json=payload, stream=True)
                        
                        if response.status_code == 200:
                            # Use st.write_stream for proper streaming with typewriter effect
                            def stream_generator():
                                for line in response.iter_lines():
                                    if line:
                                        line_str = line.decode('utf-8')
                                        if line_str.startswith('data: '):
                                            try:
                                                data = json.loads(line_str[6:])
                                                if data.get('type') == 'token':
                                                    yield data.get('content', '')
                                                elif data.get('type') == 'done':
                                                    break
                                                elif data.get('type') == 'error':
                                                    st.error(f"❌ **Error:** {data.get('message')}")
                                                    return
                                            except json.JSONDecodeError:
                                                continue
                            
                            # Stream the response with typewriter effect
                            response_text = st.write_stream(stream_generator())
                            
                            # Add assistant response to history
                            assistant_message = {
                                "role": "assistant",
                                "content": response_text,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.session_state.chat_history.append(assistant_message)
                            
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
                else:
                    # Handle regular response
                    try:
                        response = requests.post(f"{API_BASE_URL}/query", json=payload)
                        
                        if response.status_code == 200:
                            result = response.json()
                            response_text = result.get('response', 'No response available')
                            
                            st.markdown(response_text)
                            
                            # Add assistant response to history
                            assistant_message = {
                                "role": "assistant",
                                "content": response_text,
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            st.session_state.chat_history.append(assistant_message)
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")
                        
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {e}")
            st.info("Make sure the FastAPI server is running on http://localhost:8000")

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

if __name__ == "__main__":
    main() 