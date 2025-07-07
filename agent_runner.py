# agent_runner.py
import os
import re
import requests
from dotenv import load_dotenv
from typing import Optional, Type
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper

# Load env variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITLAB_PERSONAL_ACCESS_TOKEN = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
GITLAB_REPOSITORY = os.getenv("GITLAB_REPOSITORY")
GITLAB_BRANCH = os.getenv("GITLAB_BRANCH")

# Setup GitLab tools
gitlab = GitLabAPIWrapper(
    gitlab_personal_access_token=GITLAB_PERSONAL_ACCESS_TOKEN,
    gitlab_repository=GITLAB_REPOSITORY,
    gitlab_branch=GITLAB_BRANCH
)
toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()

# ✅ Custom tool: Comment on Issue (bypassing LangChain bug)
class CommentInput(BaseModel):
    instructions: str

def comment_on_gitlab_issue_custom(instructions: str) -> str:
    try:
        # Extract issue number and comment
        issue_number_str, comment = instructions.split("\n\n", 1)
        issue_number = int(issue_number_str.strip())
        comment = comment.strip()
    except Exception as e:
        return f"❌ FORMAT ERROR: Invalid instructions format — {e}"

    if not GITLAB_REPOSITORY or not GITLAB_PERSONAL_ACCESS_TOKEN:
        return "❌ Missing GitLab config."

    base_url = "https://gitlab.com/api/v4"
    project_path = GITLAB_REPOSITORY.replace("/", "%2F")
    endpoint = f"{base_url}/projects/{project_path}/issues/{issue_number}/notes"

    headers = {
        "PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    data = {
        "body": comment
    }

    try:
        response = requests.post(endpoint, headers=headers, json=data)
        if response.status_code == 201:
            return f"✅ Comment added to issue #{issue_number}"
        else:
            return f"❌ GitLab API error {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ EXCEPTION: {e}"

CommentOnIssueTool = Tool.from_function(
    name="Comment on Issue",
    description="""
    Adds a comment to a GitLab issue. Input format:
    
    <issue_number>
    
    <comment body>

    Example:
    12

    Please update the README accordingly.
    """,
    func=comment_on_gitlab_issue_custom,
    args_schema=CommentInput
)

# ✅ Replace buggy tool with custom one
tools = [tool if tool.name != "Comment on Issue" else CommentOnIssueTool for tool in tools]

# TEMP DEBUG TOOL PRINTING
for tool in tools:
    print(f"Tool Name: {tool.name}")
    print(f"Tool Description: {tool.description}")
    print(f"Tool Arguments: {tool.args}\n")

# Setup LLM
llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key=GROQ_API_KEY
)

# Prompt template
prompt_template_str = """
You are an expert GitLab assistant that automates repository operations using the tools provided.

You have access to the following tools:
{tools}
If action = "Comment on Issue", directly invoke that tool without extra reasoning.

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

# Agent setup
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=10, handle_parsing_errors=True)

# 🧠 Main Agent Runner
def run_gitlab_agent(parsed_output: dict):
    action = parsed_output.get("action")

    # ✅ Direct bypass if action is "Comment on Issue"
    if action == "Comment on Issue":
        print("DEBUG: Pre-processing for 'Comment on Issue'.")
        issue_id = parsed_output.get("issue_iid")
        body = parsed_output.get("body")

        if issue_id is not None and body is not None:
            try:
                body = body.encode("utf-8").decode("unicode_escape").strip()
                iid = int(str(issue_id).strip())
                instruction = f"{iid}\n\n{body}"
                print(f"✅ Bypassing agent — directly calling comment tool with:\n{repr(instruction)}")
                return comment_on_gitlab_issue_custom(instruction)
            except Exception as e:
                return f"❌ FORMAT ERROR: Could not format issue comment. Reason: {e}"
        else:
            return "❌ TRANSLATION FAILED: Missing 'issue_iid' or 'body' in JSON."

    # 🔁 Let agent handle everything else
    print(f"DEBUG: Invoking agent with input: {parsed_output}")

    if "instructions" in parsed_output and isinstance(parsed_output["instructions"], str):
        instr = parsed_output["instructions"]
        instr = re.sub(r"\\\\n", "\n", instr)
        instr = re.sub(r"\\n", "\n", instr)
        instr = instr.strip().strip('"').strip("'")
        parsed_output["instructions"] = instr
        print(f"✅ Final cleaned instruction going to agent: {repr(instr)}")

    result = executor.invoke({
        "input": parsed_output,
        "agent_scratchpad": ""
    })

    return result.get("output", "No response.")