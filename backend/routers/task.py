from fastapi import APIRouter, Depends
from controllers.user import get_current_user
from typing import Annotated
from controllers.task import (
    create_task as controller_create_task, 
    get_tasks as controller_get_tasks, 
    update_task as controller_update_task, 
    add_user_to_task as controller_add_user_to_task,
    update_user_role as controller_update_user_role, delete_user_from_task as controller_delete_user_from_task)
from models.tasks import Task
from pydantic import BaseModel,Field, model_validator
from typing import Optional


class AddUserToTaskModel(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: str = Field(default="viewer")

    @model_validator(mode="after")
    def validate_user_identifier(self):
        if not self.user_id and not self.email:
            raise ValueError("Either user_id or email must be provided")

        if self.user_id and self.email:
            raise ValueError("Only one of user_id or email can be provided")

        return self

router = APIRouter(
    prefix="/task",
    tags=["Tasks"]
)

@router.post("/create-task")
async def create_task(task:Task,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_create_task(task,current_user)
    return response

@router.get("/get-tasks")
async def get_tasks(current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_get_tasks(current_user)
    return response

@router.put("/update-task/{task_id}")
async def update_task(task:Task,task_id:str,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_update_task(task,task_id,current_user)
    return response

@router.post("/add-user-to-task/{task_id}")
async def add_user_to_task(payload:AddUserToTaskModel, task_id:str,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_add_user_to_task(task_id, payload.user_id, payload.email, payload.role, current_user)
    return response

@router.post("/update-user-role/{task_id}/{user_id}")
async def update_user_role(task_id:str,user_id:str,new_role:str,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_update_user_role(task_id,user_id,new_role,current_user)
    return response

@router.delete("/delete-user-from-task/{task_id}/{user_id}")
async def delete_user_from_task(task_id:str,user_id:str,current_user: Annotated[dict, Depends(get_current_user)]):
    response = await controller_delete_user_from_task(task_id,user_id,current_user)
    return response