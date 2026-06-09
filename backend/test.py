import asyncio
import httpx
import google.auth
import google.auth.transport.requests
from config.settings import AGENT_URL

# ─────────────────────────────────────────────────────────────────────────────
# OPTION A: Test the DEPLOYED Reasoning Engine via REST
#
# Cloud Logs confirmed two internal routes:
#   POST /api/reasoning_engine       → handles :query       → 404 (no query method)
#   POST /api/stream_reasoning_engine → handles :streamQuery → correct route
#
# AgentClass.stream_query() accepts: user_id, message, session_id (optional)
# Do NOT send user_name — causes TypeError inside the engine.
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL = AGENT_URL.rsplit(":", 1)[0]  # strip :query suffix

PAYLOAD = {
    "input": {
        "user_id": "6a0bf7fe0d1d187a4fe5cf61",
        "message": "im going to Pavillion shopping at 10am"
    }
}

async def test_deployed_engine():
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token
        print(f"Authenticated as project: {project}")
    except Exception as e:
        print(f"Auth failed: {e}")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Use :streamQuery — the engine only registers stream_query, not query
    url = f"{BASE_URL}:streamQuery"
    print(f"\nPOST {url}")
    print(f"Payload: {PAYLOAD}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=PAYLOAD)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")


asyncio.run(test_deployed_engine())


# ─────────────────────────────────────────────────────────────────────────────
# OPTION B: Test the LOCAL ADK Runner directly (no Reasoning Engine needed)
# Uncomment this and comment out asyncio.run(test_deployed_engine()) above.
# ─────────────────────────────────────────────────────────────────────────────
# import asyncio
# from services.agent_runner import run_agent
#
# async def test_local():
#     reply = await run_agent(
#         user_id="6854f321a0046b021f3f9ad8",
#         user_name="John Doe",
#         conversation_id="691310df2b583b6ab2b97474",
#         message="im going to Pavillion shopping at 10am",
#     )
#     print("Agent reply:", reply)
#
# asyncio.run(test_local())
