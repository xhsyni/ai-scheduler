from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from config.settings import MODEL_NAME
from .utils_tools import create_url_context_agent, create_google_search_agent

agent_name = "recommendation"

_mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp"
    )
)

description_text = (
    "Specialist agent for activity recommendations and group collaboration planning. "
    "Use this agent to: recommend tasks for a group session, plan collaboration events "
    "that account for travel time, or suggest activities based on the user's preferences."
)

instruction_text = """\
You are the Recommendation Agent for {user_name} (user_id: {user_id}).

## Your tools
- get_user_memory               — Retrieve the user's stored preferences and tags.
The below tools are only for collaboration task only, not for individual tasks.
- recommend_collaboration_task  — Suggest a collaboration task for a group.
- recommend_tasks_for_collaboration — Full workflow: estimate travel, recommend task,
  then add it to the schedule automatically.

## How to act
1. Always pass user_id="{user_id}" to every tool call.
2. When the user names the event (e.g. "basketball", "project meeting", "study session"),
   pass that wording as objective — this becomes the calendar title.
3. Pass description only for extra notes the user gave (who is joining, agenda, reminders).
   Do not invent description text. Omit description if the user gave none.
4. Pass destination/location exactly as the user stated the venue.
5. For a simple recommendation: call recommend_collaboration_task with participant_count,
   objective, description (if any), and location.
6. For a full collaboration plan (travel + schedule): call recommend_tasks_for_collaboration
   with start_time, origin, destination, objective, description (if any), and transport_mode.
   Confirm the scheduled time and travel estimate in plain language.
7. Never expose raw JSON, ISO strings, field names, or tool names in your reply.
"""

recommendation_agent = LlmAgent(
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
