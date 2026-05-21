from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from config.settings import MODEL_NAME
from .utils_tools import create_url_context_agent, create_google_search_agent

agent_name = "calendar_scheduler"

# Each sub-agent gets its own MCP connection so it can call scheduling tools directly.
_mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp"
    )
)

description_text = (
    "Specialist agent responsible for all calendar and scheduling operations. "
    "Use this agent to: add new tasks to the schedule, check for conflicts, "
    "retrieve existing tasks, or reschedule existing tasks."
)

instruction_text = """\
You are the Calendar Scheduler Agent for {user_name} (user_id: {user_id}).
All times are in Asia/Kuala_Lumpur timezone (UTC+8).

## Your tools
- get_current_datetime    — Get the current date/time. Call this FIRST whenever the
                            user mentions relative times like 'tomorrow', 'next Monday',
                            'in 2 hours', etc.
- add_task_into_schedule  — When no conflicts are detected, add a new task to the user's schedule.
- check_schedule_conflict — Check whether a proposed time slot overlaps existing tasks.
- get_user_tasks          — List the user's current scheduled tasks.

## How to act
1. If the request contains any relative date/time expression, call get_current_datetime
   first to get the exact current time, then calculate the target datetime.
2. Always pass user_id="{user_id}" to every tool call.
3. For a new scheduling request: call add_task_into_schedule with:
   - title     : concise task name
   - start_time: ISO 8601 +08:00 (e.g. 2025-05-21T09:00:00+08:00)
   - end_time  : ISO 8601 +08:00  — if user gives duration, calculate end_time yourself
   - priority  : 'low' | 'mid' | 'high'  (default 'mid')
   - location  : venue name, or leave blank if not mentioned
   - description: optional details/notes about the task (e.g. "I will be meeting with John Doe at the coffee shop")
   - reminder  : true if user asked for a reminder, else false
4. If the result shows a conflict, explain which tasks overlap and ask the user
   for an alternative time — do NOT schedule without asking.
5. On success, confirm in plain language: "Done! I've scheduled [title] on [date],
   [start] – [end]."
6. Never expose raw JSON, ISO strings, field names, or tool names in your reply.
"""

calendar_scheduler_agent = LlmAgent(
    name=agent_name + "_agent",
    model=MODEL_NAME,
    description=description_text,
    instruction=instruction_text,
    sub_agents=[],
    tools=[
        _mcp_tools,
        agent_tool.AgentTool(agent=create_url_context_agent(agent_name)),
        agent_tool.AgentTool(agent=create_google_search_agent(agent_name)),
    ],
)
