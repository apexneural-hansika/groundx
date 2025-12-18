import os
import tempfile
import requests
from typing import Any, Dict

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from groundx_utils import (
    create_client, 
    ensure_bucket, 
    check_file_exists, 
    get_xray_for_existing_document,
    process_document
)

# Application Configuration
st.set_page_config(page_title="Ground X - X-Ray", layout="wide")

# Custom CSS for enhanced chat interface layout
st.markdown("""
<style>
    /* Fixed chat input at bottom */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 15% !important;
        width: 60% !important;
        max-width: 800px !important;
        background: var(--background-color) !important;
        z-index: 9999 !important;
        padding: 1rem !important;
        border-top: 1px solid var(--border-color) !important;
        margin: 0 !important;
    }
    
    /* Make chat area scrollable */
    .main .block-container {
        padding-bottom: 120px !important;
    }
    
    /* Limit chat message width to match main content */
    .stChatMessage {
        max-width: 60% !important;
        width: 60% !important;
    }
    
    /* Ensure chat message content doesn't overflow */
    .stChatMessageContent {
        max-width: 100% !important;
        word-wrap: break-word !important;
    }
</style>
""", unsafe_allow_html=True)

def reset_analysis():
    """Reset all analysis-related session state variables"""
    keys_to_delete = ["xray_data", "uploaded_file_path", "uploaded_file_name", "uploaded_file_type", 
                      "processing_complete", "used_existing_file", "auto_loaded_file", "chat_history"]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]

# Chat Interface Functions
def prepare_chat_context(xray_data, prompt):
    """Prepare context from X-Ray data for the LLM"""
    if not xray_data:
        return None
    
    context_parts = []
    
    # Add summary first for quick overview
    if xray_data.get('fileSummary'):
        context_parts.append(f"Summary: {xray_data['fileSummary']}")
    
    # Add limited document content (first 2 pages, first 3 chunks each)
    if 'documentPages' in xray_data and xray_data['documentPages']:
        extracted_texts = []
        for page in xray_data['documentPages'][:2]:  # Only first 2 pages
            if 'chunks' in page:
                for chunk in page['chunks'][:3]:  # Only first 3 chunks per page
                    if 'text' in chunk and chunk['text']:
                        text = chunk['text']
                        if len(text) > 500:  # Shorter limit
                            text = text[:500] + "..."
                        extracted_texts.append(text)
        
        if extracted_texts:
            context_parts.append(f"Document Content: {' '.join(extracted_texts)}")
    
    # Add essential metadata
    if xray_data.get('fileType'):
        context_parts.append(f"File Type: {xray_data['fileType']}")
    if xray_data.get('language'):
        context_parts.append(f"Language: {xray_data['language']}")
    
    return "\n\n".join(context_parts) if context_parts else None

def generate_chat_response(prompt, context=None):
    """Generate AI response using OpenRouter API with structured prompt engineering"""
    # Get OpenRouter API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "❌ Error: OPENROUTER_API_KEY not found in environment variables. Please add it to your .env file."
    
    # If no context provided, create a basic prompt
    if not context:
        context = "No document context available. Answer the question based on general knowledge."
    
    # Construct comprehensive prompt for intelligent query handling
    full_prompt = f"""You are an AI assistant helping analyze a document. You have access to the following document information:

{context}

User Question: {prompt}

Instructions:
- Answer the question directly and concisely
- Use Document Content for specific details
- Use Summary for general overview
- Don't add unnecessary disclaimers or explanations
- If you don't have the information, simply say "I don't have enough information to answer that question"
- Keep responses focused and to the point

Response:"""

    # Initialize OpenRouter API request
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/your-repo",  # Optional: for analytics
                "X-Title": "Ground X Document Processing"  # Optional: for analytics
            },
            json={
                "model": "openai/gpt-4o-mini",  # Using GPT-4o-mini via OpenRouter
                "messages": [
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return "Sorry, I couldn't generate a response."
        else:
            return f"I'm having trouble accessing the AI model right now. Status: {response.status_code}"
            
    except Exception as e:
        return f"I'm having trouble accessing the AI model right now. Error: {str(e)}"

# Initialize Streamlit session state
for key in ["xray_data", "uploaded_file_path", "uploaded_file_name", "uploaded_file_type", "processing_complete", "used_existing_file", "auto_loaded_file"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "xray_data" else False

# Application Header
st.markdown("""
# World-class Document Processing Pipeline
""")

# Load and display GroundX branding
import base64
try:
    with open("assets/groundx.png", "rb") as img_file:
        logo_base64 = base64.b64encode(img_file.read()).decode()

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px;">
        <strong>powered by</strong>
        <img src="data:image/png;base64,{logo_base64}" width="200" style="display: inline-block;">
    </div>
    <br>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px;">
        <strong>powered by</strong>
        <strong>Ground X</strong>
    </div>
    <br>
    """, unsafe_allow_html=True)

# Document Upload Interface
with st.sidebar:
    st.header("📄 Upload Document")
    
    if st.session_state.uploaded_file_name:
        status_text = f"✅ **File loaded**: {st.session_state.uploaded_file_name}"
        if st.session_state.used_existing_file:
            status_text += " (Auto-loaded from bucket)" if st.session_state.auto_loaded_file else " (Used existing file in bucket)"
        st.success(status_text)
        if st.button("🔄 Re-process File"):
            st.session_state.processing_complete = False
            st.session_state.xray_data = None
            st.session_state.used_existing_file = False
            st.session_state.auto_loaded_file = False
            st.rerun()
    
    uploaded = st.file_uploader(
        "Choose a document", 
        type=["pdf", "png", "jpg", "jpeg", "docx"],
        help="Upload a document to analyze with Ground X X-Ray"
    )

    if uploaded is not None:
        st.info(f"**File**: {uploaded.name}\n**Size**: {uploaded.size / 1024:.1f} KB\n**Type**: {uploaded.type}")
        st.session_state.uploaded_file_name = uploaded.name
        st.session_state.uploaded_file_type = uploaded.type

    col1, col2 = st.columns(2)
    with col1:
        st.button("🔄 Clear Analysis", on_click=reset_analysis)
    with col2:
        if st.button("🔄 Reload API Keys"):
            # Force reload environment variables
            from dotenv import load_dotenv
            from groundx_utils import create_client, ensure_bucket
            load_dotenv(override=True)
            # Clear cached resources to force reload
            try:
                create_client.clear()
                ensure_bucket.clear()
            except:
                pass
            # Reset API key hash to force cache invalidation
            if 'last_api_key_hash' in st.session_state:
                del st.session_state.last_api_key_hash
            st.success("API keys reloaded! Refreshing...")
            st.rerun()

# Initialize Ground X API client and storage bucket
gx = None
bucket_id = None
groundx_available = False
groundx_error = None

try:
    # Reload environment variables to ensure latest values
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Check API key before attempting to create client
    api_key_check = os.getenv("GROUNDX_API_KEY") or os.environ.get("GROUNDX_API_KEY")
    if api_key_check:
        api_key_check = api_key_check.strip().lstrip('\ufeff')
    
    if not api_key_check or api_key_check == "your-groundx-api-key-here":
        groundx_available = False
        groundx_error = "API key is missing or still using placeholder value. Please update GROUNDX_API_KEY in your .env file with your actual API key."
    else:
        # Use API key hash to invalidate cache when key changes
        import hashlib
        api_key_hash = hashlib.md5(api_key_check.encode()).hexdigest()
        # Clear cache if key changed
        if hasattr(st.session_state, 'last_api_key_hash') and st.session_state.last_api_key_hash != api_key_hash:
            create_client.clear()
        st.session_state.last_api_key_hash = api_key_hash
        
        gx = create_client(_api_key_hash=api_key_hash)
        bucket_id = ensure_bucket(gx)
        groundx_available = True
except ValueError as e:
    groundx_available = False
    groundx_error = str(e)
except Exception as e:
    groundx_available = False
    groundx_error = f"Unexpected error: {str(e)}"

# Auto-load existing document from bucket if available
if gx and bucket_id and not st.session_state.auto_loaded_file and not st.session_state.xray_data:
    # Configurable sample file - can be set via environment variable
    existing_file_name = os.getenv("SAMPLE_FILE_NAME", "tmpivkf8qf8_sample-file.pdf")
    existing_doc_id = check_file_exists(gx, bucket_id, existing_file_name)
    
    if existing_doc_id:
        xray = get_xray_for_existing_document(gx, existing_doc_id, bucket_id)
        st.session_state.xray_data = xray
        st.session_state.uploaded_file_name = existing_file_name
        st.session_state.uploaded_file_type = "application/pdf"
        st.session_state.processing_complete = True
        st.session_state.used_existing_file = True
        st.session_state.auto_loaded_file = True
        st.success(f"✅ **Auto-loaded**: {existing_file_name} from bucket")
        st.rerun()
    else:
        st.session_state.auto_loaded_file = True

# Document Processing Logic
should_process = False
file_to_process = None

if uploaded is not None:
    should_process = True
    file_to_process = uploaded
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded.name}")
    tmp_file.write(uploaded.getbuffer())
    tmp_file.close()
    st.session_state.uploaded_file_path = tmp_file.name
elif st.session_state.uploaded_file_path and not st.session_state.processing_complete:
    should_process = True
    class MockUploadedFile:
        def __init__(self, name, type, path):
            self.name = name
            self.type = type
            self.path = path
        def getbuffer(self):
            with open(self.path, 'rb') as f:
                return f.read()
    
    file_to_process = MockUploadedFile(
        st.session_state.uploaded_file_name,
        st.session_state.uploaded_file_type,
        st.session_state.uploaded_file_path
    )

if should_process and st.session_state.xray_data is None:
    if not groundx_available:
        st.error("❌ Ground X API key is required for document processing.")
        
        # Show detailed diagnostics
        with st.expander("🔍 Troubleshooting - Click to see details", expanded=True):
            api_key_check = os.getenv("GROUNDX_API_KEY") or os.environ.get("GROUNDX_API_KEY")
            if api_key_check:
                api_key_check = api_key_check.strip().lstrip('\ufeff')
            
            st.write("**Current Status:**")
            if not api_key_check:
                st.write("❌ GROUNDX_API_KEY is not set")
            elif api_key_check == "your-groundx-api-key-here":
                st.write("⚠️ GROUNDX_API_KEY is set but still using placeholder value")
                st.write(f"Current value: `{api_key_check}`")
                st.write("")
                st.write("**To fix:**")
                st.write("1. Open the `.env` file in your project directory")
                st.write("2. Replace `your-groundx-api-key-here` with your actual API key")
                st.write("3. Save the file")
                st.write("4. Click the '🔄 Re-process File' button or refresh the page")
            else:
                st.write(f"✅ GROUNDX_API_KEY is set (length: {len(api_key_check)} characters)")
                if groundx_error:
                    st.write(f"**Error:** {groundx_error}")
            
            st.write("")
            st.write("**File location:**")
            env_path = os.path.join(os.getcwd(), ".env")
            st.code(env_path, language=None)
            st.write(f"File exists: {os.path.exists(env_path)}")
        
        st.stop()
    else:
        with st.status("🔄 Processing document...", expanded=True) as status:
            # Determine file path for processing (temporary for new uploads, stored for existing)
            if hasattr(file_to_process, 'path'):
                file_path = file_to_process.path
            else:
                file_path = st.session_state.uploaded_file_path
            
            try:
                xray, used_existing = process_document(gx, bucket_id, file_to_process, file_path)
                st.session_state.xray_data = xray
                st.session_state.processing_complete = True
                st.session_state.used_existing_file = used_existing
                
                if used_existing:
                    st.write("✅ **File already exists in bucket**")
                    st.write("📥 **Fetched X-Ray data...**")
                    st.success("✅ Document analysis completed! (Used existing file)")
                else:
                    st.write("📤 **Uploaded to Ground X...**")
                    st.write("⏳ **Processed document...**")
                    st.write("📥 **Fetched X-Ray data...**")
                    st.success("✅ Document parsed successfully! Explore the results below.")
                
                st.write("🎉 **Analysis complete!**")
            except Exception as e:
                st.error(f"❌ Error processing document: {str(e)}")
                st.session_state.processing_complete = False

# Analysis Results Display
if st.session_state.xray_data:
    xray = st.session_state.xray_data
    
    # Extract and display document metadata metrics
    file_type = xray.get('fileType', 'Unknown')
    language = xray.get('language', 'Unknown')
    pages = len(xray.get("documentPages", []))
    keywords = len(xray.get("fileKeywords", "").split(",")) if xray.get("fileKeywords") else 0
    
    st.markdown(f"**File Type:** {file_type} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Language:** {language} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Pages:** {pages} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **Keywords:** {keywords}")
    
    # Primary interface tabs for analysis and interaction
    main_tabs = st.tabs([
        "📊 X-Ray Analysis",
        "💬 Chat"
    ])
    
    with main_tabs[0]:
        st.markdown("### 📊 X-Ray Analysis Results")
        tabs = st.tabs([
            "🔍 JSON Output",
            "📝 Narrative Summary", 
            "📋 File Summary",
            "💡 Suggested Text",
            "📄 Extracted Text",
            "🏷️ Keywords"
        ])

    with tabs[0]:
        st.subheader("🔍 Raw JSON Data")
        st.json(xray)

    with tabs[1]:
        st.subheader("📝 Narrative Summary")
        # Extract and display narrative content from document chunks
        narratives = []
        if "documentPages" in xray:
            for page in xray["documentPages"]:
                if "chunks" in page:
                    for chunk in page["chunks"]:
                        if "narrative" in chunk and chunk["narrative"]:
                            narratives.extend(chunk["narrative"])
        
        if narratives:
            for i, narrative in enumerate(narratives, 1):
                st.markdown(f"**Narrative {i}:**")
                st.markdown(narrative)
                st.divider()
        else:
            st.info("No narrative text found in the X-Ray data")

    with tabs[2]:
        st.subheader("📋 File Summary")
        file_summary = xray.get("fileSummary")
        if file_summary:
            st.markdown(file_summary)
        else:
            st.info("No file summary found in the X-Ray data")

    with tabs[3]:
        st.subheader("💡 Suggested Text")
        # Extract and display suggested text content from document chunks
        suggested_texts = []
        if "documentPages" in xray:
            for page in xray["documentPages"]:
                if "chunks" in page:
                    for chunk in page["chunks"]:
                        if "suggestedText" in chunk and chunk["suggestedText"]:
                            suggested_texts.append(chunk["suggestedText"])
        
        if suggested_texts:
            for i, suggested in enumerate(suggested_texts, 1):
                st.markdown(f"**Suggested Text {i}:**")
                st.markdown(suggested)
                st.divider()
        else:
            st.info("No suggested text found in the X-Ray data")

    with tabs[4]:
        st.subheader("📄 Extracted Text")
        # Extract and display raw text content from document chunks
        extracted_texts = []
        if "documentPages" in xray:
            for page in xray["documentPages"]:
                if "chunks" in page:
                    for chunk in page["chunks"]:
                        if "text" in chunk and chunk["text"]:
                            extracted_texts.append(chunk["text"])
        
        if extracted_texts:
            combined_text = "\n\n---\n\n".join(extracted_texts)
            st.text_area("Extracted Content", combined_text, height=400)
        else:
            st.info("No extracted text found in the X-Ray data")

    with tabs[5]:
        st.subheader("🏷️ Keywords")
        keywords = xray.get("fileKeywords")
        if keywords:
            st.write(keywords)
        else:
            st.info("No keywords found in the X-Ray data")
    
    # Interactive Chat Interface
    with main_tabs[1]:
        st.markdown("### 💬 Chat with Document")
        st.markdown("Ask questions about your document.")
        
        # Check if OpenRouter API key is available
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            st.error("❌ **OPENROUTER_API_KEY not found** - Chat interface requires OpenRouter API key.")
            st.info("💡 Please add `OPENROUTER_API_KEY` to your `.env` file to enable chat features.")
        else:
            # Initialize and display chat conversation history
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            
            # Render existing chat messages
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Process user input and generate responses
            if prompt := st.chat_input("Ask a question about your document..."):
                # Store user message in conversation history
                st.session_state.chat_history.append({"role": "user", "content": prompt})
                
                # Display user message in chat interface
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Generate and display AI assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        context = prepare_chat_context(xray, prompt)
                        response = generate_chat_response(prompt, context)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.markdown(response)

elif uploaded is None and st.session_state.uploaded_file_name is None and not st.session_state.xray_data:
    # Show API key status messages only when no document is loaded
    if not groundx_available:
        st.warning("⚠️ **GROUNDX_API_KEY not found** - Document processing features are disabled.")
        if groundx_error:
            with st.expander("🔍 Detailed Error Information", expanded=False):
                st.code(groundx_error, language=None)
        st.info("💡 **To enable document processing**: Add `GROUNDX_API_KEY` to your `.env` file.")
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        st.warning("⚠️ **OPENROUTER_API_KEY not found** - Chat interface is disabled.")
        st.info("💡 **To enable chat**: Add `OPENROUTER_API_KEY` to your `.env` file.")
    elif not groundx_available:
        st.info("💡 **Note**: Chat interface is available, but requires processed documents. Upload a document (with GROUNDX_API_KEY) to use chat features.")
    
    st.info("👆 **Upload a document in the sidebar to begin analysis**")
elif uploaded is None and st.session_state.uploaded_file_name and st.session_state.xray_data:
    status = "Auto-loaded" if st.session_state.auto_loaded_file else "Analysis"
    st.success(f"✅ **{status} complete for**: {st.session_state.uploaded_file_name}")
    st.info("💡 **Tip**: You can re-process the file using the button in the sidebar, or upload a new document.")
