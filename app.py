import streamlit as st
from agent import run_agent

st.set_page_config(page_title="GitLab AI Agent", layout="wide")
st.title("🤖 GitLab Assistant using Groq + LangGraph")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("What do you want the GitLab assistant to do?")

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            result = run_agent(user_input)
            response = result["output"]
            st.write(response)
    
    st.session_state.chat_history.append(("assistant", response))

st.subheader("Conversation History")
for role, message in st.session_state.chat_history:
    if role == "user":
        st.chat_message("user").write(f"**You:** {message}")
    else:
        st.chat_message("assistant").write(f"**Assistant:** {message}")
