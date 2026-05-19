from fastapi import APIRouter, Depends
from controllers.user import get_current_user
from typing import Annotated
from controllers.task import create_task as controller_create_task, get_tasks as controller_get_tasks
from models.tasks import Task

router = APIRouter(
    prefix="/conversation",
    tags=["Conversation"]
)

@router.post("/create-conversation")
async def create_conversation(task:Task,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_create_task(task,current_user)
    return response

@router.get("/get-conversation")
async def get_conversation(task:Task,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_get_tasks(task,current_user)
    return response