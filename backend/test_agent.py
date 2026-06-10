import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

KEY_PATH = "gcp-key.json"

RESOURCE_NAME = (
    "projects/701630160330/"
    "locations/us-west1/"
    "reasoningEngines/1761831044069195776"
)

USER_ID = "u_123"

credentials = service_account.Credentials.from_service_account_file(
    KEY_PATH,
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
credentials.refresh(Request())

headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json",
}

base_url = f"https://us-west1-aiplatform.googleapis.com/v1/{RESOURCE_NAME}:streamQuery?alt=sse"


# 1. create session first
create_payload = {
    "classMethod": "create_session",
    "input": {
        "user_id": USER_ID,
        "state": {
            "user_id": USER_ID
        }
    }
}

create_res = requests.post(base_url, headers=headers, json=create_payload, stream=True)

print("CREATE STATUS:", create_res.status_code)

session_id = None

for line in create_res.iter_lines():
    if line:
        text = line.decode("utf-8")
        print(text)

        if '"id"' in text:
            import json
            data = json.loads(text.replace("data: ", ""))
            session_id = data.get("id")

print("SESSION ID:", session_id)


# 2. stream query
query_payload = {
    "classMethod": "stream_query",
    "input": {
        "user_id": USER_ID,
        "session_id": session_id,
        "message": "hello"
    }
}

query_res = requests.post(base_url, headers=headers, json=query_payload, stream=True)

print("QUERY STATUS:", query_res.status_code)

for line in query_res.iter_lines():
    if line:
        print(line.decode("utf-8"))