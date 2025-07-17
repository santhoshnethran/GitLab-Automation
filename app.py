import sys
import os
import streamlit as st
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from translation import PromptTranslation
from agent import GitLabAgent

translator = PromptTranslation()
agent = GitLabAgent()

st.set_page_config(page_title="GitLab Assistant", layout="centered")
st.title("🤖 GitLab Automation Assistant")

#session start initialization
if "response" not in st.session_state:
    st.session_state.response = ""

if "history" not in st.session_state:
    st.session_state.history = []  # {"prompt", "response", "time"}

#input form to enter prompt
with st.form(key="prompt_form", clear_on_submit=True):
    prompt = st.text_input("Enter your GitLab instruction:", placeholder="e.g., Create a file named test.py", key="user_prompt")
    submit_button = st.form_submit_button("Submit")

if submit_button:
    if prompt.strip() == "":
        st.warning("Please enter a prompt.")
    else:
        try:
            #translates to json
            parsed_output = translator.translate(prompt)

            #calls agent to get output
            response = agent.run(parsed_output)

        except Exception as e:
            response = f"❌ Error: {str(e)}"

        #stores result
        st.session_state.response = response
        timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        st.session_state.history.append({
            "prompt": prompt,
            "response": response,
            "time": timestamp
        })
        st.session_state.history = st.session_state.history[-10:]  # Keep last 10

#show current response
if st.session_state.response:
    st.success(st.session_state.response)

#show history with clear button
if st.session_state.history:
    st.markdown("### 🕓 History (Last 10 Prompts)")
    for i, entry in enumerate(reversed(st.session_state.history), 1):
        with st.expander(f"{i}. {entry['prompt']} — *{entry['time']}*"):
            st.markdown(entry["response"])

    st.markdown("---")
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.response = ""
        st.success("History cleared.")
        st.rerun()
else:
    st.session_state.response = ""
