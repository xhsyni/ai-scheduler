from fastapi import status
from fastapi.responses import JSONResponse
from models.conversations import Conversation
from services.db import DBService

db = DBService()


# Conversation Function
async def create_conversation(conversation: Conversation):
    db.insert_conversations([conversation])
    return {
        "status": status.HTTP_200_OK,
        "message": "Conversation created successfully"
    }

async def get_conversations(user_id:str):
    conversations = db.get_conversations_by_user_id(user_id)
    return {
        "status": status.HTTP_200_OK,
        "conversations": conversations
    }