import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastmcp import FastMCP
from routers import conversation, task, user
from services.tools import register_mcp_tools
from services.scheduler import weekly_memory_updater_loop, reminder_check_loop
from fastapi.middleware.cors import CORSMiddleware

key_path = os.path.join(os.path.dirname(__file__), "gcp-key.json")
if os.path.exists(key_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

print("VERTEX:", os.getenv("GOOGLE_GENAI_USE_VERTEXAI"))
print("PROJECT:", os.getenv("GOOGLE_CLOUD_PROJECT"))
print("LOCATION:", os.getenv("GOOGLE_CLOUD_LOCATION"))

mcp = FastMCP("AI Scheduler MCP")
register_mcp_tools(mcp)
mcp_app = mcp.http_app(path="/")

#@asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Start weekly memory updater loop as a background task
#     # scheduler_task = asyncio.create_task(weekly_memory_updater_loop())
#     try:
#         async with mcp_app.lifespan(app):
#             yield
#     finally:
#         scheduler_task.cancel()
#         try:
#             await scheduler_task
#         except asyncio.CancelledError:
#             pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # scheduler_task = asyncio.create_task(
    #     weekly_memory_updater_loop()
    # )
    reminder_task = asyncio.create_task(reminder_check_loop())

    try:
        async with mcp_app.lifespan(app):
            yield
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-scheduler-l5y5xyk44-xhsynis-projects.vercel.app",
        "https://cogniplan-scheduler.xhsync.com",
        "http://localhost:8080",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"message": "OK"}

@app.get("/")
def read_root():
    return {"message": "Server is running"}

app.include_router(user.router)
app.include_router(task.router)
app.include_router(conversation.router)
app.mount("/mcp", mcp_app)

