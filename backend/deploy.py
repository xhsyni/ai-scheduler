import vertexai
from vertexai import agent_engines
from vertexai.agent_engines import AdkApp
from agent import root_agent

vertexai.init(
    project="automate-life-scheduler",
    location="us-west1",
    staging_bucket="gs://ai-scheduler-agent-staging-701630160330",
)

app = AdkApp(
    agent=root_agent,
    app_name="scheduler_agent",
)

remote_agent = agent_engines.create(
    app,
    display_name="scheduler-agent",
    requirements=[
        "google-cloud-aiplatform[agent_engines,adk]==1.157.0",
        "google-adk==2.0.0",
        "google-genai==1.75.0",
        "cloudpickle==3.1.2",
        "pydantic==2.13.4",
        "mcp==1.27.1",
        "httpx-sse==0.4.3",
        "sse-starlette==3.4.4",
    ],
)

print(remote_agent.resource_name)