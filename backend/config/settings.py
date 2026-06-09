# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()


MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB", "scheduler")
MONGO_ID = os.getenv("MONGO_ID")
MONGO_PASS = os.getenv("MONGO_PASS")
# MODEL_NAME = os.getenv("MODEL_NAME", "gemma-4-31b-it")
# MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.5-flash")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash-lite")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")
AGENT_URL=os.getenv("AGENT_URL")