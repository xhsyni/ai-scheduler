from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB", "scheduler")
MONGO_ID = os.getenv("MONGO_ID")
MONGO_PASS = os.getenv("MONGO_PASS")

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AGENT_URL = os.getenv("AGENT_URL")

GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "701630160330")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-west1")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")