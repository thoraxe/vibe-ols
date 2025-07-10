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
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Operation", ["🤖 AI Query", "🔍 Investigate", "📥 Inbox"])
    
    if page == "🤖 AI Query":
        query_page()
    elif page == "🔍 Investigate":
        investigate_page()
    elif page == "📥 Inbox":
        inbox_page()

def query_page():
    st.header("📝 OpenShift Query")
    st.write("🤖 **AI-Powered OpenShift Troubleshooting** - Submit your OpenShift-related questions and get expert guidance!")
    
    # Add some example queries
    st.info("**Example queries:**\n"
           "- My pods are stuck in CrashLoopBackOff state. How do I troubleshoot this?\n"
           "- How do I check if my OpenShift cluster is healthy?\n"
           "- What are the best practices for OpenShift resource management?\n"
           "- How do I troubleshoot networking issues in OpenShift?")
    
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
    st.write("Submit a topic for investigation")
    
    with st.form("investigate_form"):
        topic = st.text_input("Investigation Topic:")
        parameters = st.text_area("Parameters (JSON format - optional):", height=100, help="Enter parameters as JSON")
        
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
                    
                    with st.spinner("Investigating..."):
                        response = requests.post(f"{API_BASE_URL}/investigate", json=payload)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Investigation completed!")
                        st.json(result)
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