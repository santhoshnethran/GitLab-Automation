# app.py
import streamlit as st
from agent import run_agent

st.set_page_config(page_title="GitLab AI Agent", layout="wide")
st.title("🤖 GitLab Assistant using Groq + LangChain")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

prompt = st.chat_input("What do you want the GitLab assistant to do?")

if prompt:
    st.session_state.chat_history.append(("user", prompt))
    with st.spinner("Thinking..."):
        result = run_agent(prompt)
    st.session_state.chat_history.append(("agent", result["output"]))

# Show conversation
for role, message in st.session_state.chat_history:
    if role == "user":
        st.chat_message("user").write(message)
    else:
        st.chat_message("assistant").write(message)
