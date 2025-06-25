import os
import langchain_groq
from dotenv import load_dotenv
from langchain_community.utilities.gitlab import GitLabAPIWrapper
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_groq import ChatGroq  # ✅ Correct
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory



load_dotenv()

# GitLab Wrapper
gitlab = GitLabAPIWrapper(
    gitlab_personal_access_token=os.getenv("GITLAB_TOKEN"),
    gitlab_repository="akshithcodez-group/my-agentic-ai",
    gitlab_branch="branch1"
)

toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()

# LLM
llm = ChatGroq(temperature=0.3, model_name="llama3-70b-8192")

# Memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

from langchain_core.prompts import PromptTemplate

template = """
You are a helpful GitLab assistant. Your job is to interpret the user’s request, select the correct tool, and use it properly by following strict JSON schema and interaction protocol.

---

🔧 **Available Tools (Strict Schema Format): use one of the following {tools}**

1. **Create File**
   - Description: Create a new file in the repository.
   - Input JSON:
     ```json
     {{
       "file_path": "string",             
       "content": "string",               
       "branch": "branch1",               
       "commit_message": "string"
     }}
     ```

2. **Update File**
   - Description: Modify an existing file.
   - Input JSON:
     ```json
     {{
       "file_path": "string",
       "content": "string",
       "branch": "branch1",
       "commit_message": "string"
     }}
     ```

3. **Delete File**
   - Description: Delete an existing file.
   - Input JSON:
     ```json
     {{
       "file_path": "string",
       "branch": "branch1",
       "commit_message": "string"
     }}
     ```

4. **Create Issue**
   - Description: Open a new issue.
   - Input JSON:
     ```json
     {{
       "title": "string",
       "description": "string"
     }}
     ```

5. **Get Issue**
   - Description: Retrieve an issue by number.
   - Input JSON:
     ```json
     {{
       "issue_number": integer
     }}
     ```

6. **Get Issues**
   - Description: List all issues.
   - Input JSON:
     ```json
     {{}}
     ```

7. **Create Merge Request**
   - Description: Propose a merge from one branch to another.
   - Input JSON:
     ```json
     {{
       "source_branch": "string",
       "target_branch": "string",
       "title": "string"
     }}
     ```

---

Question: [User’s query]  
Thought: [Analyze user intent, check if file exists if needed]  
Action: [One of {tool_names}]  
Action Input: [Valid JSON input]  
Observation: [What happened after the tool call]  
Thought: Based on this, decide next step  
Final Answer: [What you successfully did or what the user should do]


🚨 **Global Rules (Must Always Obey)**

- 🔑 Use `file_path` exactly as provided — do not modify or guess it
- 🔐 Always set `"branch": "branch1"` for all file-related actions
- 📝 All file actions must include a `"commit_message"`
- 🔁 Do NOT retry or guess actions unless explicitly instructed
- 🧪 Before calling "Create File", use "Get File" or call the tool and check the error
- 🤖 If the file creation fails due to existence, switch to "Update File"
- ✅ Always end with `Final Answer:` explaining what you did
- ❌ Never assume a file exists unless the GitLab tool confirms it
- 💡 If unsure whether a file exists, ask the user or use a check
---

{chat_history}
Question: {input}
{agent_scratchpad}
"""





prompt = PromptTemplate.from_template(template)


# Agent
agent_executor = AgentExecutor.from_agent_and_tools(
    agent=create_react_agent(llm=llm, tools=tools, prompt=prompt),
    tools=tools,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# Streamlit-compatible function
def run_agent(user_input: str):
    return agent_executor.invoke({"input": user_input})
