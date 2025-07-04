import os
import re
from dotenv import load_dotenv

# --- Core LangChain Imports ---
from langchain_community.utilities.gitlab import GitLabAPIWrapper
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_react_agent, AgentExecutor

# --- Imports for the Robust Parser ---
from langchain.agents.agent import AgentOutputParser
from langchain.schema import AgentAction, AgentFinish, OutputParserException

# --- 1. Environment Setup ---
load_dotenv()
# Add your environment variable checks here if you want them.
print("✅ Environment variables loaded successfully.")

# --- 2. Tools and LLM Setup ---
gitlab = GitLabAPIWrapper()
toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()
print(f"🛠️  {len(tools)} tools loaded from GitLabToolkit.")

# Make sure to use a valid, non-deprecated model ID.
llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
print(f"🤖 LLM Initialized: {llm.model_name}")

# In gitlab_agent.py

class RobustReActParser(AgentOutputParser):
    """
    The final, robust parser. It handles markdown and ensures the Action Input
    is captured correctly on a single line.
    """
    def parse(self, text: str) -> AgentAction | AgentFinish:
        if "Final Answer:" in text:
            return AgentFinish(
                return_values={"output": text.split("Final Answer:")[-1].strip()},
                log=text,
            )

        # --- THIS IS THE ONLY LINE THAT CHANGES ---
        # The (.*) at the end is replaced with ([^\n]*) to capture only a single line.
        regex = r"\**\s*Action\s*\**\s*:\s*(.*?)\n+\**\s*Action Input\s*\**\s*:\s*([^\n]*)"
        # --- END OF CHANGE ---

        action_match = re.search(regex, text, re.DOTALL)

        if action_match:
            action = action_match.group(1).strip().strip('*').strip()
            # The cleaning for action_input also needs to be robust.
            action_input = action_match.group(2).strip().strip('*').strip()
            return AgentAction(tool=action, tool_input=action_input, log=text)

        raise OutputParserException(f"Could not parse LLM output: `{text}`")

    @property
    def _type(self) -> str:
        return "robust_react_parser"
# --- 3. Custom Prompt Design ---

prompt = ChatPromptTemplate.from_template(
    """
You are a GitLab DevOps automation engineer. Your persona is professional, efficient, and precise.
You are given a suite of GitLab tools to interact with repositories, issues, and merge requests.

---
### 🎯 Your Goal
Your primary objective is to resolve open GitLab issues by making the necessary code changes and submitting a merge request for review.

---
### 🧠 Your Reasoning Workflow (ReAct Framework)
You must strictly follow this cycle until the goal is achieved:
1.  **Thought:** Analyze the current situation and decide the next logical step.
2.  **Action:** Choose one tool from the available list. The name must be an EXACT match.
3.  **Action Input:** Provide the input the tool needs.
4.  **Observation:** Review the result from the tool to inform your next thought.

---
### 🔒 Protected Branch Workflow
Most projects protect their 'main' branch. You cannot commit directly to it. You MUST follow this specific sequence:

1.  **Get Issue Details:** Use `Get Issue` to understand the task.
2.  **Read Original File:** Use `Read File` to get the file's current content.
3.  **Create File on a NEW BRANCH:** Use the `Create File` tool to commit the corrected file content. **Crucially, the file path MUST start with your new branch name**, like `"new-branch-name/path/to/file.md"`.
4.  **Create Pull Request:** Once the file is successfully created on the new branch, use `Create Pull Request`. Reference the issue number you are fixing in the description (e.g., "Fixes #123").

**Example of `Create File` on a new branch:**
- **Action:** `Create File`
- **Action Input:** `fix-readme-typo/README.md\n<The full, corrected content of the README file goes here>`

---
### 📦 Available Tools
Here are the tools you can use:
{tools}
**Tool Names:** [{tool_names}]

---
### ❗ Important Rules
- NEVER attempt to use `Update File` on the main branch. It will fail.
- ALWAYS use the `Create File` tool with a new branch path (`branch/file.md`) to make your changes.

---
### Let's Begin!
**Question:** {input}
**Thought:**
{agent_scratchpad}
"""
)
print("📝 Custom prompt template configured.")

# --- 4. Agent Creation ---
output_parser = RobustReActParser()

agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt,
    output_parser=output_parser
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)
print("🚀 Agent created and wrapped in executor.")

# --- 5. Agent Invocation ---
input_task = "Check for open issues in the repository and resolve them by updating files and submitting merge requests."
print(f"\n▶️  Invoking agent with task: '{input_task}'")

result = agent_executor.invoke({
    "input": input_task
})

# --- 6. Output ---
print("\n✅ Agent execution finished.")
print(f"🏁 Final Answer: {result['output']}")