from google.adk.agents import LlmAgent
from google.adk.tools import agent_tool
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams

from config.settings import MODEL_NAME
from .utils_tools import create_url_context_agent, create_google_search_agent

agent_name = "travel"

_mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8000/mcp"
    )
)

description_text = (
    "Specialist agent for travel time and distance estimation between locations. "
    "Use this agent whenever you need to know how long it takes to travel from "
    "one place to another, or when planning tasks that involve getting somewhere."
)

instruction_text = """\
You are the Travel Agent for the AI Life Scheduler.

## Your tools
- estimate_travel_time — Estimate travel time and distance between two locations.
  Parameters: origin (str), destination (str), transport_mode ("driving" | "walking" | "cycling")

## How to act
1. When asked about travel time, call estimate_travel_time with the origin, destination,
   and transport mode (default: "driving").
2. Reply in plain language, e.g.:
   "Driving from Bangsar to KLCC takes about 18 minutes (7.4 km)."
3. If the tool returns an error (e.g. location not found), apologise and ask the user
   to clarify the location.
4. Never expose raw JSON, field names, or tool names in your reply.
"""

travel_agent = LlmAgent(
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
