from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from models.conversations import Conversation, Message, SendMessageRequest
from services.agent_runner import run_agent
from services.db import DBService
from utils.timezone import now_myt

db = DBService()


# ── Conversation CRUD ─────────────────────────────────────────────────────────

async def create_conversation(conversation: Conversation, current_user):
    conversation = conversation.model_copy(
        update={"user_id": current_user.id, "created_at": now_myt()}
    )
    conversation_id = db.insert_conversation(conversation)
    if not conversation_id:
        return JSONResponse(
            {"status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
             "detail": "Failed to create conversation"}
        )
    return {
        "status": status.HTTP_200_OK,
        "message": "Conversation created successfully",
        "conversation_id": conversation_id,
    }


async def get_conversations(current_user):
    conversations = db.get_conversations_by_user_id(current_user.id)
    return {
        "status": status.HTTP_200_OK,
        "conversations": [c.to_json() for c in conversations],
    }


async def get_conversation(conversation_id: str, current_user):
    conversation = db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this conversation",
        )
    return {"status": status.HTTP_200_OK, "conversation": conversation.to_json()}


async def get_messages(conversation_id: str, current_user):
    conversation = db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access messages in this conversation",
        )
    messages = db.get_messages(conversation_id)
    return {
        "status": status.HTTP_200_OK,
        "messages": [m.to_json() for m in messages],
    }


# ── AI Chat ───────────────────────────────────────────────────────────────────

async def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    current_user,
):
    """
    The single entry point for all user↔agent interaction.

    The user sends a plain natural-language message.  The AI orchestrator
    agent understands the intent, calls whatever MCP tools it needs
    (schedule, travel, recommendations…), and replies in plain language.
    No structured fields are required from the caller.
    """
    # ── 1. Guard: conversation must exist and belong to this user ─────────────
    conversation = db.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to use this conversation",
        )

    # ── 2. Persist the user's message ─────────────────────────────────────────
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.content,
        message_input=payload.message_input,
        language=payload.language,
        created_at=now_myt(),
    )
    user_message_id = db.insert_message(user_message)

    # ── 3. Hand off to the AI agent ───────────────────────────────────────────
    #   The agent reads conversation history from its ADK session, understands
    #   the request, calls MCP tools (add_task_into_schedule, etc.) as needed,
    #   and returns a friendly plain-language reply.
    agent_reply = await run_agent(
        user_id=current_user.id,
        user_name=current_user.name,
        conversation_id=conversation_id,
        message=payload.content,
    )

    # ── 4. Persist the assistant's reply ──────────────────────────────────────
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=agent_reply,
        message_input="agent",
        language=payload.language,
        created_at=now_myt(),
    )
    assistant_message_id = db.insert_message(assistant_message)

    return {
        "status": status.HTTP_200_OK,
        "user_message_id": user_message_id,
        "assistant_message_id": assistant_message_id,
        "assistant_message": assistant_message.to_json(),
    }
