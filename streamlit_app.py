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
    st.header("📥 Inbox - Investigation Reports")
    
    # Initialize session state for inbox
    if "inbox_view" not in st.session_state:
        st.session_state.inbox_view = "list"  # "list" or "detail"
    if "selected_reports" not in st.session_state:
        st.session_state.selected_reports = set()
    if "current_report_id" not in st.session_state:
        st.session_state.current_report_id = None
    if "inbox_page_offset" not in st.session_state:
        st.session_state.inbox_page_offset = 0
    if "inbox_search_query" not in st.session_state:
        st.session_state.inbox_search_query = ""
    if "refresh_inbox" not in st.session_state:
        st.session_state.refresh_inbox = 0
    
    # Navigation between list and detail views
    if st.session_state.inbox_view == "detail" and st.session_state.current_report_id:
        if st.button("← Back to Reports List"):
            st.session_state.inbox_view = "list"
            st.session_state.current_report_id = None
            st.rerun()
        show_report_detail()
    else:
        show_reports_list()

def show_reports_list():
    """Display the list of investigation reports with search, pagination, and bulk actions."""
    
    # Search and pagination controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search reports:",
            value=st.session_state.inbox_search_query,
            placeholder="Search by question content...",
            key="search_input"
        )
        if search_query != st.session_state.inbox_search_query:
            st.session_state.inbox_search_query = search_query
            st.session_state.inbox_page_offset = 0  # Reset to first page
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh"):
            st.session_state.refresh_inbox += 1
            st.session_state.selected_reports.clear()
            st.rerun()
    
    with col3:
        page_size = st.selectbox("Reports per page:", [10, 25, 50], index=1, key="page_size")
    
    # Load reports from API
    try:
        params = {
            "limit": page_size,
            "offset": st.session_state.inbox_page_offset,
        }
        if st.session_state.inbox_search_query:
            params["search"] = st.session_state.inbox_search_query
        
        with st.spinner("Loading reports..."):
            response = requests.get(f"{API_BASE_URL}/inbox/reports", params=params)
        
        if response.status_code == 200:
            data = response.json()
            reports = data.get("reports", [])
            total = data.get("total", 0)
            
            # Display summary info
            st.info(f"📊 Showing {len(reports)} of {total} reports")
            
            if reports:
                # Bulk actions
                col1, col2, col3 = st.columns([2, 2, 2])
                
                with col1:
                    if st.button("☑️ Select All", disabled=not reports):
                        for report in reports:
                            st.session_state.selected_reports.add(report["id"])
                        st.rerun()
                
                with col2:
                    if st.button("☐ Clear Selection", disabled=len(st.session_state.selected_reports) == 0):
                        st.session_state.selected_reports.clear()
                        st.rerun()
                
                with col3:
                    selected_count = len(st.session_state.selected_reports)
                    if st.button(f"🗑️ Delete Selected ({selected_count})", 
                               disabled=selected_count == 0,
                               type="primary" if selected_count > 0 else "secondary"):
                        if selected_count > 0:
                            delete_selected_reports()
                
                st.markdown("---")
                
                # Reports grid
                for report in reports:
                    show_report_summary(report)
                
                st.markdown("---")
                
                # Pagination
                show_pagination(total, page_size)
                
            else:
                if st.session_state.inbox_search_query:
                    st.info("🔍 No reports found matching your search criteria.")
                else:
                    st.info("📭 No investigation reports found. Create some investigations to see them here!")
        
        else:
            st.error(f"Failed to load reports: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        st.info("Make sure the FastAPI server is running on http://localhost:8000")

def show_report_summary(report):
    """Display a single report summary in the list."""
    
    # Create a container for the report
    with st.container():
        col1, col2, col3 = st.columns([0.5, 6, 1.5])
        
        # Checkbox for selection
        with col1:
            is_selected = report["id"] in st.session_state.selected_reports
            if st.checkbox(
                f"Select report {report['id'][:8]}",
                value=is_selected, 
                key=f"select_{report['id']}",
                label_visibility="hidden"
            ):
                st.session_state.selected_reports.add(report["id"])
            else:
                st.session_state.selected_reports.discard(report["id"])
        
        # Report content
        with col2:
            # Question as clickable title
            if st.button(
                f"📋 {report['question'][:80]}{'...' if len(report['question']) > 80 else ''}",
                key=f"view_{report['id']}",
                use_container_width=True
            ):
                st.session_state.current_report_id = report["id"]
                st.session_state.inbox_view = "detail"
                st.rerun()
            
            # Parameters and metadata
            if report.get("parameters"):
                params_text = ", ".join([f"{k}: {v}" for k, v in report["parameters"].items()])
                st.caption(f"🔧 Parameters: {params_text[:100]}{'...' if len(params_text) > 100 else ''}")
            
            # Created date and report length
            created_date = datetime.fromisoformat(report["created_at"].replace('Z', '+00:00'))
            st.caption(f"📅 Created: {created_date.strftime('%Y-%m-%d %H:%M')} | 📄 Length: {report['report_length']:,} chars")
        
        # Quick actions
        with col3:
            if st.button("👁️ View", key=f"quick_view_{report['id']}", use_container_width=True):
                st.session_state.current_report_id = report["id"]
                st.session_state.inbox_view = "detail"
                st.rerun()
    
    st.divider()

def show_pagination(total, page_size):
    """Display pagination controls."""
    
    total_pages = max(1, (total + page_size - 1) // page_size)
    current_page = (st.session_state.inbox_page_offset // page_size) + 1
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏪ First", disabled=current_page == 1):
            st.session_state.inbox_page_offset = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Prev", disabled=current_page == 1):
            st.session_state.inbox_page_offset = max(0, st.session_state.inbox_page_offset - page_size)
            st.rerun()
    
    with col3:
        st.write(f"📄 Page {current_page} of {total_pages}")
    
    with col4:
        if st.button("▶️ Next", disabled=current_page == total_pages):
            st.session_state.inbox_page_offset = min((total_pages - 1) * page_size, st.session_state.inbox_page_offset + page_size)
            st.rerun()
    
    with col5:
        if st.button("⏩ Last", disabled=current_page == total_pages):
            st.session_state.inbox_page_offset = (total_pages - 1) * page_size
            st.rerun()

def show_report_detail():
    """Display detailed view of a specific investigation report."""
    
    try:
        with st.spinner("Loading report details..."):
            response = requests.get(f"{API_BASE_URL}/inbox/reports/{st.session_state.current_report_id}")
        
        if response.status_code == 200:
            report = response.json()
            
            # Report header
            st.subheader("📋 Investigation Report Details")
            
            # Question - prominently displayed
            st.markdown("### ❓ Investigation Question")
            st.markdown(f"**{report['question']}**")
            
            # Parameters - prominently displayed if present
            if report.get("parameters"):
                st.markdown("### 🔧 Parameters")
                st.json(report["parameters"])
            
            # Metadata and actions
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.info(f"**Report ID:** {report['id']}")
            
            with col2:
                created_date = datetime.fromisoformat(report["created_at"].replace('Z', '+00:00'))
                st.info(f"**Created:** {created_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col3:
                # Delete button for single report
                if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                    if delete_single_report(report["id"]):
                        st.session_state.inbox_view = "list"
                        st.session_state.current_report_id = None
                        st.rerun()
            
            st.markdown("---")
            
            # Report content
            st.markdown("### 📄 Investigation Report")
            
            # Display report text with syntax highlighting if it looks like markdown
            report_text = report.get("report_text", "No report content available.")
            
            if report_text.strip().startswith("#") or "```" in report_text:
                # Looks like markdown
                st.markdown(report_text)
            else:
                # Plain text
                st.text_area(
                    "Report Content:",
                    value=report_text,
                    height=400,
                    disabled=True
                )
            
        elif response.status_code == 404:
            st.error("❌ Report not found. It may have been deleted.")
            st.session_state.inbox_view = "list"
            st.session_state.current_report_id = None
        else:
            st.error(f"Failed to load report: {response.status_code} - {response.text}")
    
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        st.info("Make sure the FastAPI server is running on http://localhost:8000")

def delete_selected_reports():
    """Delete all selected reports."""
    
    if not st.session_state.selected_reports:
        st.warning("No reports selected for deletion.")
        return
    
    # Confirmation dialog
    selected_count = len(st.session_state.selected_reports)
    
    # Use a form for confirmation to avoid accidental deletions
    with st.form("confirm_bulk_delete"):
        st.warning(f"⚠️ Are you sure you want to delete {selected_count} selected report(s)? This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm_delete = st.form_submit_button("🗑️ Confirm Delete", type="primary")
        with col2:
            cancel_delete = st.form_submit_button("❌ Cancel")
        
        if confirm_delete:
            success_count = 0
            error_count = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            selected_list = list(st.session_state.selected_reports)
            
            for i, report_id in enumerate(selected_list):
                status_text.text(f"Deleting report {i+1} of {len(selected_list)}...")
                progress_bar.progress((i + 1) / len(selected_list))
                
                try:
                    response = requests.delete(f"{API_BASE_URL}/inbox/reports/{report_id}")
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                        st.error(f"Failed to delete report {report_id}: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    error_count += 1
                    st.error(f"Connection error deleting report {report_id}: {e}")
            
            # Clear selection and show results
            st.session_state.selected_reports.clear()
            
            if success_count > 0:
                st.success(f"✅ Successfully deleted {success_count} report(s)")
            if error_count > 0:
                st.error(f"❌ Failed to delete {error_count} report(s)")
            
            # Refresh the list
            st.session_state.refresh_inbox += 1
            st.rerun()
        
        elif cancel_delete:
            st.info("Deletion cancelled.")

def delete_single_report(report_id: str) -> bool:
    """Delete a single report by ID. Returns True if successful."""
    
    try:
        response = requests.delete(f"{API_BASE_URL}/inbox/reports/{report_id}")
        if response.status_code == 200:
            st.success("✅ Report deleted successfully!")
            st.session_state.refresh_inbox += 1
            return True
        else:
            st.error(f"Failed to delete report: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    main() 