import os
from dotenv import load_dotenv
from langchain_community.utilities.gitlab import GitLabAPIWrapper
from langchain_community.agent_toolkits.gitlab.toolkit import GitLabToolkit
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent  # ✅ Use LangGraph version
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory

load_dotenv()

gitlab = GitLabAPIWrapper(
    gitlab_personal_access_token=os.getenv("GITLAB_TOKEN"),
    gitlab_repository="akshithcodez-group/my-agentic-ai",
    gitlab_branch="branch1"
)

toolkit = GitLabToolkit.from_gitlab_api_wrapper(gitlab)
tools = toolkit.get_tools()

# initializing LLM
llm = ChatGroq(
    temperature=0.3, 
    model_name="qwen-qwq-32b",
    api_key=os.getenv("GROQ_API_KEY")
)

# creating agent
agent = create_react_agent(
    model=llm,
    tools=tools,
   prompt="""You are a helpful GitLab assistant. Your job is to:

1. **Interpret user requests** and select the appropriate GitLab tool
2. **Execute CRUD operations** (Create, Read, Update, Delete) on files and issues
3. **Always use branch "branch1"** for file operations
4. **Provide clear commit messages** for all file changes

Available operations:
- Create/Update/Delete files in the repository
- Create/Get issues
- Create merge requests

When creating or updating files:
- Always include a descriptive commit message
- Use the exact file path as provided by the user to name the file
- If the file does not exist, create it
- Set branch to "branch1"

Be precise and execute the requested operations step by step."""
)

# Memory for conversation history
memory = ConversationBufferMemory(
    memory_key="chat_history", 
    return_messages=True
)

def run_agent(user_input: str):
    """Execute the agent with proper message formatting"""
    try:
        chat_history = memory.chat_memory.messages
        messages = chat_history + [HumanMessage(content=user_input)]
        result = agent.invoke({"messages": messages})
        final_message = result["messages"][-1]
        response_content = final_message.content
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(response_content)
        return {"output": response_content}
        
    except Exception as e:
        error_msg = f"Agent execution failed: {str(e)}"
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(error_msg)
        return {"output": error_msg}
