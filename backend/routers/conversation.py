from typing import Annotated

from fastapi import APIRouter, Depends

from controllers.conversation import (
    create_conversation as controller_create_conversation,
    get_conversation as controller_get_conversation,
    get_conversations as controller_get_conversations,
    get_messages as controller_get_messages,
    send_message as controller_send_message,
)
from controllers.user import get_current_user
from models.conversations import Conversation, SendMessageRequest

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"],
)


@router.post("/create-conversation")
async def create_conversation(
    conversation: Conversation,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await controller_create_conversation(conversation, current_user)


@router.get("/get-conversations")
async def get_conversations(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await controller_get_conversations(current_user)


@router.get("/get-conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await controller_get_conversation(conversation_id, current_user)


@router.get("/{conversation_id}/get-messages")
async def get_messages(
    conversation_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    return await controller_get_messages(conversation_id, current_user)


@router.post("/{conversation_id}/send-message")
async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """
    Send a natural-language message. The AI agent handles everything —
    scheduling, travel, recommendations — from the plain text alone.
    """
    return await controller_send_message(conversation_id, payload, current_user)
