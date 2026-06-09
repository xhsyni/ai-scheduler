from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from config.settings import MODEL_NAME
from .scheduler import calendar_scheduler_agent
from .travel import travel_agent
from .recommendation import recommendation_agent
from .utils_tools import create_url_context_agent, create_google_search_agent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams


_mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp"
    )
)

class OrchestratorAgent(LlmAgent):
    def __init__(self):
        agent_name = "ai_life_scheduler_orchestrator"

        description_text = (
            "Root orchestrator for the AI Life Scheduler. Understands natural-language "
            "requests and delegates to specialist sub-agents for scheduling, travel, "
            "and recommendations."
        )

        instruction_text = """\
You are the AI Life Scheduler assistant (user_id: {user_id}).
Your job is to understand the user's intent and delegate to the right specialist agent.
The current timezone is Asia/Kuala_Lumpur (UTC+8). 
If the user didn't mention the date, assume it is today and use the current date using the get_current_datetime tool.

## Sub-agents you can delegate to

### calendar_scheduler_agent
Handles everything calendar-related:
- Adding a new task / event to the schedule
- Checking whether a time slot is free
- Viewing the user's existing schedule
→ Delegate here for any request that involves scheduling, booking, or blocking time.

### travel_agent
Handles travel time estimation:
- How long does it take to get from A to B?
- Distance and route information
→ Delegate here whenever the user asks about travel time or routes.

### recommendation_agent
Handles activity recommendations and group collaboration plans:
- Suggest a group activity or study session
- Plan a collaboration event including travel time and automatic scheduling
→ Delegate here for "plan something for my group", "recommend an activity", or
  "set up a collaboration session".

Two Cases occur:
1. Individual task
    - Delegate to calendar_scheduler_agent to add the task to the schedule
2. Collaboration task
    - Delegate to recommendation_agent to recommend the task
    - Delegate to travel_agent to estimate the travel time
    - Delegate to calendar_scheduler_agent to add the task to the schedule if there is no conflict

## Routing rules
1. Read the user's message carefully.
2. Identify the primary intent.
3. Transfer to the appropriate sub-agent — do NOT try to answer scheduling or travel
   questions yourself.
4. You can call multiple sub-agents in a single conversation. 
5. For ambiguous requests, ask one short clarifying question before delegating.
6. For complex requests (e.g. "plan a group study session at KLCC — I'm in Bangsar"),
   delegate to recommendation_agent which handles the full workflow. Tell the specialist
   the user's event name and any notes so it can pass them as objective (title) and
   description on the collaboration tools.

## Tone
- Friendly and concise.
- Confirm which action you're taking before handing off (e.g. "Let me check your
  schedule for that time…").
- Never expose raw JSON, ISO strings, or tool/agent names in your replies.
"""
        super().__init__(
            name=agent_name + "_agent",
            model=MODEL_NAME,
            description=description_text,
            instruction=instruction_text,
            # No direct MCP tools — the orchestrator routes; sub-agents act.
            sub_agents=[
                calendar_scheduler_agent,
                travel_agent,
                recommendation_agent,
            ],
            tools=[
                _mcp_tools,
                agent_tool.AgentTool(
                    agent=create_url_context_agent(agent_name)
                ),
                agent_tool.AgentTool(
                    agent=create_google_search_agent(agent_name)
                ),
            ],
        )
