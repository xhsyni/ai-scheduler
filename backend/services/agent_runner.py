"""
ADK Agent Runner — manages per-conversation sessions and streams the
OrchestratorAgent response for a given user message.
"""
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from services.agents.orchestrator import OrchestratorAgent
from google.cloud import aiplatform

APP_NAME = "ai_scheduler"

PROJECT_ID = "701630160330"
LOCATION = "us-west1"
REASONING_ENGINE_ID = "1761831044069195776"
RESOURCE_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{REASONING_ENGINE_ID}"

_session_service = InMemorySessionService()
_runner: Runner | None = None
_remote_agent = None

def _get_runner() -> Runner:
    global _runner
    if _runner is None:
        _runner = Runner(
            agent=OrchestratorAgent(),
            app_name=APP_NAME,
            session_service=_session_service,
        )
    return _runner

def _get_remote_agent():
    """Get a handle to the cloud Reasoning Engine (cached singleton to avoid frequent handshakes)"""
    global _remote_agent
    if _remote_agent is None:
        # initialize AI Platform regional environment
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        # load the already ready cloud agent brain
        _remote_agent = aiplatform.ReasoningEngine(RESOURCE_NAME)
        print(f"[agent_runner] Successfully bound Cloud Agent Engine: {RESOURCE_NAME}")
    return _remote_agent

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
        remote_agent = _get_remote_agent()

        # 2. Core change: replace the previous async loop that ran the local runner
        # to generate streaming responses with directly feeding the context to the
        # cloud Reasoning Engine for inference.
        # Package the user's decrypted identity together with the message so the
        # model's internal prompt and MCP tools can correctly recognize them.
        context_input = f"User Name: {user_name}, User ID: {user_id}. Message: {message}"
        
        response = remote_agent.query(
            input_text=context_input,
            conversation_id=conversation_id
        )
        
        # The structure of the response may vary based on how the cloud agent is set up.
        if hasattr(response, 'text'):
            response_text = response.text
        elif isinstance(response, dict) and "output" in response:
            response_text = response["output"]
        else:
            response_text = str(response)
            
    except Exception as exc:
        print(f"[agent_runner] Remote Cloud Agent run failed: {exc}")
        return "Sorry, I ran into an issue processing your request via Cloud Agent. Please try again."

    return response_text or "I wasn't able to process that via Cloud Agent. Could you rephrase?"

    #     async for event in runner.run_async(
    #         user_id=user_id,
    #         session_id=conversation_id,
    #         new_message=content,
    #     ):
    #         if event.is_final_response() and event.content and event.content.parts:
    #             response_text = event.content.parts[0].text or ""
    # except Exception as exc:
    #     print(f"[agent_runner] Agent run failed: {exc}")
    #     return "Sorry, I ran into an issue processing your request. Please try again."

    # return response_text or "I wasn't able to process that. Could you rephrase?"
