import os
from dotenv import load_dotenv
from translation import translate
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.runnables import Runnable
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper

#load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
GITLAB_REPOSITORY = os.getenv("GITLAB_REPOSITORY")
GITLAB_BRANCH = os.getenv("GITLAB_BRANCH")

#translated dict from translation.py
parsed_output = translate()

#setup tools
gitlab = GitLabAPIWrapper(
    gitlab_personal_access_token=GITLAB_PERSONAL_ACCESS_TOKEN,
    gitlab_repository=GITLAB_REPOSITORY,
    gitlab_branch=GITLAB_BRANCH
)
toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()

#setup LLM
llm = ChatGroq(
    temperature = 0.4,
    model_name = "llama-3.1-8b-instant",
    groq_api_key = GROQ_API_KEY
)

#instructions to guide the model
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
- Once an action is performed successfully, do not repeat it. End with a final answer.

Common action corrections:
- "show_file", "see_file", "display_file", "open_file" → "Read File"
- "edit_file", "change_file", "modify_file" → "Update File"
- "remove_file", "del_file" → "Delete File"
- "make_issue", "open_bug", "create_issue", "bug_report" → "Create Pull Request"
- "write_file", "new_file", "add_file" → "Create File"
- "comment", "reply_issue" → "Comment on Issue"

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

#creating an agent
agent = create_react_agent(
    llm=llm, 
    tools=tools,
    prompt=prompt
)

#run the agent
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=2)
result = executor.invoke({
    "input": parsed_output,
    "agent_scratchpad": ""
})

print("Final Agent Result: ", result)

