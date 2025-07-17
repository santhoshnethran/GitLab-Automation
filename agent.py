import os
from dotenv import load_dotenv
from translation import PromptTranslation
from langchain_groq import ChatGroq
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_community.utilities.gitlab import GitLabAPIWrapper

class GitLabAgent:
    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gitlab_token = os.getenv("GITLAB_PERSONAL_ACCESS_TOKEN")
        self.repo = os.getenv("GITLAB_REPOSITORY")
        self.branch = os.getenv("GITLAB_BRANCH")
        
        gitlab = GitLabAPIWrapper(
            gitlab_personal_access_token=self.gitlab_token,
            gitlab_repository=self.repo,
            gitlab_branch=self.branch
        )
        toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
        tools = toolkit.get_tools()

        llm = ChatGroq(
            temperature = 0.3,
            model_name = "llama3-70b-8192",
            groq_api_key = self.groq_api_key
        )

        prompt_template_str = '''
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
'''

        prompt = PromptTemplate(
            input_variables=["input", "agent_scratchpad"],
            template=prompt_template_str
        )

        agent = create_react_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        self.executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=3,
            handle_parsing_errors=True
        )

    #function to run the agent
    def run(self, parsed_output: dict) -> str:
        result = self.executor.invoke({
            "input": parsed_output,
            "agent_scratchpad": ""
        })
        return result.get("output", "No response.")

# for testing
# if __name__ == "__main__":
#     from translation import PromptTranslation 

#     translator = PromptTranslation()
#     parsed_output = translator.translate("update test2.py to welcome user")

#     agent = GitLabAgent()
#     result = agent.run(parsed_output)
#     print("Final Agent Result:", result)
