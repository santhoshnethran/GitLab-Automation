# agent_runner.py
import os
import re
import requests
import urllib.parse
from dotenv import load_dotenv
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
# ADDED FOR MEMORY: Import the memory module
from langchain.memory import ConversationSummaryBufferMemory
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

# --- Custom Tools ---
# All your custom tool definitions remain unchanged
def delete_branch(branch_name: str) -> str:
    # ... function code
    if branch_name in ['main', 'master', 'develop']: return "❌ Error: For safety, deleting primary branches like 'main', 'master', or 'develop' is not allowed."
    try:
        encoded_branch_name = urllib.parse.quote(branch_name, safe=''); project_path = GITLAB_REPOSITORY.replace("/", "%2F"); url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/branches/{encoded_branch_name}"; headers = {"PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN}; response = requests.delete(url, headers=headers); response.raise_for_status(); return f"✅ Successfully deleted branch '{branch_name}'."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404: return f"❌ Error: Branch '{branch_name}' not found."
        return f"❌ Error deleting branch: {e.response.text}"
    except Exception as e: return f"An unexpected error occurred: {e}"
DeleteBranchTool = Tool.from_function(name="Delete Branch", description="Deletes a branch from the repository. This is a destructive action and cannot be undone.", func=delete_branch)

def list_branches(args: Optional[str] = None) -> str:
    # ... function code
    try:
        project_path = GITLAB_REPOSITORY.replace("/", "%2F"); url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/branches"; headers = {"PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN}; response = requests.get(url, headers=headers); response.raise_for_status(); branches = response.json()
        if not branches: return "No branches found in the repository."
        branch_names = [f"- {branch['name']}" for branch in branches]; return "Repository Branches:\n" + "\n".join(branch_names)
    except Exception as e: return f"An error occurred while listing branches: {e}"
ListBranchesTool = Tool.from_function(name="List Branches", description="Lists all branches in the repository.", func=list_branches)

def create_branch(instructions: str) -> str:
    # ... function code
    try:
        parts = instructions.split(' from ');
        if len(parts) != 2: return "❌ Error: Invalid input format. Expected 'new_branch_name from source_branch_name'."
        new_branch = parts[0].strip(); source_branch = parts[1].strip(); project_path = GITLAB_REPOSITORY.replace("/", "%2F"); url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/branches"; headers = {"PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN}; params = {"branch": new_branch, "ref": source_branch}; response = requests.post(url, headers=headers, params=params); response.raise_for_status(); return f"✅ Successfully created branch '{new_branch}' from '{source_branch}'."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "already exists" in e.response.text: return f"❌ Error: A branch with that name already exists."
        return f"❌ Error creating branch: {e.response.text}"
    except Exception as e: return f"An unexpected error occurred: {e}"
CreateBranchTool = Tool.from_function(name="Create Branch", description="Creates a new branch from an existing source branch. Input must be a single string in the format 'new_branch_name from source_branch_name'.", func=create_branch)

class ListFilesInput(BaseModel):
    path: str = Field(default=".", description="The directory path to list files from. Defaults to the root directory.")
def list_files_in_repo(path: str) -> str:
    # ... function code
    try:
        project_path = GITLAB_REPOSITORY.replace("/", "%2F"); url = f"https://gitlab.com/api/v4/projects/{project_path}/repository/tree?path={path}&ref={GITLAB_BRANCH}"; headers = {"PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN}; response = requests.get(url, headers=headers); response.raise_for_status(); items = response.json()
        if not items: return f"Directory '{path}' is empty or does not exist."
        file_list = [f"- {item['name']} ({item['type']})" for item in items]; return "Files in '" + path + "':\n" + "\n".join(file_list)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404: return f"Error: The path '{path}' was not found in the repository."
        return f"Error: A network error occurred: {e}"
    except Exception as e: return f"An unexpected error occurred: {e}"
ListFilesTool = Tool.from_function(name="List Files", description="Lists files and directories in a repository path. The 'path' argument is optional and defaults to the root directory.", func=list_files_in_repo, args_schema=ListFilesInput)

class CommentInput(BaseModel):
    instructions: str
def comment_on_gitlab_issue_custom(instructions: str) -> str:
    # ... function code
    try:
        issue_number_str, comment = instructions.split("\n\n", 1); issue_number = int(issue_number_str.strip()); comment = comment.strip()
    except Exception as e: return f"❌ FORMAT ERROR: Invalid instructions format — {e}"
    if not GITLAB_REPOSITORY or not GITLAB_PERSONAL_ACCESS_TOKEN: return "❌ Missing GitLab config."
    base_url = "https://gitlab.com/api/v4"; project_path = GITLAB_REPOSITORY.replace("/", "%2F"); endpoint = f"{base_url}/projects/{project_path}/issues/{issue_number}/notes"; headers = {"PRIVATE-TOKEN": GITLAB_PERSONAL_ACCESS_TOKEN, "Content-Type": "application/json"}; data = {"body": comment}
    try:
        response = requests.post(endpoint, headers=headers, json=data); return f"✅ Comment added to issue #{issue_number}" if response.status_code == 201 else f"❌ GitLab API error {response.status_code}: {response.text}"
    except Exception as e: return f"❌ EXCEPTION: {e}"
CommentOnIssueTool = Tool.from_function(name="Comment on Issue", description="Adds a comment to a GitLab issue. Input is the issue number and comment, separated by two newlines.", func=comment_on_gitlab_issue_custom, args_schema=CommentInput)

# --- Combine and Finalize Tool List ---
new_tools = []
for tool in tools:
    if tool.name == "Comment on Issue":
        new_tools.append(CommentOnIssueTool)
    else:
        new_tools.append(tool)
new_tools.append(ListFilesTool)
new_tools.append(ListBranchesTool)
new_tools.append(CreateBranchTool)
new_tools.append(DeleteBranchTool)
tools = new_tools

# --- LLM and Prompt Setup ---
llm = ChatGroq(
    temperature=0,
    model_name="llama3-70b-8192",
    groq_api_key=GROQ_API_KEY
)

# ADDED FOR MEMORY: Chat History is added back to the prompt
prompt_template_str = """
You are an expert GitLab assistant that automates repository operations using the tools provided.

You have access to the following tools:
{tools}
If action = "Comment on Issue", directly invoke that tool without extra reasoning.

Available Tools Explanation:
- Read File: View the contents of a file in the repository.
- Create File: Add a new file to a specific branch.
- Update File: Replace content within an existing file.
- Delete File: Remove a file permanently. This action is for files only.
- Get Issues: List all issues in the project.
- List Files: See the files and directories in a given path.
- Comment on Issue: Add a comment to a specific issue.
- Create Pull Request: Merge changes between branches.
- List Branches: Display all branches in the project.
- Create Branch: Make a new branch from a source branch.
- Delete Branch: Permanently delete a branch. This action cannot be undone.

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

Chat History:
{chat_history}

Input: {input}
{agent_scratchpad}
"""

# ADDED FOR MEMORY: 'chat_history' is added to the input variables
prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad", "tools", "tool_names", "chat_history"],
    template=prompt_template_str
)

agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# ADDED FOR MEMORY: The function now accepts a memory object
def run_gitlab_agent(parsed_output: dict, session_memory: ConversationSummaryBufferMemory):
    action = parsed_output.get("action")
    if action == "Comment on Issue":
        # ... (bypass logic is unchanged)
        print("DEBUG: Pre-processing for 'Comment on Issue'."); issue_id = parsed_output.get("issue_iid"); body = parsed_output.get("body")
        if issue_id is not None and body is not None:
            try:
                body = body.encode("utf-8").decode("unicode_escape").strip(); iid = int(str(issue_id).strip()); instruction = f"{iid}\n\n{body}"; print(f"✅ Bypassing agent — directly calling comment tool with:\n{repr(instruction)}"); return comment_on_gitlab_issue_custom(instruction)
            except Exception as e: return f"❌ FORMAT ERROR: Could not format issue comment. Reason: {e}"
        else: return "❌ TRANSLATION FAILED: Missing 'issue_iid' or 'body' in JSON."
    
    print(f"DEBUG: Invoking agent with input: {parsed_output}")
    if "instructions" in parsed_output and isinstance(parsed_output["instructions"], str):
        instr = parsed_output["instructions"]; instr = re.sub(r"\\\\n", "\n", instr); instr = re.sub(r"\\n", "\n", instr); instr = instr.strip().strip('"').strip("'"); parsed_output["instructions"] = instr; print(f"✅ Final cleaned instruction going to agent: {repr(instr)}")
    
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        # ADDED FOR MEMORY: The memory object is now used by the executor
        memory=session_memory,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )

    result = executor.invoke({
        "input": str(parsed_output)
    })

    return result.get("output", "No response.")