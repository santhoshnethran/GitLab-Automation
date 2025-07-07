# agent_runner.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper

# Load env variables once
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
GITLAB_REPOSITORY = os.getenv("GITLAB_REPOSITORY")
GITLAB_BRANCH = os.getenv("GITLAB_BRANCH")

# Setup tools once
gitlab = GitLabAPIWrapper(
    gitlab_personal_access_token=GITLAB_PERSONAL_ACCESS_TOKEN,
    gitlab_repository=GITLAB_REPOSITORY,
    gitlab_branch=GITLAB_BRANCH
)
toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()

# Setup LLM
llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key=GROQ_API_KEY
)

# Prompt Template
prompt_template_str = """
You are an expert GitLab assistant that automates repository operations using the tools provided.

You have access to the following tools:
{tools}
Available Tools Explanation:
- Read File: View the contents of a file in the repository.
- Create File: Add a new file to a specific branch.
- Update File: Replace content within an existing file.
- Delete File: Remove a file permanently.
- Get Issues: List all issues in the project.
- Comment on Issue: Add a comment to a specific issue.
- Create Pull Request: Merge changes between branches.

You will receive a JSON dictionary input with keys like "action", "file_path", "branch", "content", etc.

You must:
- Identify the correct tool from: [{tool_names}]
- If the tool executes successfully and provides the needed result, you must conclude with a Final Answer and stop.
- If the "action" is unclear, fuzzy, or has a typo, map it to the right tool using your understanding.
- If any required information is missing, ask a clear follow-up question and stop.
- If the "old_content" is missing or unknown when performing an "Update File" operation, use the "Read File" tool to fetch the current content first.
- Once an action is performed successfully, do not repeat it. End with a final answer.

Use the following format:

Input: the structured dictionary from the user
Thought: your reasoning about what to do
Action: the tool name (must be one of [{tool_names}])
Action Input: what to send to the tool
Observation: what the tool returns
Important: After one successful action or observation, you MUST stop the chain with:
Thought: I now know the final answer
Final Answer: <your actual result>

Begin!

Input: {input}
{agent_scratchpad}
"""

prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad"],
    template=prompt_template_str
)

# Reusable agent + executor
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10, handle_parsing_errors=True)

# Function to run agent
def run_gitlab_agent(parsed_output: dict):
    result = executor.invoke({
        "input": parsed_output,
        "agent_scratchpad": ""
    })
    return result.get("output", "No response.")