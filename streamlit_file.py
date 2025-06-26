import streamlit as st
import os
from dotenv import load_dotenv
st.set_page_config(page_title="Gitlab Automation")
st.markdown("""
    <style>
        html, body, .main, .block-container, .stApp {
            background-color: white !important;
            color: black !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #cccccc !important;
        }
        [class^="st-"], [class*=" st-"] {
            background-color: white !important;
            color: black !important;
        }
        h1, h2, h3, h4, h5, h6, p, div {
            color: black !important;
        }
        .css-1d391kg, .css-1vq4p4l {
            box-shadow: none !important;
            border: none !important;
        }
    </style>
""", unsafe_allow_html=True)
load_dotenv()
groqapi = os.getenv("GROQ_API")
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = ""
with st.sidebar:
    st.title("Enter Your GitLab Private Token")
    PAT = st.text_input("YOUR GITLAB TOKEN", type="password")
    groqapi = PAT
    st.write(f"Current GITLAB TOKEN is {groqapi}")
    st.markdown("---")
    st.title("Prompt History")
    reversed_history = list(reversed(st.session_state.prompt_history))
    if reversed_history:
        for i, prompt in enumerate(reversed_history):
            btn_label = f"{len(reversed_history) - i}. {prompt}"
            if st.button(btn_label, key=f"hist_btn_{i}"):
                st.session_state.selected_prompt = prompt
                st.rerun()
    else:
        st.write("No prompts yet.")
    if st.button("Clear History"):
        st.session_state.prompt_history = []
st.title("GitLab Automation Chat")
input_value = st.session_state.selected_prompt if st.session_state.selected_prompt else ""
textinput = st.text_input("Your Prompt", value=input_value, key="prompt_input")
st.session_state.selected_prompt = ""
if textinput and (not st.session_state.prompt_history or textinput != st.session_state.prompt_history[-1]):
    st.session_state.prompt_history.append(textinput)
    st.rerun()
