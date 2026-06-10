import vertexai
from vertexai import agent_engines

vertexai.init(
    project="automate-life-scheduler",
    location="us-west1",
)

agent_engine = agent_engines.get(
    "projects/701630160330/locations/us-west1/reasoningEngines/3401563520897122304"
)

USER_ID = "6a26ebd93512c2f7136bb51f"

for event in agent_engine.stream_query(
    user_id=USER_ID,
    message=f"""
Create a meeting tomorrow at 3pm for 1 hour.

user_id={USER_ID}
"""
):
    print(event)
