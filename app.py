import streamlit as st
import os
import re
import json
from dotenv import load_dotenv
from translation1 import translate
# Import the llm object from agent_runner to use for summarization
from agent_runner import run_gitlab_agent, llm
# Import the memory module
from langchain.memory import ConversationSummaryBufferMemory

# --- Page Config ---
st.set_page_config(layout="wide", page_title="GitLab Automation Agent", page_icon="🤖")

# --- Load Environment Variables ---
load_dotenv()
GITLAB_REPOSITORY = os.getenv("GITLAB_REPOSITORY")
GITLAB_BRANCH = os.getenv("GITLAB_BRANCH")
required_vars = ["GROQ_API_KEY", "GITLAB_PERSONAL_ACCESS_TOKEN", "GITLAB_REPOSITORY", "GITLAB_BRANCH"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

# --- Sidebar for Configuration and Actions ---
with st.sidebar:
    st.header("Configuration")
    if missing_vars:
        st.error(f"❌ Missing: {', '.join(missing_vars)}")
    else:
        st.success("✅ All configurations loaded.")
        st.info(f"**Repository:** `{GITLAB_REPOSITORY}`")
        st.info(f"**Branch:** `{GITLAB_BRANCH}`")

    st.markdown("---")
    st.header("Actions")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        # Also clear the memory object
        if "memory" in st.session_state:
            st.session_state.memory.clear()
        st.rerun()

    st.markdown("---")
    st.info("This agent uses AI to perform real actions on your GitLab repository.")


# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
# ADDED FOR MEMORY: Initialize the memory object in the session state
if "memory" not in st.session_state:
    st.session_state.memory = ConversationSummaryBufferMemory(
        llm=llm,  # The LLM is needed for summarization
        max_token_limit=1200, # Keeps the buffer from getting too large
        memory_key="chat_history",
        return_messages=True
    )

# --- Main Page UI ---
st.title("🤖 GitLab Automation Agent")
st.markdown("I can help you manage your GitLab repository. I now have memory and can understand follow-up questions.")

# --- Actionable Suggestions ---
st.markdown("**Suggestions:**")
cols = st.columns(4)
suggestions = {
    "List Files": "List all files in the root directory",
    "List Branches": "Show me all the branches",
    "Create Branch": "Create a branch named 'feature/new-idea' from main",
    "List Issues": "Get the open issues"
}
# Create buttons in columns
if cols[0].button(list(suggestions.keys())[0], use_container_width=True):
    st.session_state.messages.append({"role": "user", "content": list(suggestions.values())[0]})
    st.rerun()
if cols[1].button(list(suggestions.keys())[1], use_container_width=True):
    st.session_state.messages.append({"role": "user", "content": list(suggestions.values())[1]})
    st.rerun()
if cols[2].button(list(suggestions.keys())[2], use_container_width=True):
    st.session_state.messages.append({"role": "user", "content": list(suggestions.values())[2]})
    st.rerun()
if cols[3].button(list(suggestions.keys())[3], use_container_width=True):
    st.session_state.messages.append({"role": "user", "content": list(suggestions.values())[3]})
    st.rerun()


# --- Chat History Display ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Chat Input and Agent Logic ---
if prompt := st.chat_input("Enter your GitLab instruction..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            parsed = translate(prompt)

            with st.expander("Show Translated Command"):
                st.json(parsed)

            if parsed:
                # FIXED: Pass the session_memory object to the agent runner
                agent_response = run_gitlab_agent(parsed, st.session_state.memory)
            else:
                agent_response = "⚠️ Could not parse the instruction."

            st.write(agent_response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    st.rerun()