"""
ADK Agent Runner — manages per-conversation sessions and streams the
OrchestratorAgent response for a given user message.
"""

# import os

# os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
# os.environ["GOOGLE_CLOUD_PROJECT"] = "701630160330"
# os.environ["GOOGLE_CLOUD_LOCATION"] = "us-west1"

# print("VERTEX MODE =", os.getenv("GOOGLE_GENAI_USE_VERTEXAI"))
# print("PROJECT =", os.getenv("GOOGLE_CLOUD_PROJECT"))
# print("LOCATION =", os.getenv("GOOGLE_CLOUD_LOCATION"))

# from google.genai import types
# from google.adk.runners import Runner
# from google.adk.sessions import InMemorySessionService

# from services.agents.orchestrator import OrchestratorAgent

# APP_NAME = "ai_scheduler"

# _session_service = InMemorySessionService()
# _runner: Runner | None = None

# PROJECT_ID = "701630160330"
# LOCATION = "us-west1"
# REASONING_ENGINE_ID = 1761831044069195776
# RESOURCE_NAME = (
#     f"projects/701630160330/locations/us-west1/reasoningEngines/1761831044069195776"
# )

import os
import json
import requests

from google.oauth2 import service_account
from google.auth.transport.requests import Request

import google.auth

KEY_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "gcp-key.json"
)

PROJECT_ID = "701630160330"
LOCATION = "us-west1"
REASONING_ENGINE_ID = "3401563520897122304"

RESOURCE_NAME = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}"
    f"/reasoningEngines/{REASONING_ENGINE_ID}"
)

BASE_URL = (
    f"https://{LOCATION}-aiplatform.googleapis.com/v1/"
    f"{RESOURCE_NAME}:streamQuery?alt=sse"
)


def get_access_token():
    if os.path.exists(KEY_PATH):
        credentials = service_account.Credentials.from_service_account_file(
            KEY_PATH,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    else:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
    credentials.refresh(Request())
    return credentials.token

# def _get_runner() -> Runner:
#     global _runner
#     if _runner is None:
#         _runner = Runner(
#             agent=OrchestratorAgent(),
#             app_name=APP_NAME,
#             session_service=_session_service,
#         )
#     return _runner


async def run_agent(
    user_id: str,
    user_name: str,
    conversation_id: str,
    message: str,
) -> str:
    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
    "classMethod": "stream_query",
    "input": {
        "user_id": user_id,
        "message": f"""
{message}

user_id={user_id}
user_name={user_name}
conversation_id={conversation_id}
"""
    }
}

    try:
        res = requests.post(
            BASE_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=90,
        )

        if res.status_code != 200:
            print("[agent_runner] Vertex error:", res.status_code, res.text)
            return "Agent service is temporarily unavailable."

        final_text = ""

        print("[STATUS]", res.status_code)
        print("[HEADERS]", res.headers)

        for line in res.iter_lines(decode_unicode=True):
            if not line:
                continue

            print("[RAW LINE]", line)

            if line.startswith("data: "):
                data = line.replace("data: ", "", 1)
            else:
                data = line

            try:
                event = json.loads(data)
            except Exception as e:
                print("[JSON ERROR]", e)
                continue

            print("[EVENT]", event)

            contents = [
                event.get("content"),
                event.get("output", {}).get("content"),
                event.get("result", {}).get("content"),
            ]

            for content in contents:
                if not content:
                    continue

                parts = content.get("parts", [])

                for part in parts:
                    if "text" in part:
                        final_text += part["text"]

        print("[agent_runner] Final response:", final_text)
        return final_text or "I wasn't able to process that."

    except Exception as exc:
        print("[agent_runner] Agent run failed:", exc)
        return "Agent service is temporarily unavailable."
