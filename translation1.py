import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

#this is system prompt to instruct the LLM for required output
system_prompt = """
You are an assistant that converts user instructions about GitLab operations into a pure JSON format. 
Do not add any explanations or extra text. Only return valid JSON.

The JSON should describe GitLab operations like creating issues, branches, merge requests, updating files, commenting on issue.

- You must only return a single, valid JSON object.
- Do not add any extra text, explanations, or markdown.

**YOUR MOST IMPORTANT RULE FOR COMMENTS:**
When a user asks to comment on an issue, you MUST return a JSON object with two keys: "issue_iid" (an integer) and "body" (a string).

Follow this example PRECISELY:
User: "On issue #15, add the comment 'This is fixed.'"
{
  "action": "Comment on Issue",
  "issue_iid": 15,
  "body": "This is fixed."
}

Example format for tasks other than comment on issue:
{
  "action": "create_issue",
  "title": "Bug: Login fails",
  "description": "Login fails with error code 403 when using correct credentials.",
  "project_id": 71420853
}



Common action corrections:
- "show_file", "see_file", "display_file", "open_file" → "Read File"
- "edit_file", "change_file", "modify_file" → "Update File"
- "remove_file", "del_file" → "Delete File"
- "make_issue", "open_bug", "create_issue", "bug_report" → "Create Pull Request"
- "write_file", "new_file", "add_file" → "Create File"
- "comment", "reply_issue" → "Comment on Issue"
- "get_issues", "list_issues" → "Get Issues"
- "merge_request", "pull_request" → "Create Pull Request"
"""



def json_parse(raw_output):
    try:
        json_str = re.search(r'\{.*\}', raw_output, re.DOTALL).group()
        return json.loads(json_str)
    except Exception as e:
        print("Failed to parse JSON: ", e)
        return {}



def translate(user_input: str):
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