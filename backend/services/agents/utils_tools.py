from google.adk.agents import LlmAgent
from google.adk.tools.google_search_tool import GoogleSearchTool
from google.adk.tools import url_context
from config.settings import MODEL_NAME

def create_url_context_agent(agent_name:str):
    return LlmAgent(
        name=f'{agent_name}_url_context_agent',
        model=MODEL_NAME,
        description=(
            'Agent specialized in fetching content from URLs.'
        ),
        sub_agents=[],
        instruction='Use the UrlContextTool to retrieve content from provided URLs.',
        tools=[
            url_context
        ],
    )

def create_google_search_agent(agent_name:str):
    return LlmAgent(
        name=f'{agent_name}_google_search_agent',
        model=MODEL_NAME,
        description=(
            'Agent specialized in performing Google searches.'
        ),
        sub_agents=[],
        instruction='Use the GoogleSearchTool to find information on the web.',
        tools=[
            GoogleSearchTool()
        ],
    )
