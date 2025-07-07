#this is the original translation which uses just simple system prompt with no required fields

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

#load the environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

#intializing groq client
client = Groq(api_key=GROQ_API_KEY)

#this is example user prompt which will be from the UI
user_input = "read test.md"

#this is system prompt to instruct the LLM for required output
system_prompt = """
You are an assistant that converts user instructions about GitLab operations into a pure JSON format. 
Do not add any explanations or extra text. Only return valid JSON.

The JSON should describe GitLab operations like creating issues, branches, merge requests, or updating files.

Return only the JSON. No markdown formatting, no text before or after, no code blocks.

Example format:
{
  "action": "create_issue",
  "title": "Bug: Login fails",
  "description": "Login fails with error code 403 when using correct credentials.",
  "project_id": "123456"
}

For the action "update_file", include these fields in the JSON:
- "file_path": the relative path to the file (e.g., "test.md")
- "branch": (optional) the branch where the update should happen
- "old_content": the exact text that should be replaced
- "new_content": the new text that should replace the old content

Example:
{
  "action": "update_file",
  "file_path": "test.md",
  "branch": "branch1",
  "old_content": "cat",
  "new_content": "dog"
}

if the old_content is not provided, leave it blank or omit it as it will be read by the system later on.

Common action corrections:
- "show_file", "see_file", "display_file", "open_file" → "Read File"
- "edit_file", "change_file", "modify_file" → "Update File"
- "remove_file", "del_file" → "Delete File"
- "make_issue", "open_bug", "create_issue", "bug_report" → "Create Pull Request"
- "write_file", "new_file", "add_file" → "Create File"
- "comment", "reply_issue" → "Comment on Issue"
"""
#function to parse the raw json into proper dict
def json_parse(raw_output):
    try:
        json_str = re.search(r'\{.*\}', raw_output, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        print("Failed to parse JSON: ", e)
        return {}

#function to translate using LLM and parse
def translate():
    try:
        response = client.chat.completions.create(
            model = "llama3-70b-8192",
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        raw_output = response.choices[0].message.content
        parsed_output = json_parse(raw_output)
        return parsed_output
    except Exception as e:
        print("Error during translation: ", e)
        return {}

result = translate()
print(result)

#to check the code    
# if __name__ == "__main__":
#     user_input = "create a new issue in project 123456 titled Login Error with description Login fails on clicking submit"
#     result = translate()
#     print("Final Ouput: ",result)
