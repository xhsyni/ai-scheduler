import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP
from routers import conversation, task, user
from services.tools import register_mcp_tools
from services.scheduler import weekly_memory_updater_loop
from fastapi.middleware.cors import CORSMiddleware

mcp = FastMCP("AI Scheduler MCP")
register_mcp_tools(mcp)
mcp_app = mcp.http_app(path="/")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start weekly memory updater loop as a background task
    scheduler_task = asyncio.create_task(weekly_memory_updater_loop())
    try:
        async with mcp_app.lifespan(app):
            yield
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)
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

