"""
ADK Agent Runner — manages per-conversation sessions and streams the
OrchestratorAgent response for a given user message.
"""

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from services.agents.orchestrator import OrchestratorAgent

APP_NAME = "ai_scheduler"

_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            agent=OrchestratorAgent(),
            app_name=APP_NAME,
            session_service=_session_service,
        )
    return _runner


async def run_agent(
    user_id: str,
    user_name: str,
    conversation_id: str,
    message: str,
) -> str:
    """
    Run the orchestrator agent for a single user turn.

    - Reuses the existing ADK session for this conversation_id so the agent
      has full conversation memory across multiple messages.
    - The user_id and user_name are stored in session state so the agent can
      reference them in its instruction template and pass them to MCP tools.

    Returns the agent's final text response, or a fallback string on failure.
    """
    runner = _get_runner()

    # Reuse the session for this conversation so history is maintained.
    session = await _session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=conversation_id,
    )
    if session is None:
        session = await _session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=conversation_id,
            state={"user_id": user_id, "user_name": user_name},
        )

    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    response_text = ""
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=conversation_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text = event.content.parts[0].text or ""
        print(f"[agent_runner] Final response: {response_text}")
    except Exception as exc:
        print(f"[agent_runner] Agent run failed: {exc}")
        return f"Sorry, I ran into an issue processing your request. Please try again. {exc}"

    return response_text or f"I wasn't able to process that. Could you rephrase?"
