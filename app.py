import streamlit as st
from translation1 import translate
from agent_runner import run_gitlab_agent
import os
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Set page
st.set_page_config(page_title="GitLab Chat Agent", page_icon="🤖")
st.title("🤖 GitLab LLM Agent")
st.markdown("Ask me anything about GitLab repo operations — I'll convert your instruction to action!")

# Validate .env critical variables
required_vars = {
    "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    "GITLAB_PERSONAL_ACCESS_TOKEN": os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN"),
    "GITLAB_REPOSITORY": os.getenv("GITLAB_REPOSITORY"),
    "GITLAB_BRANCH": os.getenv("GITLAB_BRANCH"),
}

missing = [key for key, value in required_vars.items() if not value]
if missing:
    st.error(f"❌ Missing environment variables: {', '.join(missing)}. Please check your `.env` file.")
    st.stop()

# Clear Chat Button
if st.button("🔄 Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Chat input
user_input = st.chat_input("Enter your GitLab instruction")

if user_input:
    # Save user input
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Translating and executing..."):
        parsed = translate()

        if parsed:
            # Show raw JSON output from translator
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"🧾 Translated JSON:\n```json\n{parsed}\n```"
            })

            # Run agent and get final action result
            agent_response = run_gitlab_agent(parsed)
        else:
            agent_response = "⚠️ Could not parse instruction into valid JSON."

    # Save final agent reply
    st.session_state.messages.append({"role": "assistant", "content": agent_response})

# Render full chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
