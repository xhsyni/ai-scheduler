from fastapi import FastAPI
from fastmcp import FastMCP
from routers import conversation, task, user
from services.tools import register_mcp_tools
from fastapi.middleware.cors import CORSMiddleware

mcp = FastMCP("AI Scheduler MCP")
register_mcp_tools(mcp)
mcp_app = mcp.http_app(path="/")
app = FastAPI(lifespan=mcp_app.lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"message": "OK"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.include_router(user.router)
app.include_router(task.router)
app.include_router(conversation.router)
app.mount("/mcp", mcp_app)

