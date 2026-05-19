# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_ID = os.getenv("MONGO_ID")
MONGO_PASS = os.getenv("MONGO_PASS")
