import streamlit as st
from translation1 import translate
from agent_runner import run_gitlab_agent
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Set page
st.set_page_config(page_title="GitLab Chat Agent", page_icon="🤖", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .config-section {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        border-left: 4px solid #4ECDC4;
    }
    .chat-container {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 0.5rem 0;
    }
    .info-box {
        background-color: #e7f3ff;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown('<div class="main-header">🤖 GitLab LLM Agent</div>', unsafe_allow_html=True)
st.markdown("### Transform your natural language instructions into GitLab actions!")

# Configuration Section
with st.container():
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.markdown("### 🔧 Repository Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Project ID input
        project_id = st.text_input(
            "📁 GitLab Project ID",
            placeholder="e.g., 71434157",
            help="Enter your GitLab project ID (found in your project's main page)"
        )
        
        # Repository URL input (optional helper)
        repo_url = st.text_input(
            "🔗 Repository URL (optional)",
            placeholder="e.g., https://gitlab.com/username/repo-name",
            help="Optional: Paste your repo URL to help identify the project"
        )
    
    with col2:
        # Branch input
        branch_name = st.text_input(
            "🌿 Branch Name",
            value="main",
            help="Default branch to work with (usually 'main' or 'master')"
        )
        
        # GitLab Personal Access Token
        access_token = st.text_input(
            "🔐 Personal Access Token",
            type="password",
            help="Your GitLab Personal Access Token (required for API access)"
        )
    
    # Info box with instructions
    st.markdown("""
    <div class="info-box">
        <strong>💡 How to get your Project ID:</strong><br>
        1. Go to your GitLab project page<br>
        2. Look for the project ID below the project name<br>
        3. Or check the URL: gitlab.com/username/repo-name (ID is in project settings)
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Validate configuration
config_valid = False
if project_id and access_token:
    # Update environment variables dynamically
    os.environ["GITLAB_PERSONAL_ACCESS_TOKEN"] = access_token
    os.environ["GITLAB_REPOSITORY"] = project_id
    os.environ["GITLAB_BRANCH"] = branch_name
    
    # Check if GROQ API key exists
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        config_valid = True
        st.markdown("""
        <div class="success-message">
            ✅ Configuration is valid! You can now chat with your GitLab repository.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ GROQ_API_KEY is missing from environment variables. Please check your .env file.")
else:
    st.warning("⚠️ Please fill in the Project ID and Personal Access Token to continue.")

# Chat Section (only show if configuration is valid)
if config_valid:
    st.markdown("---")
    st.markdown("### 💬 Chat with Your Repository")
    
    # Action examples
    with st.expander("📝 Example Commands"):
        st.markdown("""
        **File Operations:**
        - "Show me the contents of README.md"
        - "Create a new file called config.json with basic settings"
        - "Update the package.json file to add a new dependency"
        - "Delete the old-file.txt"
        
        **Issue Management:**
        - "List all open issues"
        - "Create a new issue about login bug"
        - "Add a comment to issue #5"
        
        **Repository Operations:**
        - "Create a pull request from feature branch to main"
        - "Show me all files in the src directory"
        """)
    
    # ♻ Clear Chat Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Chat container
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # 💬 Chat input
        user_input = st.chat_input("Enter your GitLab instruction (e.g., 'Show me README.md' or 'Create new issue about bug')")
        
        if user_input:
            # Save user input
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.spinner("🔄 Translating and executing your request..."):
                parsed = translate(user_input)
                
                if parsed:
                    # Add project_id to parsed output if not present
                    if "project_id" not in parsed:
                        parsed["project_id"] = int(project_id)
                    
                    # Show raw JSON output from translator
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": f"🧾 **Translated Command:**\n```json\n{parsed}\n```"
                    })
                    
                    # Run agent and get final action result
                    agent_response = run_gitlab_agent(parsed)
                else:
                    agent_response = "⚠️ Could not parse instruction into valid JSON."
            
            # Save final agent reply
            st.session_state.messages.append({"role": "assistant", "content": agent_response})
        
        # 🪄 Render full chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚀 Powered by LangChain, Groq, and GitLab API | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)