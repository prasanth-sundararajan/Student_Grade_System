import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(
    page_title="Hybrid RAG Knowledge Base Assistant",
    page_icon="📚",
    layout="wide"
)

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Document Upload & Indexing
with st.sidebar:
    st.header("Document Upload")
    uploaded_file = st.file_uploader("Upload PDF / Knowledge Base", type=["pdf", "txt"])
    
    if st.button("Upload & Index", type="primary"):
        if uploaded_file is not None:
            with st.spinner("Processing & Indexing..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_URL}/upload", files=files)
                    if response.status_code == 200:
                        st.success(f"Indexed: {uploaded_file.name}")
                    else:
                        st.error(f"Failed: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        else:
            st.warning("Select a file first.")

    st.markdown("---")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main Interface Header
st.title("📚 Hybrid RAG Knowledge Base Assistant")
st.markdown("---")

# 1. Render existing conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. BULLETPROOF INPUT FORM
st.markdown("### Ask your Knowledge Base")
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Query", 
            placeholder="Ask a question about your uploaded document...", 
            label_visibility="collapsed"
        )
    with col2:
        submit_button = st.form_submit_button("Send 🚀", use_container_width=True)

# Handle Form Submission
if submit_button and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(f"{BACKEND_URL}/query", json={"question": user_input})
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "No response generated.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"❌ **Backend Error ({res.status_code}):** `{res.text}`"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"❌ **Connection Error:** Could not connect to backend at `{BACKEND_URL}`. Details: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()